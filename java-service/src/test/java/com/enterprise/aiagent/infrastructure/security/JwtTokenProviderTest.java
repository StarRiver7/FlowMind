package com.enterprise.aiagent.infrastructure.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("JwtTokenProvider 单元测试")
class JwtTokenProviderTest {

    private JwtTokenProvider provider;

    @BeforeEach
    void setUp() {
        // 4参数构造器：secret, expiration, refreshExpiration, issuer
        provider = new JwtTokenProvider(
                "test-secret-key-for-unit-tests-only-must-be-256-bits",
                900000L,
                604800000L,
                "test-issuer"
        );
    }

    @Test
    @DisplayName("生成AccessToken并正确解析userId、username、roles、jti")
    void shouldGenerateAndParseAccessToken() {
        List<String> roles = List.of("admin", "employee");
        String token = provider.generateAccessToken(1L, "testuser", roles);

        assertNotNull(token);
        assertEquals(1L, provider.getUserId(token));
        assertEquals("testuser", provider.getUsername(token));
        assertEquals(2, provider.getRoles(token).size());
        assertTrue(provider.getRoles(token).contains("admin"));

        // jti 不为空，用于黑名单
        String tokenId = provider.getTokenId(token);
        assertNotNull(tokenId);
        assertFalse(tokenId.isBlank());
    }

    @Test
    @DisplayName("校验有效Token返回true")
    void shouldValidateValidToken() {
        String token = provider.generateAccessToken(1L, "user", List.of("employee"));
        assertTrue(provider.validateToken(token));
    }

    @Test
    @DisplayName("校验无效Token返回false")
    void shouldRejectInvalidToken() {
        assertFalse(provider.validateToken("invalid.token.here"));
        assertFalse(provider.validateToken(""));
        assertFalse(provider.validateToken(null));
    }

    @Test
    @DisplayName("过期时间配置正确 — Access Token 15分钟")
    void shouldReturnCorrectExpiration() {
        assertEquals(900000L, provider.getExpiration());
    }

    @Test
    @DisplayName("getExpirationDate返回正确的过期时间")
    void shouldReturnCorrectExpirationDate() {
        String token = provider.generateAccessToken(1L, "user", List.of("employee"));
        assertNotNull(provider.getExpirationDate(token));
        assertTrue(provider.getExpirationDate(token).getTime() > System.currentTimeMillis());
    }
}