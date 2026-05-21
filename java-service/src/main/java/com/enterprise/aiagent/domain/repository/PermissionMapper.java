package com.enterprise.aiagent.domain.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.enterprise.aiagent.domain.model.entity.Permission;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface PermissionMapper extends BaseMapper<Permission> {
}
