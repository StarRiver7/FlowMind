package com.company.aiplatform.thirdparty.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

/** 工具执行请求 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AIToolExecuteRequest {

    @JsonProperty("tool_name")
    private String toolName;

    private Map<String, Object> params;

    @JsonProperty("user_id")
    private Long userId;

    @JsonProperty("conversation_id")
    private Long conversationId;
}
