package com.enterprise.aiagent.domain.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.enterprise.aiagent.domain.model.entity.RolePermission;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface RolePermissionMapper extends BaseMapper<RolePermission> {
}
