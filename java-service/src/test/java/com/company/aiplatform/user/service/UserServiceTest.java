package com.company.aiplatform.user.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.company.aiplatform.user.service.IUserService;
import com.company.aiplatform.user.service.impl.UserServiceImpl;
import com.company.aiplatform.auth.entity.User;
import com.company.aiplatform.auth.dto.AssignRoleReq;
import com.company.aiplatform.user.vo.UserVO;
import com.company.aiplatform.auth.mapper.UserMapper;
import com.company.aiplatform.auth.mapper.UserRoleMapper;
import com.company.aiplatform.common.exception.BusinessException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("UserService 单元测试")
class UserServiceTest {

    @Mock private UserMapper userMapper;
    @Mock private UserRoleMapper userRoleMapper;

    @InjectMocks
    private UserServiceImpl userService;

    private User mockUser;

    @BeforeEach
    void setUp() {
        mockUser = new User();
        mockUser.setId(1L);
        mockUser.setUsername("testuser");
        mockUser.setNickname("Test User");
        mockUser.setEmail("test@example.com");
        mockUser.setStatus(1);
        mockUser.setCreateTime(LocalDateTime.now());
    }

    @Test
    @DisplayName("分页查询用户列表 — 返回用户VO含角色")
    void shouldListUsersWithRoles() {
        Page<User> mpPage = new Page<>(1, 20);
        mpPage.setRecords(List.of(mockUser));
        mpPage.setTotal(1);

        when(userMapper.selectPage(any(Page.class), any())).thenReturn(mpPage);
        when(userMapper.findRoleCodesByUserId(1L)).thenReturn(List.of("employee", "developer"));

        IPage<UserVO> result = userService.listUsers(1, 20, null);

        assertNotNull(result);
        assertEquals(1, result.getTotal());
        assertEquals(2, result.getRecords().get(0).getRoles().size());
    }

    @Test
    @DisplayName("获取用户详情成功")
    void shouldGetUserDetail() {
        when(userMapper.selectById(1L)).thenReturn(mockUser);
        when(userMapper.findRoleCodesByUserId(1L)).thenReturn(List.of("admin"));

        UserVO vo = userService.getUserDetail(1L);

        assertEquals("testuser", vo.getUsername());
        assertTrue(vo.getRoles().contains("admin"));
    }

    @Test
    @DisplayName("获取不存在用户抛出异常")
    void shouldThrowWhenUserNotFound() {
        when(userMapper.selectById(999L)).thenReturn(null);
        assertThrows(BusinessException.class, () -> userService.getUserDetail(999L));
    }

    @Test
    @DisplayName("分配角色 — 先删后插")
    void shouldAssignRoles() {
        AssignRoleReq req = new AssignRoleReq();
        req.setUserId(1L);
        req.setRoleIds(List.of(2L, 3L));

        when(userMapper.selectById(1L)).thenReturn(mockUser);
        when(userRoleMapper.delete(any())).thenReturn(1);
        doReturn(1).when(userRoleMapper).insert((com.company.aiplatform.auth.entity.UserRole) any());

        assertDoesNotThrow(() -> userService.assignRoles(req));
        verify(userRoleMapper, times(2)).insert((com.company.aiplatform.auth.entity.UserRole) any());
    }

    @Test
    @DisplayName("切换用户状态")
    void shouldToggleUserStatus() {
        when(userMapper.selectById(1L)).thenReturn(mockUser);
        when(userMapper.updateById(mockUser)).thenReturn(1);

        userService.toggleUserStatus(1L, 0);

        assertEquals(0, mockUser.getStatus());
        verify(userMapper).updateById(mockUser);
    }
}
