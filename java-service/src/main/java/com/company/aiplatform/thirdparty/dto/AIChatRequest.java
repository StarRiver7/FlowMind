package com.company.aiplatform.thirdparty.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

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

    private String model;

    @Builder.Default
    private boolean stream = true;

    @Builder.Default
    @JsonProperty("use_rag")
    private boolean useRag = true;

    @Builder.Default
    @JsonProperty("use_tools")
    private boolean useTools = true;
}
