package com.enterprise.aiagent.domain.model.vo;

import lombok.Builder;
import lombok.Data;

/**
 * 登录响应 VO — 返回 Access Token、Refresh Token 和用户基本信息
 */
@Data
@Builder
public class LoginVO {

    private String accessToken;

    private String refreshToken;

    /** 设备标识，刷新 Token 时必须回传 */
    private String deviceId;

    private String tokenType;

    /** Access Token 过期时间（秒） */
    private Long expiresIn;

    private UserInfo userInfo;

    @Data
    @Builder
    public static class UserInfo {
        private Long id;
        private String username;
        private String nickname;
        private String email;
        private String avatarUrl;
    }
}