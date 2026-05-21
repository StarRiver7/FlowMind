package com.enterprise.aiagent.application;

import com.enterprise.aiagent.application.service.AuthService;
import com.enterprise.aiagent.domain.model.entity.User;
import com.enterprise.aiagent.domain.model.req.LoginReq;
import com.enterprise.aiagent.domain.model.req.RegisterReq;
import com.enterprise.aiagent.domain.model.vo.LoginVO;
import com.enterprise.aiagent.domain.repository.LoginLogMapper;
import com.enterprise.aiagent.domain.repository.UserMapper;
import com.enterprise.aiagent.domain.repository.UserRoleMapper;
import com.enterprise.aiagent.infrastructure.cache.RefreshTokenService;
import com.enterprise.aiagent.infrastructure.cache.TokenBlacklistService;
import com.enterprise.aiagent.infrastructure.common.BusinessException;
import com.enterprise.aiagent.infrastructure.security.JwtTokenProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("AuthService 单元测试")
class AuthServiceTest {

    @Mock private UserMapper userMapper;
    @Mock private UserRoleMapper userRoleMapper;
    @Mock private LoginLogMapper loginLogMapper;
    @Mock private PasswordEncoder passwordEncoder;
    @Mock private JwtTokenProvider jwtTokenProvider;
    @Mock private RefreshTokenService refreshTokenService;
    @Mock private TokenBlacklistService tokenBlacklistService;

    @InjectMocks
    private AuthService authService;

    private User mockUser;

    @BeforeEach
    void setUp() {
        mockUser = new User();
        mockUser.setId(1L);
        mockUser.setUsername("testuser");
        mockUser.setPassword("$2a$10$encoded");
        mockUser.setNickname("Test User");
        mockUser.setEmail("test@example.com");
        mockUser.setStatus(1);
    }

    @Test
    @DisplayName("注册成功 — 用户名和邮箱均未占用")
    void shouldRegisterSuccessfully() {
        RegisterReq req = new RegisterReq();
        req.setUsername("newuser");
        req.setPassword("password123");
        req.setEmail("new@example.com");

        when(userMapper.findByUsername("newuser")).thenReturn(Optional.empty());
        when(userMapper.findByEmail("new@example.com")).thenReturn(Optional.empty());
        when(passwordEncoder.encode("password123")).thenReturn("$2a$10$encoded");
        doReturn(1).when(userMapper).insert(any(User.class));

        assertDoesNotThrow(() -> authService.register(req));
        verify(userMapper).insert((com.enterprise.aiagent.domain.model.entity.User) any());
        verify(userRoleMapper).insert((com.enterprise.aiagent.domain.model.entity.UserRole) any());
    }

    @Test
    @DisplayName("注册失败 — 用户名已存在")
    void shouldFailWhenUsernameExists() {
        RegisterReq req = new RegisterReq();
        req.setUsername("testuser");
        req.setPassword("password123");

        when(userMapper.findByUsername("testuser")).thenReturn(Optional.of(mockUser));

        BusinessException ex = assertThrows(BusinessException.class, () -> authService.register(req));
        assertTrue(ex.getMessage().contains("用户名已存在"));
    }

    @Test
    @DisplayName("登录成功 — 返回 Access Token + Refresh Token + deviceId")
    void shouldLoginSuccessfully() {
        LoginReq req = new LoginReq();
        req.setUsername("testuser");
        req.setPassword("correct");

        when(userMapper.findByUsername("testuser")).thenReturn(Optional.of(mockUser));
        when(passwordEncoder.matches("correct", "$2a$10$encoded")).thenReturn(true);
        when(userMapper.findRoleCodesByUserId(1L)).thenReturn(List.of("employee"));
        when(jwtTokenProvider.generateAccessToken(1L, "testuser", List.of("employee")))
                .thenReturn("access-token");
        when(jwtTokenProvider.getExpiration()).thenReturn(900000L);
        when(refreshTokenService.createRefreshToken(eq(1L), anyString()))
                .thenReturn("redis-refresh-token");

        LoginVO vo = authService.login(req, "127.0.0.1", "JUnit/5.0");

        assertNotNull(vo);
        assertEquals("access-token", vo.getAccessToken());
        assertEquals("redis-refresh-token", vo.getRefreshToken());
        assertNotNull(vo.getDeviceId());
        assertEquals("Bearer", vo.getTokenType());
        assertEquals("testuser", vo.getUserInfo().getUsername());
        assertEquals(900L, vo.getExpiresIn());

        verify(refreshTokenService).createRefreshToken(eq(1L), anyString());
    }

    @Test
    @DisplayName("登录失败 — 密码错误")
    void shouldFailWhenPasswordWrong() {
        LoginReq req = new LoginReq();
        req.setUsername("testuser");
        req.setPassword("wrong");

        when(userMapper.findByUsername("testuser")).thenReturn(Optional.of(mockUser));
        when(passwordEncoder.matches("wrong", "$2a$10$encoded")).thenReturn(false);

        BusinessException ex = assertThrows(BusinessException.class,
                () -> authService.login(req, "127.0.0.1", "JUnit"));
        assertTrue(ex.getMessage().contains("用户名或密码错误"));
    }

    @Test
    @DisplayName("登录失败 — 用户被禁用")
    void shouldFailWhenUserDisabled() {
        mockUser.setStatus(0);
        LoginReq req = new LoginReq();
        req.setUsername("testuser");
        req.setPassword("correct");

        when(userMapper.findByUsername("testuser")).thenReturn(Optional.of(mockUser));

        assertThrows(BusinessException.class,
                () -> authService.login(req, "127.0.0.1", "JUnit"));
    }

    @Test
    @DisplayName("刷新Token成功 — Redis验证通过并轮换")
    void shouldRefreshTokenSuccessfully() {
        when(userMapper.selectById(1L)).thenReturn(mockUser);
        when(refreshTokenService.rotateRefreshToken(1L, "device-1", "old-refresh"))
                .thenReturn("new-refresh");
        when(userMapper.findRoleCodesByUserId(1L)).thenReturn(List.of("employee"));
        when(jwtTokenProvider.generateAccessToken(1L, "testuser", List.of("employee")))
                .thenReturn("new-access");
        when(jwtTokenProvider.getExpiration()).thenReturn(900000L);

        LoginVO vo = authService.refreshToken(1L, "device-1", "old-refresh", "127.0.0.1", "JUnit");

        assertNotNull(vo);
        assertEquals("new-access", vo.getAccessToken());
        assertEquals("new-refresh", vo.getRefreshToken());
        assertEquals("device-1", vo.getDeviceId());
        verify(refreshTokenService).rotateRefreshToken(1L, "device-1", "old-refresh");
    }

    @Test
    @DisplayName("刷新Token失败 — Refresh Token无效")
    void shouldFailWhenRefreshTokenInvalid() {
        when(userMapper.selectById(1L)).thenReturn(mockUser);
        when(refreshTokenService.rotateRefreshToken(1L, "device-1", "bad-token"))
                .thenReturn(null);

        assertThrows(BusinessException.class,
                () -> authService.refreshToken(1L, "device-1", "bad-token", "127.0.0.1", "JUnit"));
    }
}