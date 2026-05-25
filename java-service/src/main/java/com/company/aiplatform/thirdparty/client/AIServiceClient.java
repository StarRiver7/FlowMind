package com.company.aiplatform.thirdparty.client;

import com.company.aiplatform.thirdparty.dto.*;
import com.company.aiplatform.common.exception.BusinessException;
import com.company.aiplatform.common.enums.ResultCode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class AIServiceClient {

    private final WebClient aiServiceWebClient;
    private final ObjectMapper objectMapper;

    // ======================== Chat ========================

    public Mono<AIChatResponse> chatAsync(Long userId, String conversationId, String query, boolean useRag, boolean useTools) {
        AIChatRequest request = AIChatRequest.builder()
                .userId(userId != null ? userId.toString() : "anonymous")
                .conversationId(conversationId)
                .message(query)
                .stream(false)
                .useRag(useRag)
                .useTools(useTools)
                .build();

        return aiServiceWebClient.post()
                .uri("/ai/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<AIChatResponse>>() {})
                .map(this::unwrap)
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("Chat request failed: status {}, body {}", e.getStatusCode(), e.getResponseBodyAsString());
                })
                .onErrorResume(e -> {
                    log.error("Chat request failed", e);
                    throw new BusinessException(ResultCode.AI_SERVICE_UNAVAILABLE, "AI chat failed: " + e.getMessage());
                });
    }

    public AIChatResponse chat(Long userId, String conversationId, String query, boolean useRag, boolean useTools) {
        return chatAsync(userId, conversationId, query, useRag, useTools).block();
    }

    public SseEmitter chatStream(AIChatRequest request) {
        SseEmitter emitter = new SseEmitter(0L);
        request.setStream(true);

        aiServiceWebClient.post()
                .uri("/ai/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToFlux(String.class)
                .doOnNext(line -> {
                    try {
                        if (line.startsWith("data: ")) {
                            String data = line.substring(6);
                            if ("[DONE]".equals(data)) {
                                emitter.complete();
                            } else {
                                emitter.send(SseEmitter.event().data(data));
                            }
                        }
                    } catch (Exception e) {
                        emitter.completeWithError(e);
                    }
                })
                .doOnComplete(emitter::complete)
                .doOnError(emitter::completeWithError)
                .subscribe();

        return emitter;
    }

    // ======================== Health ========================

    public Mono<Boolean> healthAsync() {
        return aiServiceWebClient.get()
                .uri("/ai/health")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<Map<String, Object>>>() {})
                .map(resp -> resp != null && "healthy".equals(resp.getData().get("status")))
                .onErrorReturn(false)
                .doOnError(e -> log.warn("AI health check failed: {}", e.getMessage()));
    }

    // ======================== RAG ========================

    public Mono<Map<String, Object>> indexDocumentAsync(Long docId, String filePath, Map<String, Object> metadata, String tenantId) {
        Map<String, Object> body = Map.of(
                "file_path", filePath,
                "file_id", docId,
                "metadata", metadata != null ? metadata : Map.of(),
                "tenant_id", tenantId != null ? tenantId : "default"
        );

        return aiServiceWebClient.post()
                .uri("/ai/rag/index")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(body)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<Map<String, Object>>>() {})
                .map(this::unwrap)
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("Document indexing failed: status {}", e.getStatusCode());
                })
                .onErrorResume(e -> {
                    log.error("Document indexing failed", e);
                    throw new BusinessException(ResultCode.AI_SERVICE_UNAVAILABLE, "RAG index failed: " + e.getMessage());
                });
    }

    public Mono<Void> deleteDocumentAsync(String documentId) {
        return aiServiceWebClient.delete()
                .uri("/ai/rag/document/{docId}", documentId)
                .retrieve()
                .bodyToMono(Void.class)
                .doOnError(e -> log.error("Document deletion failed: documentId={}", documentId, e));
    }

    @SuppressWarnings("unchecked")
    public Mono<List<AIRagChunk>> searchRagAsync(AIRagSearchRequest request) {
        return aiServiceWebClient.post()
                .uri("/ai/rag/search")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<Map<String, Object>>>() {})
                .map(resp -> {
                    Map<String, Object> data = unwrap(resp);
                    List<Map<String, Object>> chunks = (List<Map<String, Object>>) data.get("chunks");
                    if (chunks == null) return List.<AIRagChunk>of();
                    return chunks.stream()
                            .map(m -> objectMapper.convertValue(m, AIRagChunk.class))
                            .toList();
                })
                .doOnError(e -> log.error("RAG search failed", e))
                .onErrorReturn(List.of());
    }

    public List<AIRagChunk> searchRag(AIRagSearchRequest request) {
        return searchRagAsync(request).block();
    }

    // ======================== Tools ========================

    @SuppressWarnings("unchecked")
    public Mono<List<Map<String, Object>>> listToolsAsync() {
        return aiServiceWebClient.get()
                .uri("/ai/tools")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .<List<Map<String, Object>>>map(m -> {
                    List<Map<String, Object>> tools = (List<Map<String, Object>>) m.get("tools");
                    return tools != null ? tools : List.of();
                })
                .onErrorReturn(List.of());
    }

    public List<Map<String, Object>> listTools() {
        return listToolsAsync().block();
    }

    public Mono<AIToolExecuteResponse> executeToolAsync(AIToolExecuteRequest request) {
        return aiServiceWebClient.post()
                .uri("/ai/tools/execute")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(AIToolExecuteResponse.class)
                .doOnError(e -> log.error("Tool execution failed", e))
                .onErrorResume(e -> {
                    throw new BusinessException(ResultCode.AI_SERVICE_UNAVAILABLE, "Tool execution failed: " + e.getMessage());
                });
    }

    public AIToolExecuteResponse executeTool(AIToolExecuteRequest request) {
        return executeToolAsync(request).block();
    }

    // ======================== Workflow ========================

    @SuppressWarnings("unchecked")
    public Mono<List<Map<String, Object>>> listWorkflowsAsync() {
        return aiServiceWebClient.get()
                .uri("/ai/workflow")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .<List<Map<String, Object>>>map(m -> {
                    List<Map<String, Object>> workflows = (List<Map<String, Object>>) m.get("workflows");
                    return workflows != null ? workflows : List.of();
                })
                .onErrorReturn(List.of());
    }

    public List<Map<String, Object>> listWorkflows() {
        return listWorkflowsAsync().block();
    }

    public Mono<Map<String, Object>> executeWorkflowAsync(AIWorkflowExecuteRequest request) {
        return aiServiceWebClient.post()
                .uri("/ai/workflow/execute")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<Map<String, Object>>>() {})
                .map(this::unwrap)
                .doOnError(e -> log.error("Workflow execution failed", e))
                .onErrorResume(e -> {
                    throw new BusinessException(ResultCode.AI_SERVICE_UNAVAILABLE, "Workflow execution failed: " + e.getMessage());
                });
    }

    public Map<String, Object> executeWorkflow(AIWorkflowExecuteRequest request) {
        return executeWorkflowAsync(request).block();
    }

    // ======================== Internal ========================

    private <T> T unwrap(AICommonResponse<T> resp) {
        if (resp == null) {
            throw new BusinessException(ResultCode.AI_SERVICE_UNAVAILABLE, "AI service no response");
        }
        if (!resp.isSuccess()) {
            throw new BusinessException(resp.getCode(), resp.getMessage());
        }
        return resp.getData();
    }
}
