package com.company.aiplatform.rag.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.company.aiplatform.rag.entity.Document;
import com.company.aiplatform.rag.mapper.DocumentMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;


public interface DocumentService {


    Path getUploadDir() throws IOException;

    Page<Document> listDocuments(Long userId, Integer pageNum, Integer pageSize) ;

    Document uploadDocument(Long userId, String title, MultipartFile file) throws IOException;

    void processDocumentAsync(Long documentId, String filePath, String fileName);

    Map<String, Object> chat(Long userId, String query, List<Long> docIds);

    void deleteDocument(Long documentId, Long userId) ;
}
