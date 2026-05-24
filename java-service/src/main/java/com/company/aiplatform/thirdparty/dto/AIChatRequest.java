package com.company.aiplatform.thirdparty.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/** AI 对话请求 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AIChatRequest {

    @NotBlank
    @JsonProperty("conversation_id")
    private String conversationId;

    @NotBlank
    @JsonProperty("user_id")
    private String userId;

    @NotBlank
    private String message;

    /**
     * 返回Top K
     */
    private Integer topK;

    /**
     * 文档ID列表
     */
    private List<Long> documentIds;

    /**
     * 模型名称
     */
    private String model;

    /**
     * 是否流式返回
     */

    @Builder.Default
    private boolean stream = true;

    /**
     * 是否使用RAG
     */
    @Builder.Default
    @JsonProperty("use_rag")
    private boolean useRag = true;

    /**
     * 是否使用工具
     */
    @Builder.Default
    @JsonProperty("use_tools")
    private boolean useTools = true;
}
