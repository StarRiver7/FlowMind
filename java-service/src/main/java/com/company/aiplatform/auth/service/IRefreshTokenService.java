package com.company.aiplatform.auth.service;

/**
 * Refresh Token 服务接口
 */
public interface IRefreshTokenService {

    /** 生成新的 Refresh Token 并存入 Redis */
    String generateRefreshToken(Long userId, String deviceId);

    /** 从令牌中解析 userId */
    Long parseUserId(String token);

    /** 验证 Refresh Token 并执行滑动刷新（必要时延长 TTL） */
    boolean validateAndExtendTtl(String token, String deviceId);

    /** 删除 Refresh Token（登出时调用） */
    void deleteRefreshToken(String token, String deviceId);

    /** 删除用户所有设备的 Refresh Token（全局强制登出） */
    void deleteAllUserTokens(Long userId);
}
