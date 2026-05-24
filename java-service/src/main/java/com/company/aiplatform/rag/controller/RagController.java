package com.company.aiplatform.rag.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.company.aiplatform.annotation.CurrentUserId;
import com.company.aiplatform.annotation.RequireRole;
import com.company.aiplatform.common.enums.ResultCode;
import com.company.aiplatform.common.result.Result;
import com.company.aiplatform.rag.entity.Document;
import com.company.aiplatform.rag.service.DocumentService;
import com.company.aiplatform.user.entity.ChatRequest;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@Tag(name = "文档管理", description = "文档管理相关接口")
@RestController
@RequestMapping("/api/v1/documents")
@RequiredArgsConstructor
public class RagController {

    private final DocumentService documentService;

    @Operation(summary = "分页查询用户的文档列表")
    //  分页查询用户的文档列表
    @GetMapping
    public Result<Page<Document>> listDocuments(
            @CurrentUserId Long userId,
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize) {
        Page<Document> page = documentService.listDocuments(userId, pageNum, pageSize);
        return Result.success(page);
    }

    @Operation(summary = "上传文档（仅管理员）")
    /**
     * 上传文档（仅管理员）
     */
    @PostMapping("/upload")
    public Result<Document> uploadDocument(
            @CurrentUserId Long userId,
            @RequestParam("title") String title,
            @RequestParam("file") MultipartFile file) {
        try {
            Document document = documentService.uploadDocument(userId, title, file);
            return Result.success(document);
        } catch (Exception e) {
            return Result.fail(ResultCode.UPLOAD_FAILED, "上传失败: " + e.getMessage());
        }
    }

    @Operation(summary = "删除文档")
    //  删除文档
    @DeleteMapping("/{id}")
    public Result<Void> deleteDocument(
            @CurrentUserId Long userId,
            @PathVariable Long id) {
        documentService.deleteDocument(id, userId);
        return Result.success();

    }

    @Operation(summary = "ai聊天")
    //  ai聊天
    @PostMapping("/chat")
    public Result<Map<String, Object>> chat(
            @CurrentUserId Long userId,
            @RequestBody ChatRequest chatRequest) {
        Map<String, Object> result = documentService.chat(
                userId,
                chatRequest.getQuery(),
                chatRequest.getDocumentIds()
        );
        return Result.success(result);
    }

}
