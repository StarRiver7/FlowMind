package com.company.aiplatform.thirdparty.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/** 工具执行响应 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AIToolExecuteResponse {

    private boolean success;

    private String result;

    private String error;

    @JsonProperty("execution_time_ms")
    private Integer executionTimeMs;
}
