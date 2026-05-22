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
import static org.mockito.ArgumentMatchers.*;
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
    @DisplayName("注册成功")
    void shouldRegisterSuccessfully() {
        RegisterReq req = new RegisterReq();
        req.setUsername("newuser");
        req.setPassword("password123");
        req.setEmail("new@example.com");

        when(userMapper.findByUsername("newuser")).thenReturn(Optional.empty());
        when(userMapper.findByEmail("new@example.com")).thenReturn(Optional.empty());
        when(passwordEncoder.encode("password123")).thenReturn("$2a$10$encoded");
        when(userMapper.insert(any(User.class))).thenReturn(1);

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
    @DisplayName("登录成功 — 返回双 Token")
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
                .thenReturn("1:abc123def456");

        LoginVO vo = authService.login(req, "127.0.0.1", "JUnit/5.0");

        assertNotNull(vo);
        assertEquals("access-token", vo.getAccessToken());
        assertEquals("1:abc123def456", vo.getRefreshToken());
        assertEquals("Bearer", vo.getTokenType());
        assertEquals(900L, vo.getExpiresIn());
        assertEquals("testuser", vo.getUserInfo().getUsername());

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
    @DisplayName("刷新Token成功 — 不轮换refreshToken，仅延长TTL")
    void shouldRefreshTokenSuccessfully() {
        String refreshToken = "1:existing-token";

        when(refreshTokenService.validateAndExtendTtl(eq(refreshToken), anyString()))
                .thenReturn(true);
        when(refreshTokenService.parseUserId(refreshToken)).thenReturn(1L);
        when(userMapper.selectById(1L)).thenReturn(mockUser);
        when(userMapper.findRoleCodesByUserId(1L)).thenReturn(List.of("employee"));
        when(jwtTokenProvider.generateAccessToken(1L, "testuser", List.of("employee")))
                .thenReturn("new-access");
        when(jwtTokenProvider.getExpiration()).thenReturn(900000L);

        LoginVO vo = authService.refreshToken(refreshToken, "127.0.0.1", "JUnit/5.0");

        assertNotNull(vo);
        assertEquals("new-access", vo.getAccessToken());
        // refreshToken 值不变
        assertEquals(refreshToken, vo.getRefreshToken());
        verify(refreshTokenService).validateAndExtendTtl(eq(refreshToken), anyString());
    }

    @Test
    @DisplayName("刷新Token失败 — Refresh Token 无效")
    void shouldFailWhenRefreshTokenInvalid() {
        String refreshToken = "1:bad-token";

        when(refreshTokenService.validateAndExtendTtl(eq(refreshToken), anyString()))
                .thenReturn(false);
        when(refreshTokenService.parseUserId(refreshToken)).thenReturn(1L);

        assertThrows(BusinessException.class,
                () -> authService.refreshToken(refreshToken, "127.0.0.1", "JUnit"));
    }
}