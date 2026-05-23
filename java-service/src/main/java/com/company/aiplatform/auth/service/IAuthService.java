package com.company.aiplatform.auth.service;

import com.company.aiplatform.auth.dto.LoginReq;
import com.company.aiplatform.auth.dto.RegisterReq;
import com.company.aiplatform.auth.vo.LoginVO;

/**
 * 认证服务接口
 */
public interface IAuthService {

    /** 用户注册 */
    void register(RegisterReq req);

    /** 用户登录，返回双 Token */
    LoginVO login(LoginReq req, String ip, String userAgent);

    /** 刷新 Access Token（滑动刷新） */
    LoginVO refreshToken(String refreshToken, String ip, String userAgent);

    /** 登出：Access Token 加入黑名单，Refresh Token 从 Redis 删除 */
    void logout(String accessToken, String refreshToken, String ip, String userAgent);
}
