package com.company.aiplatform.rag.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("t_document_permission")
public class DocumentPermission {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long documentId;
    private String principalType;
    private String principalId;
    private String permission;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    private Long creatorId;
}
