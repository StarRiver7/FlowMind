package com.company.aiplatform.auth.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.Date;
import java.util.Set;

/**
 * Token 黑名单服务 — 基于 Redis 的 Access Token 失效管理
 *
 * <p>Key 模式：jwt:blacklist:{token_id}（遵循全局规则 5.5 节）</p>
 * <p>TTL = Access Token 剩余有效时间，过期后 Redis 自动清理</p>
 *
 * <p>使用场景：</p>
 * <ul>
 *   <li>用户主动登出：将当前 Access Token 加入黑名单</li>
 *   <li>管理员强制下线：将指定用户的 Access Token 加入黑名单</li>
 *   <li>安全事件响应：批量失效可疑 Token</li>
 * </ul>
 */
@Slf4j
@Service
public class TokenBlacklistService {

    private static final String KEY_PREFIX = "jwt:blacklist:";

    private final RedisTemplate<String, Object> redisTemplate;

    public TokenBlacklistService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    /**
     * 将 Access Token 加入黑名单
     *
     * @param tokenId       令牌唯一标识（jti）
     * @param expirationDate 令牌过期时间，用于计算黑名单 TTL
     */
    public void blacklist(String tokenId, Date expirationDate) {
        long remainingMs = expirationDate.getTime() - Instant.now().toEpochMilli();
        if (remainingMs <= 0) {
            log.debug("Token already expired, skip blacklist: jti={}", tokenId);
            return;
        }
        String key = buildKey(tokenId);
        redisTemplate.opsForValue().set(key, "1", Duration.ofMillis(remainingMs));
        log.info("Access token blacklisted: jti={}, ttl={}s", tokenId, remainingMs / 1000);
    }

    /**
     * 检查 Token 是否在黑名单中
     *
     * @param tokenId 令牌唯一标识（jti）
     * @return true 表示 Token 已被撤销
     */
    public boolean isBlacklisted(String tokenId) {
        String key = buildKey(tokenId);
        Boolean exists = redisTemplate.hasKey(key);
        return Boolean.TRUE.equals(exists);
    }

    /**
     * 批量检查 Token 是否在黑名单中
     *
     * @param tokenIds 令牌唯一标识集合
     * @return 已加入黑名单的 tokenId 集合
     */
    public Set<String> filterBlacklisted(Set<String> tokenIds) {
        return tokenIds.stream()
                .filter(this::isBlacklisted)
                .collect(java.util.stream.Collectors.toSet());
    }

    /** 构建 Redis Key */
    private String buildKey(String tokenId) {
        return KEY_PREFIX + tokenId;
    }
}