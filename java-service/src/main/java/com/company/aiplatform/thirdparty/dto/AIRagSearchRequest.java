package com.company.aiplatform.thirdparty.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/** RAG 检索请求 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AIRagSearchRequest {

    private String query;

    @Builder.Default
    @JsonProperty("top_k")
    private Integer topK = 5;

    @Builder.Default
    @JsonProperty("score_threshold")
    private Double scoreThreshold = 0.5;
}
