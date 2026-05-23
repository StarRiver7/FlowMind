package com.company.aiplatform.thirdparty.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/** RAG 检索结果中的单个文档块 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AIRagChunk {

    @JsonProperty("chunk_id")
    private String chunkId;

    @JsonProperty("file_id")
    private Integer fileId;

    private String content;

    private Double score;

    private Object metadata;
}
