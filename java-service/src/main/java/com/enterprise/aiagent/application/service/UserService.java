package com.enterprise.aiagent.application.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.enterprise.aiagent.domain.enums.ResultCode;
import com.enterprise.aiagent.domain.model.entity.User;
import com.enterprise.aiagent.domain.model.entity.UserRole;
import com.enterprise.aiagent.domain.model.req.AssignRoleReq;
import com.enterprise.aiagent.domain.model.vo.UserVO;
import com.enterprise.aiagent.domain.repository.UserMapper;
import com.enterprise.aiagent.domain.repository.UserRoleMapper;
import com.enterprise.aiagent.infrastructure.common.BusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserService {

    private final UserMapper userMapper;
    private final UserRoleMapper userRoleMapper;

    public IPage<UserVO> listUsers(int page, int pageSize, String keyword) {
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        if (keyword != null && !keyword.isBlank()) {
            wrapper.like(User::getUsername, keyword)
                    .or()
                    .like(User::getNickname, keyword)
                    .or()
                    .like(User::getEmail, keyword);
        }
        wrapper.orderByDesc(User::getCreateTime);

        Page<User> mpPage = new Page<>(page, pageSize);
        IPage<User> userPage = userMapper.selectPage(mpPage, wrapper);

        return userPage.convert(user -> {
            List<String> roles = userMapper.findRoleCodesByUserId(user.getId());
            return UserVO.builder()
                    .id(user.getId())
                    .username(user.getUsername())
                    .nickname(user.getNickname())
                    .email(user.getEmail())
                    .phone(user.getPhone())
                    .avatarUrl(user.getAvatarUrl())
                    .status(user.getStatus())
                    .lastLoginTime(user.getLastLoginTime())
                    .roles(roles)
                    .createTime(user.getCreateTime())
                    .build();
        });
    }

    public UserVO getUserDetail(Long userId) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException(ResultCode.NOT_FOUND, "用户不存在");
        }
        List<String> roles = userMapper.findRoleCodesByUserId(userId);
        return UserVO.builder()
                .id(user.getId())
                .username(user.getUsername())
                .nickname(user.getNickname())
                .email(user.getEmail())
                .phone(user.getPhone())
                .avatarUrl(user.getAvatarUrl())
                .status(user.getStatus())
                .lastLoginTime(user.getLastLoginTime())
                .roles(roles)
                .createTime(user.getCreateTime())
                .build();
    }

    @Transactional
    public void assignRoles(AssignRoleReq req) {
        User user = userMapper.selectById(req.getUserId());
        if (user == null) {
            throw new BusinessException(ResultCode.NOT_FOUND, "用户不存在");
        }

        LambdaQueryWrapper<UserRole> deleteWrapper = new LambdaQueryWrapper<>();
        deleteWrapper.eq(UserRole::getUserId, req.getUserId());
        userRoleMapper.delete(deleteWrapper);

        for (Long roleId : req.getRoleIds()) {
            UserRole ur = new UserRole();
            ur.setUserId(req.getUserId());
            ur.setRoleId(roleId);
            userRoleMapper.insert((UserRole) ur);
        }

        log.info("Roles assigned for user {}: {}", req.getUserId(), req.getRoleIds());
    }

    public void toggleUserStatus(Long userId, Integer status) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException(ResultCode.NOT_FOUND, "用户不存在");
        }
        user.setStatus(status);
        userMapper.updateById(user);
        log.info("User status changed: userId={}, status={}", userId, status);
    }
}
