package com.company.aiplatform.thirdparty.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/** Python AI 服务统一响应包装 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AICommonResponse<T> {

    private int code;

    private String message;

    private T data;

    private Double timestamp;

    @JsonProperty("trace_id")
    private String traceId;

    public boolean isSuccess() {
        return code == 200;
    }
}
