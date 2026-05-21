package com.enterprise.aiagent.domain.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.enterprise.aiagent.domain.model.entity.LoginLog;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface LoginLogMapper extends BaseMapper<LoginLog> {
}
