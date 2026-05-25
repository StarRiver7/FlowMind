package com.company.aiplatform.thirdparty.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AIRagSearchRequest {

    private String query;

    @Builder.Default
    @JsonProperty("top_k")
    private Integer topK = 5;

    @JsonProperty("score_threshold")
    private Double scoreThreshold;

    @JsonProperty("doc_ids")
    private List<Long> docIds;

    @JsonProperty("tenant_id")
    private String tenantId;
}
