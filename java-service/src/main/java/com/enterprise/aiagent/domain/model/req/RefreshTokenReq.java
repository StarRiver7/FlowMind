package com.enterprise.aiagent.domain.model.req;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

/**
 * Token刷新请求
 * <p>
 * 前端须将登录返回的 userId、deviceId、refreshToken 一并提交，
 * 后端使用 userId + deviceId 定位 Redis 中的 Refresh Token 进行验证。
 * </p>
 */
@Data
public class RefreshTokenReq {

    @NotNull(message = "userId不能为空")
    private Long userId;

    @NotBlank(message = "deviceId不能为空")
    private String deviceId;

    @NotBlank(message = "refreshToken不能为空")
    private String refreshToken;
}