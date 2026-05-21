package com.enterprise.aiagent.domain.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.enterprise.aiagent.domain.model.entity.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;
import java.util.Optional;

@Mapper
public interface UserMapper extends BaseMapper<User> {

    /**
     * 根据用户名查询（含逻辑删除判断 — MyBatis Plus 自动处理）
     */
    @Select("SELECT * FROM t_user WHERE username = #{username} AND is_deleted = 0")
    Optional<User> findByUsername(@Param("username") String username);

    /**
     * 根据邮箱查询
     */
    @Select("SELECT * FROM t_user WHERE email = #{email} AND is_deleted = 0")
    Optional<User> findByEmail(@Param("email") String email);

    /**
     * 查询用户的角色编码列表
     */
    @Select("""
        SELECT r.role_code FROM t_role r
        INNER JOIN t_user_role ur ON r.id = ur.role_id
        WHERE ur.user_id = #{userId} AND r.status = 1
    """)
    List<String> findRoleCodesByUserId(@Param("userId") Long userId);

    /**
     * 查询用户的权限标识列表
     */
    @Select("""
        SELECT DISTINCT p.perm_code FROM t_permission p
        INNER JOIN t_role_permission rp ON p.id = rp.perm_id
        INNER JOIN t_user_role ur ON rp.role_id = ur.role_id
        INNER JOIN t_role r ON ur.role_id = r.id
        WHERE ur.user_id = #{userId} AND r.status = 1 AND p.is_deleted = 0
    """)
    List<String> findPermCodesByUserId(@Param("userId") Long userId);
}
