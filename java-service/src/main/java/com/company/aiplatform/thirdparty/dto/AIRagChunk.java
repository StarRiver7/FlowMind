package com.company.aiplatform.thirdparty.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class AIRagChunk {

    private Long id;

    @JsonProperty("doc_id")
    private String docId;

    private String content;

    private Double score;

    @JsonProperty("rerank_score")
    private Double rerankScore;

    @JsonProperty("combined_score")
    private Double combinedScore;

    private Map<String, Object> metadata;

    private Map<String, Object> citation;

    private String excerpt;
}
