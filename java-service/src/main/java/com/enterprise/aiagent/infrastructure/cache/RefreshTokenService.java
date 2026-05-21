package com.enterprise.aiagent.infrastructure.cache;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Collections;
import java.util.UUID;

/**
 * Refresh Token 服务 — 基于 Redis 的刷新令牌管理
 *
 * <p>设计原则（企业级有状态+无状态混合认证）：</p>
 * <ul>
 *   <li>Refresh Token 以不透明字符串（UUID）存入 Redis，不使用 JWT</li>
 *   <li>Redis Key 格式：refresh_token:{userId}:{deviceId}</li>
 *   <li>每次刷新时执行原子 Lua 脚本：验证 → 轮换新令牌 → 重置 TTL</li>
 *   <li>滑动刷新：剩余有效期 &lt; 总有效期 1/4 时自动延长 TTL</li>
 *   <li>强制登出时直接删除 Key，实现即时失效</li>
 * </ul>
 *
 * @see com.enterprise.aiagent.infrastructure.security.JwtTokenProvider
 */
@Slf4j
@Service
public class RefreshTokenService {

    private static final String KEY_PREFIX = "refresh_token:";

    /** 滑动刷新阈值：剩余有效期低于此比例时自动延长 */
    private static final double SLIDING_REFRESH_THRESHOLD = 0.25;

    /**
     * Lua 脚本：原子性地验证 + 轮换 Refresh Token
     * <p>
     * KEYS[1]：refresh_token key
     * ARGV[1]：期望的旧令牌值
     * ARGV[2]：新令牌值
     * ARGV[3]：TTL（秒）
     * </p>
     * <p>
     * 返回值：1 = 成功，nil = 失败（令牌不存在或不匹配）
     * </p>
     */
    private static final String REFRESH_LUA_SCRIPT = """
            local current = redis.call('GET', KEYS[1])
            if current == false then
                return nil
            end
            if current ~= ARGV[1] then
                return nil
            end
            redis.call('SET', KEYS[1], ARGV[2], 'EX', ARGV[3])
            return 1
            """;

    private final RedisTemplate<String, Object> redisTemplate;
    private final DefaultRedisScript<Long> refreshScript;
    private final long refreshTokenTtlSeconds;

    public RefreshTokenService(
            RedisTemplate<String, Object> redisTemplate,
            @Value("${jwt.refresh-expiration}") long refreshExpirationMs) {
        this.redisTemplate = redisTemplate;
        this.refreshTokenTtlSeconds = refreshExpirationMs / 1000;

        this.refreshScript = new DefaultRedisScript<>();
        this.refreshScript.setScriptText(REFRESH_LUA_SCRIPT);
        this.refreshScript.setResultType(Long.class);
    }

    /**
     * 生成新的不透明 Refresh Token 并存入 Redis
     *
     * @param userId   用户ID
     * @param deviceId 设备标识（用于多端登录隔离）
     * @return 生成的 Refresh Token 字符串
     */
    public String createRefreshToken(Long userId, String deviceId) {
        String token = UUID.randomUUID().toString().replace("-", "");
        String key = buildKey(userId, deviceId);
        redisTemplate.opsForValue().set(key, token, Duration.ofSeconds(refreshTokenTtlSeconds));
        log.debug("Refresh token created: userId={}, deviceId={}, key={}", userId, deviceId, key);
        return token;
    }

    /**
     * 验证并轮换 Refresh Token（原子操作）
     * <p>
     * 验证旧令牌 → 若有效则生成新令牌替换 → 重置 TTL
     * 使用 Lua 脚本保证并发安全
     * </p>
     *
     * @param userId       用户ID
     * @param deviceId     设备标识
     * @param oldToken     旧 Refresh Token
     * @return 新的 Refresh Token；验证失败返回 null
     */
    public String rotateRefreshToken(Long userId, String deviceId, String oldToken) {
        String newToken = UUID.randomUUID().toString().replace("-", "");
        String key = buildKey(userId, deviceId);

        Long result = redisTemplate.execute(
                refreshScript,
                Collections.singletonList(key),
                oldToken,
                newToken,
                String.valueOf(refreshTokenTtlSeconds)
        );

        if (result != null && result == 1L) {
            log.debug("Refresh token rotated: userId={}, deviceId={}", userId, deviceId);
            return newToken;
        }
        log.warn("Refresh token rotation failed: userId={}, deviceId={}", userId, deviceId);
        return null;
    }

    /**
     * 验证 Refresh Token 是否有效（不轮换，仅检查）
     *
     * @param userId   用户ID
     * @param deviceId 设备标识
     * @param token    待验证的 Refresh Token
     * @return true 如果令牌存在且匹配
     */
    public boolean validateRefreshToken(Long userId, String deviceId, String token) {
        String key = buildKey(userId, deviceId);
        String stored = (String) redisTemplate.opsForValue().get(key);
        boolean valid = token != null && token.equals(stored);
        if (!valid) {
            log.debug("Refresh token validation failed: userId={}, deviceId={}", userId, deviceId);
        }
        return valid;
    }

    /**
     * 检查是否需要进行滑动刷新（剩余 TTL &lt; 总 TTL × 阈值）
     *
     * @param userId   用户ID
     * @param deviceId 设备标识
     * @return true 表示需要延长 TTL
     */
    public boolean needsSlidingRefresh(Long userId, String deviceId) {
        String key = buildKey(userId, deviceId);
        Long ttl = redisTemplate.getExpire(key);
        if (ttl == null || ttl < 0) {
            return false;
        }
        return ttl < refreshTokenTtlSeconds * SLIDING_REFRESH_THRESHOLD;
    }

    /**
     * 强制删除 Refresh Token（登出时调用）
     *
     * @param userId   用户ID
     * @param deviceId 设备标识
     */
    public void deleteRefreshToken(Long userId, String deviceId) {
        String key = buildKey(userId, deviceId);
        Boolean deleted = redisTemplate.delete(key);
        if (Boolean.TRUE.equals(deleted)) {
            log.info("Refresh token deleted (logout): userId={}, deviceId={}", userId, deviceId);
        }
    }

    /**
     * 删除用户所有设备的 Refresh Token（全局强制登出）
     *
     * @param userId 用户ID
     */
    public void deleteAllUserTokens(Long userId) {
        String pattern = KEY_PREFIX + userId + ":*";
        var keys = redisTemplate.keys(pattern);
        if (keys != null && !keys.isEmpty()) {
            Long deleted = redisTemplate.delete(keys);
            log.info("All refresh tokens deleted for user: userId={}, count={}", userId, deleted);
        }
    }

    /** 构建 Redis Key */
    private String buildKey(Long userId, String deviceId) {
        return KEY_PREFIX + userId + ":" + deviceId;
    }
}