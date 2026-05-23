package com.company.aiplatform.auth.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.company.aiplatform.auth.entity.UserRole;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface UserRoleMapper extends BaseMapper<UserRole> {

}
