package com.company.aiplatform.rag.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.company.aiplatform.rag.entity.Document;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface DocumentMapper extends BaseMapper<Document> {

    List<Long> selectAccessibleDocumentIds(@Param("userId") Long userId);
}
