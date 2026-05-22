package com.enterprise.aiagent.infrastructure.cache;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;

/**
 * Refresh Token 服务 — 基于 Redis 的刷新令牌管理
 *
 * <p>令牌格式：{userId}:{randomUUID}，userId 编码在令牌前缀中，后端自解析。</p>
 * <p>Redis Key：refresh_token:{userId}:{deviceId}，deviceId 由 User-Agent 自动推导。</p>
 *
 * <p>滑动刷新策略（遵循 08-token 存储方案）：</p>
 * <ul>
 *   <li>刷新 access token 时，不轮换 refresh token 值，仅检查并延长 Redis TTL</li>
 *   <li>当剩余 TTL &lt; 总 TTL × 1/4 时，自动重置为完整 7 天</li>
 *   <li>同一 refresh token 在整个会话周期内保持不变，前端只需存储一次</li>
 * </ul>
 */
@Slf4j
@Service
public class RefreshTokenService {

    private static final String KEY_PREFIX = "refresh_token:";
    private static final String TOKEN_SEPARATOR = ":";

    /** 滑动刷新阈值：剩余 TTL 低于此比例时自动延长（1/4 = 25%） */
    private static final double SLIDING_REFRESH_THRESHOLD = 0.25;

    private final RedisTemplate<String, Object> redisTemplate;
    private final long refreshTokenTtlSeconds;

    public RefreshTokenService(
            RedisTemplate<String, Object> redisTemplate,
            @Value("${jwt.refresh-expiration}") long refreshExpirationMs) {
        this.redisTemplate = redisTemplate;
        this.refreshTokenTtlSeconds = refreshExpirationMs / 1000;
    }

    /**
     * 生成新的 Refresh Token 并存入 Redis
     * <p>令牌格式：{userId}:{randomUUID}</p>
     *
     * @param userId   用户ID
     * @param deviceId 设备标识（由 User-Agent 推导）
     * @return Refresh Token 字符串
     */
    public String createRefreshToken(Long userId, String deviceId) {
        String uuid = java.util.UUID.randomUUID().toString().replace("-", "");
        String token = userId + TOKEN_SEPARATOR + uuid;
        String key = buildKey(userId, deviceId);
        redisTemplate.opsForValue().set(key, token, Duration.ofSeconds(refreshTokenTtlSeconds));
        log.debug("Refresh token created: userId={}, deviceId={}", userId, deviceId);
        return token;
    }

    /**
     * 从令牌中解析 userId
     */
    public Long parseUserId(String token) {
        if (token == null || !token.contains(TOKEN_SEPARATOR)) {
            return null;
        }
        try {
            return Long.parseLong(token.substring(0, token.indexOf(TOKEN_SEPARATOR)));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    /**
     * 验证 Refresh Token 并执行滑动刷新
     * <p>
     * 验证逻辑：GET Redis Key → 比对令牌值 → 检查 TTL → 必要时延长
     * 令牌值不变，仅可能延长 TTL，避免了令牌轮换带来的并发竞态问题。
     * </p>
     *
     * @param token    待验证的 Refresh Token
     * @param deviceId 设备标识
     * @return true 表示验证通过（含滑动刷新成功），false 表示令牌无效或已过期
     */
    public boolean validateAndExtendTtl(String token, String deviceId) {
        Long userId = parseUserId(token);
        if (userId == null) {
            return false;
        }
        String key = buildKey(userId, deviceId);
        String stored = (String) redisTemplate.opsForValue().get(key);

        // 令牌不存在或不匹配
        if (stored == null || !stored.equals(token)) {
            log.debug("Refresh token validation failed: userId={}, deviceId={}", userId, deviceId);
            return false;
        }

        // 滑动刷新：剩余 TTL < 阈值时，重置为完整 TTL
        Long currentTtl = redisTemplate.getExpire(key);
        if (currentTtl != null && currentTtl > 0
                && currentTtl < refreshTokenTtlSeconds * SLIDING_REFRESH_THRESHOLD) {
            redisTemplate.expire(key, Duration.ofSeconds(refreshTokenTtlSeconds));
            log.debug("Refresh token TTL extended (sliding refresh): userId={}, deviceId={}, oldTtl={}s",
                    userId, deviceId, currentTtl);
        }

        return true;
    }

    /**
     * 删除 Refresh Token（登出时调用）
     */
    public void deleteRefreshToken(String token, String deviceId) {
        Long userId = parseUserId(token);
        if (userId == null) {
            return;
        }
        String key = buildKey(userId, deviceId);
        Boolean deleted = redisTemplate.delete(key);
        if (Boolean.TRUE.equals(deleted)) {
            log.info("Refresh token deleted (logout): userId={}, deviceId={}", userId, deviceId);
        }
    }

    /**
     * 删除用户所有设备的 Refresh Token（全局强制登出）
     */
    public void deleteAllUserTokens(Long userId) {
        String pattern = KEY_PREFIX + userId + ":*";
        var keys = redisTemplate.keys(pattern);
        if (keys != null && !keys.isEmpty()) {
            Long deleted = redisTemplate.delete(keys);
            log.info("All refresh tokens deleted for user: userId={}, count={}", userId, deleted);
        }
    }

    private String buildKey(Long userId, String deviceId) {
        return KEY_PREFIX + userId + ":" + deviceId;
    }
}