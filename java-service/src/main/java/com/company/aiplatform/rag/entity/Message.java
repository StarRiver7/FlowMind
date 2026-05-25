package com.company.aiplatform.rag.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("t_message")
public class Message {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long conversationId;
    private String role;
    private String content;
    private String intent;
    private Integer tokensUsed;
    private String sources;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
