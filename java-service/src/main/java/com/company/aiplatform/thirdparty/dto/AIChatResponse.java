package com.company.aiplatform.thirdparty.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/** AI 对话响应（非流式） */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AIChatResponse {

    private String content;

    @JsonProperty("conversation_id")
    private String conversationId;

    private String intent;

    private List<SourceDoc> sources;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SourceDoc {
        @JsonProperty("chunk_id")
        private String chunkId;
        @JsonProperty("file_id")
        private Integer fileId;
        private String content;
        private Double score;
        private Object metadata;
    }
}
