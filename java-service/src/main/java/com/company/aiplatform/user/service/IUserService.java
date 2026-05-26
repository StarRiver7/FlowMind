package com.company.aiplatform.user.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.company.aiplatform.auth.dto.AssignRoleReq;
import com.company.aiplatform.auth.vo.LoginVO;
import com.company.aiplatform.user.vo.UserVO;

import java.security.Principal;

/**
 * 用户管理服务接口
 */
public interface IUserService {

    /** 分页查询用户列表 */
    IPage<UserVO> listUsers(int page, int pageSize, String keyword);

    /** 获取用户详情 */
    UserVO getUserDetail(Long userId);

    /** 分配角色 */
    void assignRoles(AssignRoleReq req);

    /** 启用/禁用用户 */
    void toggleUserStatus(Long userId, Integer status);

    /** 获取当前登录用户信息 */
    LoginVO.UserInfo getCurrentUser(Principal principal);
}
