package com.company.aiplatform.auth.service.impl;

import com.company.aiplatform.auth.service.ITokenBlacklistService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.Date;
import java.util.Set;


@Slf4j
@Service
public class TokenBlacklistServiceImpl implements ITokenBlacklistService {

    private static final String KEY_PREFIX = "jwt:blacklist:";

    private final RedisTemplate<String, Object> redisTemplate;

    public TokenBlacklistServiceImpl(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    /**
     * 将 Access Token 加入黑名单
     *
     * @param tokenId       令牌唯一标识（jti）
     * @param expirationDate 令牌过期时间，用于计算黑名单 TTL
     */
    @Override
    public void blacklist(String tokenId, Date expirationDate) {
        long remainingMs = expirationDate.getTime() - Instant.now().toEpochMilli();
        if (remainingMs <= 0) {
            log.debug("Token已经过期，无法加入黑名单: jti={}", tokenId);
            return;
        }
        String key = buildKey(tokenId);
        redisTemplate.opsForValue().set(key, "1", Duration.ofMillis(remainingMs));
        log.info("Access token 已经加入黑名单: jti={}, ttl={}s", tokenId, remainingMs / 1000);
    }

    /**
     * 检查 Token 是否在黑名单中
     *
     * @param tokenId 令牌唯一标识（jti）
     * @return true 表示 Token 已被撤销
     */
    @Override
    public boolean isBlacklisted(String tokenId) {
        String key = buildKey(tokenId);
        return redisTemplate.hasKey(key);
    }

    /**
     * 批量检查 Token 是否在黑名单中
     *
     * @param tokenIds 令牌唯一标识集合
     * @return 已加入黑名单的 tokenId 集合
     */
    @Override
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