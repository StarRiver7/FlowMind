package com.company.aiplatform.thirdparty.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

/** 工作流执行请求 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AIWorkflowExecuteRequest {

    @JsonProperty("workflow_id")
    private Long workflowId;

    @JsonProperty("input_data")
    private Map<String, Object> inputData;

    @JsonProperty("user_id")
    private Long userId;
}
