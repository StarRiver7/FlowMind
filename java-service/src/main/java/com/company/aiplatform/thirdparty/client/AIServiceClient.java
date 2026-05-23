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
import org.springframework.web.client.RestClient;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
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

    private final RestClient aiServiceRestClient;
    private final ObjectMapper objectMapper;

    // ======================== 对话 ========================

    /** 非流式对话 */
    public AIChatResponse chat(Long userId, String query, List<Long> docIds) {
        AICommonResponse<AIChatResponse> resp = aiServiceRestClient.post()
                .uri("/ai/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(new ParameterizedTypeReference<>() {});
        return unwrap(resp);
    }

    /** 流式对话 — 返回 SseEmitter 供 Controller 直接返回给前端 */
    public SseEmitter chatStream(AIChatRequest request) {
        SseEmitter emitter = new SseEmitter(0L);
        request.setStream(true);

        new Thread(() -> {
            try {
                aiServiceRestClient.post()
                        .uri("/ai/chat")
                        .contentType(MediaType.APPLICATION_JSON)
                        .body(request)
                        .exchange((clientReq, clientResp) -> {
                            try (BufferedReader reader = new BufferedReader(
                                    new InputStreamReader(clientResp.getBody(), StandardCharsets.UTF_8))) {
                                String line;
                                while ((line = reader.readLine()) != null) {
                                    if (line.startsWith("data: ")) {
                                        String data = line.substring(6);
                                        if ("[DONE]".equals(data)) {
                                            emitter.complete();
                                            return null;
                                        }
                                        emitter.send(SseEmitter.event().data(data));
                                    }
                                }
                            } catch (Exception e) {
                                emitter.completeWithError(e);
                            }
                            emitter.complete();
                            return null;
                        });
            } catch (Exception e) {
                log.error("AI chat stream failed", e);
                emitter.completeWithError(e);
            }
        }).start();

        return emitter;
    }

    // ======================== 健康检查 ========================

    public boolean health() {
        try {
            AICommonResponse<Map<String, Object>> resp = aiServiceRestClient.get()
                    .uri("/ai/health")
                    .retrieve()
                    .body(new ParameterizedTypeReference<>() {});
            return resp != null && "healthy".equals(resp.getData().get("status"));
        } catch (Exception e) {
            log.warn("AI service health check failed: {}", e.getMessage());
            return false;
        }
    }

    // ======================== RAG ========================

    /** 知识库检索 */
    public List<AIRagChunk> searchRag(AIRagSearchRequest request) {
        AICommonResponse<Map<String, Object>> resp = aiServiceRestClient.post()
                .uri("/ai/rag/search")
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(new ParameterizedTypeReference<>() {});
        Map<String, Object> data = unwrap(resp);
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> chunks = (List<Map<String, Object>>) data.get("chunks");
        if (chunks == null) {
            return List.of();
        }
        return chunks.stream()
                .map(m -> objectMapper.convertValue(m, AIRagChunk.class))
                .toList();
    }

    // ======================== 工具 ========================

    /** 获取工具列表 */
    public List<Map<String, Object>> listTools() {
        AICommonResponse<Map<String, Object>> resp = aiServiceRestClient.get()
                .uri("/ai/tools")
                .retrieve()
                .body(new ParameterizedTypeReference<>() {});
        Map<String, Object> data = unwrap(resp);
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> tools = (List<Map<String, Object>>) data.get("tools");
        return tools != null ? tools : List.of();
    }

    /** 获取工具定义（LLM function calling 格式） */
    public List<Map<String, Object>> getToolDefinitions() {
        AICommonResponse<Map<String, Object>> resp = aiServiceRestClient.get()
                .uri("/ai/tools/definitions")
                .retrieve()
                .body(new ParameterizedTypeReference<>() {});
        Map<String, Object> data = unwrap(resp);
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> tools = (List<Map<String, Object>>) data.get("tools");
        return tools != null ? tools : List.of();
    }

    /** 执行工具 */
    public AIToolExecuteResponse executeTool(AIToolExecuteRequest request) {
        AICommonResponse<AIToolExecuteResponse> resp = aiServiceRestClient.post()
                .uri("/ai/tools/execute")
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(new ParameterizedTypeReference<>() {});
        return unwrap(resp);
    }

    /** 查询工具调用日志 */
    public List<Map<String, Object>> getToolLogs(Long userId, String toolName, int limit) {
        StringBuilder uri = new StringBuilder("/ai/tools/logs?limit=").append(limit);
        if (userId != null) {
            uri.append("&user_id=").append(userId);
        }
        if (toolName != null) {
            uri.append("&tool_name=").append(toolName);
        }

        AICommonResponse<Map<String, Object>> resp = aiServiceRestClient.get()
                .uri(uri.toString())
                .retrieve()
                .body(new ParameterizedTypeReference<>() {});
        Map<String, Object> data = unwrap(resp);
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> logs = (List<Map<String, Object>>) data.get("logs");
        return logs != null ? logs : List.of();
    }

    // ======================== 工作流 ========================

    /** 工作流列表 */
    public List<Map<String, Object>> listWorkflows() {
        AICommonResponse<Map<String, Object>> resp = aiServiceRestClient.get()
                .uri("/ai/workflow")
                .retrieve()
                .body(new ParameterizedTypeReference<>() {});
        Map<String, Object> data = unwrap(resp);
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> workflows = (List<Map<String, Object>>) data.get("workflows");
        return workflows != null ? workflows : List.of();
    }

    /** 执行工作流 */
    public Map<String, Object> executeWorkflow(AIWorkflowExecuteRequest request) {
        AICommonResponse<Map<String, Object>> resp = aiServiceRestClient.post()
                .uri("/ai/workflow/execute")
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(new ParameterizedTypeReference<>() {});
        return unwrap(resp);
    }

    /** 工作流执行历史 */
    public List<Map<String, Object>> getWorkflowExecutions(Long workflowId) {
        String uri = workflowId != null
                ? "/ai/workflow/executions?workflow_id=" + workflowId
                : "/ai/workflow/executions";
        AICommonResponse<Map<String, Object>> resp = aiServiceRestClient.get()
                .uri(uri)
                .retrieve()
                .body(new ParameterizedTypeReference<>() {});
        Map<String, Object> data = unwrap(resp);
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> executions = (List<Map<String, Object>>) data.get("executions");
        return executions != null ? executions : List.of();
    }

    // ======================== 内部工具方法 ========================

    /** 解包 Python 统一响应，失败时抛异常 */
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
