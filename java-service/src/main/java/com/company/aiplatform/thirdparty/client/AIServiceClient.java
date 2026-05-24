package com.company.aiplatform.thirdparty.client;

import com.company.aiplatform.thirdparty.dto.*;
import com.company.aiplatform.common.exception.BusinessException;
import com.company.aiplatform.common.enums.ResultCode;
import com.company.aiplatform.user.vo.ProcessDocumentResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.io.File;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * AI 服务 HTTP 客户端 — 对接 Python ai-service-python 的全部接口
 *
 * <pre>
 * Python 端点一览:
 *   POST /ai/chat            AI 对话（支持 SSE 流式）
 *   GET  /ai/health          健康检查
 *   POST /ai/rag/search      知识库检索
 *   POST /ai/rag/index       文档索引
 *   GET  /ai/tools           工具列表
 *   POST /ai/tools/execute   执行工具
 *   GET  /ai/tools/logs      工具调用日志
 *   GET  /ai/workflow        工作流列表
 *   POST /ai/workflow        创建工作流
 *   POST /ai/workflow/execute 执行工作流
 * </pre>
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AIServiceClient {

    private final WebClient aiServiceWebClient;
    private final ObjectMapper objectMapper;

    // ======================== 对话 ========================

    /**
     * 非流式对话（异步）
     *
     * @param userId 用户ID
     * @param query 用户问题
     * @param topK 检索文档数量
     * @param documentIds 指定文档ID列表
     * @return AI对话响应
     */
    public Mono<AIChatResponse> chatAsync(Long userId, String query, Integer topK, java.util.List<Long> documentIds) {
        AIChatRequest request = AIChatRequest.builder()
                .userId(userId != null ? userId.toString() : "anonymous")
                .message(query)
                .topK(topK)
                .documentIds(documentIds)
                .stream(false)
                .build();

        return aiServiceWebClient.post()
                .uri("/ai/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<AIChatResponse>>() {})
                .map(this::unwrap)
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("对话请求失败: 状态码 {}, 响应体 {}",
                            e.getStatusCode(), e.getResponseBodyAsString());
                })
                .onErrorResume(e -> {
                    log.error("对话请求失败", e);
                    throw new RuntimeException("调用AI后端聊天接口失败: " + e.getMessage(), e);
                });
    }

    /**
     * 非流式对话（同步，兼容现有代码）
     *
     * @param userId 用户ID
     * @param query 用户问题
     * @param topK 检索文档数量
     * @param documentIds 指定文档ID列表
     * @return AI对话响应
     */
    public AIChatResponse chat(Long userId, String query, Integer topK, java.util.List<Long> documentIds) {
        return chatAsync(userId, query, topK, documentIds).block();
    }

    /**
     * 流式对话 — 返回 SseEmitter 供 Controller 直接返回给前端
     *
     * @param request 对话请求
     * @return SSE 发射器，用于实时推送对话结果
     */
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
                .doOnComplete(() -> emitter.complete())
                .doOnError(emitter::completeWithError)
                .subscribe();

        return emitter;
    }

    // ======================== 健康检查 ========================

    /**
     * 健康检查（异步）
     *
     * @return AI服务健康状态，true表示健康
     */
    public Mono<Boolean> healthAsync() {
        return aiServiceWebClient.get()
                .uri("/ai/health")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<Map<String, Object>>>() {})
                .map(resp -> resp != null && "healthy".equals(resp.getData().get("status")))
                .onErrorReturn(false)
                .doOnError(e -> log.warn("AI 服务健康检查失败: {}", e.getMessage()));
    }

    // ======================== RAG ========================

    /**
     * 异步处理文档
     *
     * @param documentId 文档ID
     * @param file       文件
     * @param metadata   元数据
     * @return ProcessDocumentResponse
     */
    public Mono<ProcessDocumentResponse> processDocumentAsync(Long documentId, File file, Map<String, Object> metadata) {
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", new FileSystemResource(file));

        StringBuilder uriBuilder = new StringBuilder("/api/v1/documents/process?document_id=" + documentId);
        if (metadata != null && !metadata.isEmpty()) {
            // 简单处理元数据，如果需要复杂元数据，可扩展为JSON
        }

        return aiServiceWebClient.post()
                .uri(uriBuilder.toString())
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .bodyValue(body)
                .retrieve()
                .bodyToMono(ProcessDocumentResponse.class)
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("文档处理请求失败: 状态码 {}, 响应体 {}",
                            e.getStatusCode(), e.getResponseBodyAsString());
                })
                .onErrorResume(e -> {
                    log.error("文档处理请求失败", e);
                    throw new RuntimeException("调用AI后端文档处理接口失败: " + e.getMessage(), e);
                });
    }

    /**
     * 同步处理文档（兼容现有代码）
     *
     * @param documentId 文档ID
     * @param file       文件
     * @param metadata   元数据
     * @return Map<String, Object>
     */
    public Map<String, Object> processDocument(Long documentId, File file, Map<String, Object> metadata) {
        log.info("发送文档处理请求。等待响应");
        return processDocumentAsync(documentId, file, metadata)
                .map(response -> {
                    Map<String, Object> result = new HashMap<>();
                    result.put("document_id", response.getDocumentId());
                    result.put("chunks_processed", response.getChunksProcessed());
                    result.put("status", response.getStatus());
                    return result;
                })
                .block();
    }

    /**
     * 异步删除文档
     *
     * @param documentId 文档ID
     * @return Mono<Void>
     */
    public Mono<Void> deleteDocumentAsync(Long documentId) {
        return aiServiceWebClient.delete()
                .uri("/api/v1/documents/{documentId}", documentId)
                .retrieve()
                .bodyToMono(Void.class)
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("文档删除请求失败: 状态码 {}, 响应体 {}",
                            e.getStatusCode(), e.getResponseBodyAsString());
                })
                .onErrorResume(e -> {
                    log.error("文档删除请求失败", e);
                    throw new RuntimeException("调用AI后端删除接口失败: " + e.getMessage(), e);
                });
    }

    /**
     * 知识库检索（异步）
     *
     * @param request 检索请求
     * @return 检索到的文档块列表
     */
    public Mono<List<AIRagChunk>> searchRagAsync(AIRagSearchRequest request) {
        return aiServiceWebClient.post()
                .uri("/ai/rag/search")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<Map<String, Object>>>() {})
                .map(resp -> {
                    Map<String, Object> data = unwrap(resp);
                    @SuppressWarnings("unchecked")
                    List<Map<String, Object>> chunks = (List<Map<String, Object>>) data.get("chunks");
                    if (chunks == null) {
                        return List.<AIRagChunk>of();
                    }
                    return chunks.stream()
                            .map(m -> objectMapper.convertValue(m, AIRagChunk.class))
                            .toList();
                })
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("知识库检索请求失败: 状态码 {}, 响应体 {}",
                            e.getStatusCode(), e.getResponseBodyAsString());
                })
                .onErrorResume(e -> {
                    log.error("知识库检索请求失败", e);
                    throw new RuntimeException("调用AI后端知识库检索接口失败: " + e.getMessage(), e);
                });
    }

    /**
     * 知识库检索（同步，兼容现有代码）
     *
     * @param request 检索请求
     * @return 检索到的文档块列表
     */
    public List<AIRagChunk> searchRag(AIRagSearchRequest request) {
        return searchRagAsync(request).block();
    }

    // ======================== 工具 ========================

    /**
     * 获取工具列表（异步）
     *
     * @return 工具列表
     */
    public Mono<List<Map<String, Object>>> listToolsAsync() {
        return aiServiceWebClient.get()
                .uri("/ai/tools")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<Map<String, Object>>>() {})
                .map(resp -> {
                    Map<String, Object> data = unwrap(resp);
                    @SuppressWarnings("unchecked")
                    List<Map<String, Object>> tools = (List<Map<String, Object>>) data.get("tools");
                    return tools != null ? tools : List.<Map<String, Object>>of();
                })
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("获取工具列表请求失败: 状态码 {}, 响应体 {}",
                            e.getStatusCode(), e.getResponseBodyAsString());
                })
                .onErrorResume(e -> {
                    log.error("获取工具列表请求失败", e);
                    throw new RuntimeException("调用AI后端工具列表接口失败: " + e.getMessage(), e);
                });
    }

    /**
     * 获取工具列表（同步，兼容现有代码）
     *
     * @return 工具列表
     */
    public List<Map<String, Object>> listTools() {
        return listToolsAsync().block();
    }

    /**
     * 获取工具定义（LLM function calling 格式）（异步）
     *
     * @return 工具定义列表
     */
    public Mono<List<Map<String, Object>>> getToolDefinitionsAsync() {
        return aiServiceWebClient.get()
                .uri("/ai/tools/definitions")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<Map<String, Object>>>() {})
                .map(resp -> {
                    Map<String, Object> data = unwrap(resp);
                    @SuppressWarnings("unchecked")
                    List<Map<String, Object>> tools = (List<Map<String, Object>>) data.get("tools");
                    return tools != null ? tools : List.<Map<String, Object>>of();
                })
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("获取工具定义请求失败: 状态码 {}, 响应体 {}",
                            e.getStatusCode(), e.getResponseBodyAsString());
                })
                .onErrorResume(e -> {
                    log.error("获取工具定义请求失败", e);
                    throw new RuntimeException("调用AI后端工具定义接口失败: " + e.getMessage(), e);
                });
    }

    /**
     * 获取工具定义（LLM function calling 格式）（同步，兼容现有代码）
     *
     * @return 工具定义列表
     */
    public List<Map<String, Object>> getToolDefinitions() {
        return getToolDefinitionsAsync().block();
    }

    /**
     * 执行工具（异步）
     *
     * @param request 工具执行请求
     * @return 工具执行结果
     */
    public Mono<AIToolExecuteResponse> executeToolAsync(AIToolExecuteRequest request) {
        return aiServiceWebClient.post()
                .uri("/ai/tools/execute")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<AIToolExecuteResponse>>() {})
                .map(this::unwrap)
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("执行工具请求失败: 状态码 {}, 响应体 {}",
                            e.getStatusCode(), e.getResponseBodyAsString());
                })
                .onErrorResume(e -> {
                    log.error("执行工具请求失败", e);
                    throw new RuntimeException("调用AI后端执行工具接口失败: " + e.getMessage(), e);
                });
    }

    /**
     * 执行工具（同步，兼容现有代码）
     *
     * @param request 工具执行请求
     * @return 工具执行结果
     */
    public AIToolExecuteResponse executeTool(AIToolExecuteRequest request) {
        return executeToolAsync(request).block();
    }

    /**
     * 查询工具调用日志（异步）
     *
     * @param userId 用户ID
     * @param toolName 工具名称
     * @param limit 日志数量限制
     * @return 工具调用日志列表
     */
    public Mono<List<Map<String, Object>>> getToolLogsAsync(Long userId, String toolName, int limit) {
        StringBuilder uri = new StringBuilder("/ai/tools/logs?limit=").append(limit);
        if (userId != null) {
            uri.append("&user_id=").append(userId);
        }
        if (toolName != null) {
            uri.append("&tool_name=").append(toolName);
        }

        return aiServiceWebClient.get()
                .uri(uri.toString())
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<Map<String, Object>>>() {})
                .map(resp -> {
                    Map<String, Object> data = unwrap(resp);
                    @SuppressWarnings("unchecked")
                    List<Map<String, Object>> logs = (List<Map<String, Object>>) data.get("logs");
                    return logs != null ? logs : List.<Map<String, Object>>of();
                })
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("获取工具日志请求失败: 状态码 {}, 响应体 {}",
                            e.getStatusCode(), e.getResponseBodyAsString());
                })
                .onErrorResume(e -> {
                    log.error("获取工具日志请求失败", e);
                    throw new RuntimeException("调用AI后端工具日志接口失败: " + e.getMessage(), e);
                });
    }

    /**
     * 查询工具调用日志（同步，兼容现有代码）
     *
     * @param userId 用户ID
     * @param toolName 工具名称
     * @param limit 日志数量限制
     * @return 工具调用日志列表
     */
    public List<Map<String, Object>> getToolLogs(Long userId, String toolName, int limit) {
        return getToolLogsAsync(userId, toolName, limit).block();
    }

    // ======================== 工作流 ========================

    /**
     * 工作流列表（异步）
     *
     * @return 工作流列表
     */
    public Mono<List<Map<String, Object>>> listWorkflowsAsync() {
        return aiServiceWebClient.get()
                .uri("/ai/workflow")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<Map<String, Object>>>() {})
                .map(resp -> {
                    Map<String, Object> data = unwrap(resp);
                    @SuppressWarnings("unchecked")
                    List<Map<String, Object>> workflows = (List<Map<String, Object>>) data.get("workflows");
                    return workflows != null ? workflows : List.<Map<String, Object>>of();
                })
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("获取工作流列表请求失败: 状态码 {}, 响应体 {}",
                            e.getStatusCode(), e.getResponseBodyAsString());
                })
                .onErrorResume(e -> {
                    log.error("获取工作流列表请求失败", e);
                    throw new RuntimeException("调用AI后端工作流列表接口失败: " + e.getMessage(), e);
                });
    }

    /**
     * 工作流列表（同步，兼容现有代码）
     *
     * @return 工作流列表
     */
    public List<Map<String, Object>> listWorkflows() {
        return listWorkflowsAsync().block();
    }

    /**
     * 执行工作流（异步）
     *
     * @param request 工作流执行请求
     * @return 工作流执行结果
     */
    public Mono<Map<String, Object>> executeWorkflowAsync(AIWorkflowExecuteRequest request) {
        return aiServiceWebClient.post()
                .uri("/ai/workflow/execute")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<Map<String, Object>>>() {})
                .map(this::unwrap)
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("执行工作流请求失败: 状态码 {}, 响应体 {}",
                            e.getStatusCode(), e.getResponseBodyAsString());
                })
                .onErrorResume(e -> {
                    log.error("执行工作流请求失败", e);
                    throw new RuntimeException("调用AI后端执行工作流接口失败: " + e.getMessage(), e);
                });
    }

    /**
     * 执行工作流（同步，兼容现有代码）
     *
     * @param request 工作流执行请求
     * @return 工作流执行结果
     */
    public Map<String, Object> executeWorkflow(AIWorkflowExecuteRequest request) {
        return executeWorkflowAsync(request).block();
    }

    /**
     * 工作流执行历史（异步）
     *
     * @param workflowId 工作流ID
     * @return 工作流执行历史列表
     */
    public Mono<List<Map<String, Object>>> getWorkflowExecutionsAsync(Long workflowId) {
        String uri = workflowId != null
                ? "/ai/workflow/executions?workflow_id=" + workflowId
                : "/ai/workflow/executions";
        
        return aiServiceWebClient.get()
                .uri(uri)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<AICommonResponse<Map<String, Object>>>() {})
                .map(resp -> {
                    Map<String, Object> data = unwrap(resp);
                    @SuppressWarnings("unchecked")
                    List<Map<String, Object>> executions = (List<Map<String, Object>>) data.get("executions");
                    return executions != null ? executions : List.<Map<String, Object>>of();
                })
                .doOnError(WebClientResponseException.class, e -> {
                    log.error("获取工作流历史请求失败: 状态码 {}, 响应体 {}",
                            e.getStatusCode(), e.getResponseBodyAsString());
                })
                .onErrorResume(e -> {
                    log.error("获取工作流历史请求失败", e);
                    throw new RuntimeException("调用AI后端工作流历史接口失败: " + e.getMessage(), e);
                });
    }

    /**
     * 工作流执行历史（同步，兼容现有代码）
     *
     * @param workflowId 工作流ID
     * @return 工作流执行历史列表
     */
    public List<Map<String, Object>> getWorkflowExecutions(Long workflowId) {
        return getWorkflowExecutionsAsync(workflowId).block();
    }

    // ======================== 内部工具方法 ========================

    /**
     * 解包 Python 统一响应，失败时抛异常
     *
     * @param resp Python 服务响应
     * @param <T> 响应数据类型
     * @return 响应数据
     * @throws BusinessException 当响应为空或失败时抛出
     */
    private <T> T unwrap(AICommonResponse<T> resp) {
        if (resp == null) {
            throw new BusinessException(ResultCode.AI_SERVICE_UNAVAILABLE, "AI 服务无响应");
        }
        if (!resp.isSuccess()) {
            throw new BusinessException(resp.getCode(), resp.getMessage());
        }
        return resp.getData();
    }
}
