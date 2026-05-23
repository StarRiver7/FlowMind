package com.company.aiplatform.auth.security;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;
import java.util.UUID;

/**
 * JWT Access Token 工具类 — 生成、校验、解析
 * <p>
 * 职责边界（分层责任原则）：
 * - Access Token：无状态 JWT，短有效期（≤15分钟），负责请求认证
 * - Refresh Token：移交给 RefreshTokenService，存入 Redis 实现服务端管控
 * </p>
 *
 * @see com.company.aiplatform.auth.service.IRefreshTokenService
 */
@Slf4j
@Component
public class JwtTokenProvider {

    private final SecretKey secretKey;

    /** Access Token 有效期（毫秒） */
    @Getter
    private final long expiration;

    /** Refresh Token 有效期（毫秒），供 RefreshTokenService Redis TTL 使用 */
    @Getter
    private final long refreshExpiration;

    /** JWT 签发者标识 */
    private final String issuer;

    public JwtTokenProvider(
            @Value("${jwt.secret}") String secret,
            @Value("${jwt.expiration}") long expiration,
            @Value("${jwt.refresh-expiration}") long refreshExpiration,
            @Value("${jwt.issuer:enterprise-ai-agent-platform}") String issuer) {
        this.secretKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.expiration = expiration;
        this.refreshExpiration = refreshExpiration;
        this.issuer = issuer;
    }

    /**
     * 生成访问令牌（Access Token）
     * <p>
     * 最小权限原则：仅包含 userId、username、roles，不存储敏感数据
     * jti 声明用于黑名单精确失效控制
     * </p>
     *
     * @param userId   用户ID
     * @param username 用户名
     * @param roles    角色编码列表
     * @return JWT Access Token 字符串
     */
    public String generateAccessToken(Long userId, String username, List<String> roles) {
        Date now = new Date();
        return Jwts.builder()
                .id(UUID.randomUUID().toString())          // jti：令牌唯一标识，用于黑名单
                .issuer(issuer)
                .subject(String.valueOf(userId))
                .claim("username", username)
                .claim("roles", roles)
                .issuedAt(now)
                .expiration(new Date(now.getTime() + expiration))
                .signWith(secretKey)
                .compact();
    }

    /**
     * 从 Token 中提取令牌唯一标识（jti）
     */
    public String getTokenId(String token) {
        return parseClaims(token).getId();
    }

    /**
     * 从 Token 中提取用户ID
     */
    public Long getUserId(String token) {
        return Long.parseLong(parseClaims(token).getSubject());
    }

    /**
     * 从 Token 中提取用户名
     */
    public String getUsername(String token) {
        return parseClaims(token).get("username", String.class);
    }

    /**
     * 从 Token 中提取角色列表
     */
    @SuppressWarnings("unchecked")
    public List<String> getRoles(String token) {
        return parseClaims(token).get("roles", List.class);
    }

    /**
     * 获取 Token 的过期时间，用于黑名单 TTL 计算
     */
    public Date getExpirationDate(String token) {
        return parseClaims(token).getExpiration();
    }

    /**
     * 验证 Token 是否合法（签名 + 过期）
     */
    public boolean validateToken(String token) {
        try {
            parseClaims(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            log.debug("JWT validation failed: {}", e.getMessage());
            return false;
        }
    }

    private Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}