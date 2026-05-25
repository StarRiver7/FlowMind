package com.company.aiplatform.rag.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.company.aiplatform.rag.entity.ChatHistory;
import com.company.aiplatform.rag.entity.Document;
import com.company.aiplatform.rag.entity.DocumentPermission;
import com.company.aiplatform.rag.mapper.DocumentMapper;
import com.company.aiplatform.rag.mapper.DocumentPermissionMapper;
import com.company.aiplatform.rag.service.DocumentService;
import com.company.aiplatform.thirdparty.client.AIServiceClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class DocumentServiceImpl extends ServiceImpl<DocumentMapper, Document> implements DocumentService {

    private final DocumentPermissionMapper documentPermissionMapper;
    private final AIServiceClient aiBackendClient;

    @Value("${file.upload.path:./uploads}")
    private String uploadPath;

    @Override
    public Path getUploadDir() throws IOException {
        Path uploadDir = Paths.get(uploadPath).toAbsolutePath().normalize();
        if (!Files.exists(uploadDir)) {
            Files.createDirectories(uploadDir);
            log.info("Created upload directory: {}", uploadDir);
        }
        return uploadDir;
    }

    @Override
    public Page<Document> listDocuments(Long userId, Integer pageNum, Integer pageSize) {
        List<Long> accessibleDocIds = baseMapper.selectAccessibleDocumentIds(userId);
        Page<Document> page = new Page<>(pageNum, pageSize);
        if (accessibleDocIds.isEmpty()) {
            return page;
        }
        return this.page(page, new LambdaQueryWrapper<Document>()
                .in(Document::getId, accessibleDocIds)
                .orderByDesc(Document::getCreateTime));
    }

    @Override
    public Document uploadDocument(Long userId, String title, MultipartFile file) throws IOException {
        if (file.isEmpty()) {
            throw new RuntimeException("File cannot be empty");
        }

        String originalFilename = file.getOriginalFilename();
        if (originalFilename == null || originalFilename.trim().isEmpty()) {
            throw new RuntimeException("File name cannot be empty");
        }

        String fileExt = originalFilename.substring(originalFilename.lastIndexOf(".")).toLowerCase();
        List<String> allowedExts = List.of(".txt", ".pdf", ".doc", ".docx", ".md", ".csv", ".xlsx");
        if (!allowedExts.contains(fileExt)) {
            throw new RuntimeException("Unsupported file type: " + fileExt + ". Supported: " + String.join(", ", allowedExts));
        }

        long maxSize = 100 * 1024 * 1024;
        if (file.getSize() > maxSize) {
            throw new RuntimeException("File size must not exceed 100MB");
        }

        String newFileName = UUID.randomUUID() + fileExt;
        Path uploadDir = getUploadDir();
        Path destPath = uploadDir.resolve(newFileName);
        File destFile = destPath.toFile();
        file.transferTo(destFile);
        String absolutePath = destPath.toString();

        Document document = new Document();
        document.setTitle(title);
        document.setFileName(originalFilename);
        document.setFilePath(absolutePath);
        document.setFileSize(file.getSize());
        document.setFileType(fileExt);
        document.setUserId(userId);
        document.setStatus(0);
        document.setCreateTime(LocalDateTime.now());
        document.setTenantId("default");
        this.save(document);

        DocumentPermission permission = new DocumentPermission();
        permission.setDocumentId(document.getId());
        permission.setPrincipalType("user");
        permission.setPrincipalId(String.valueOf(userId));
        permission.setPermission("write");
        permission.setCreateTime(LocalDateTime.now());
        documentPermissionMapper.insert(permission);

        this.processDocumentAsync(document.getId(), absolutePath, originalFilename);

        return document;
    }

    @Override
    @Async("ragTaskExecutor")
    public void processDocumentAsync(Long documentId, String filePath, String fileName) {
        try {
            File file = new File(filePath);
            if (!file.exists()) {
                log.error("File not found: {}", filePath);
                Document document = this.getById(documentId);
                if (document != null) {
                    document.setStatus(-1);
                    this.updateById(document);
                }
                return;
            }

            Map<String, Object> result = aiBackendClient.indexDocumentAsync(
                    documentId, filePath, null, "default"
            ).block();

            if (result != null) {
                Document document = this.getById(documentId);
                if (document != null) {
                    document.setStatus(1);
                    Integer chunkCount = (Integer) result.get("chunk_count");
                    document.setChunksProcessed(chunkCount);
                    this.updateById(document);
                }
                log.info("Document {} indexed: {} chunks", documentId, result.get("chunk_count"));
            }
        } catch (Exception e) {
            log.error("Failed to process document {}", documentId, e);
            Document document = this.getById(documentId);
            if (document != null) {
                document.setStatus(-1);
                this.updateById(document);
            }
        }
    }

    @Override
    public Map<String, Object> chat(Long userId, String query, List<Long> docIds) {
        com.company.aiplatform.thirdparty.dto.AIChatResponse response =
                aiBackendClient.chat(userId, null, query, true, true);

        Map<String, Object> result = new HashMap<>();
        result.put("answer", response.getContent());
        result.put("sources", response.getSources());
        result.put("intent", response.getIntent());
        result.put("conversation_id", response.getConversationId());
        return result;
    }

    @Override
    public void deleteDocument(Long documentId, Long userId) {
        Document document = this.getById(documentId);
        if (document == null) {
            throw new RuntimeException("Document not found");
        }
        if (!document.getUserId().equals(userId)) {
            throw new RuntimeException("No permission to delete this document");
        }

        this.removeById(documentId);

        try {
            aiBackendClient.deleteDocumentAsync(String.valueOf(documentId)).subscribe();
        } catch (Exception e) {
            log.error("Failed to delete AI backend index for document {}", documentId, e);
        }

        File file = new File(document.getFilePath());
        if (file.exists() && !file.delete()) {
            log.warn("Failed to delete local file: {}", document.getFilePath());
        }
    }
}
