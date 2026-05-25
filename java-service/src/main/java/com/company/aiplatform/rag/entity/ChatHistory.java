package com.company.aiplatform.rag.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("t_chat_history")
public class ChatHistory {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;
    private Long conversationId;
    private String role;
    private String content;
    private String intent;
    private String sources;
    private Integer tokensUsed;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
