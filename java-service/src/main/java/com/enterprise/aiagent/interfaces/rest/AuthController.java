package com.enterprise.aiagent.interfaces.rest;

import com.enterprise.aiagent.application.service.AuthService;
import com.enterprise.aiagent.domain.model.req.LoginReq;
import com.enterprise.aiagent.domain.model.req.RefreshTokenReq;
import com.enterprise.aiagent.domain.model.req.RegisterReq;
import com.enterprise.aiagent.domain.model.vo.LoginVO;
import com.enterprise.aiagent.infrastructure.common.Result;
import com.enterprise.aiagent.infrastructure.security.JwtTokenProvider;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

@Tag(name = "认证管理", description = "用户注册、登录、Token管理")
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;
    private final JwtTokenProvider jwtTokenProvider;

    @Operation(summary = "用户注册")
    @PostMapping("/register")
    public Result<Void> register(@Valid @RequestBody RegisterReq req) {
        authService.register(req);
        return Result.success("注册成功");
    }

    @Operation(summary = "用户登录 — 返回 Access Token + Refresh Token + deviceId")
    @PostMapping("/login")
    public Result<LoginVO> login(@Valid @RequestBody LoginReq req, HttpServletRequest request) {
        String ip = getClientIp(request);
        String userAgent = request.getHeader("User-Agent");
        LoginVO vo = authService.login(req, ip, userAgent);
        return Result.success(vo);
    }

    @Operation(summary = "刷新Token — 使用 Redis 中的 Refresh Token 轮换新令牌对")
    @PostMapping("/refresh")
    public Result<LoginVO> refresh(@Valid @RequestBody RefreshTokenReq req, HttpServletRequest request) {
        String ip = getClientIp(request);
        String userAgent = request.getHeader("User-Agent");
        LoginVO vo = authService.refreshToken(
                req.getUserId(), req.getDeviceId(), req.getRefreshToken(), ip, userAgent);
        return Result.success(vo);
    }

    @Operation(summary = "退出登录 — Access Token 加入黑名单 + 删除 Refresh Token")
    @PostMapping("/logout")
    public Result<Void> logout(@RequestParam(required = false) String deviceId,
                               HttpServletRequest request) {
        String accessToken = extractToken(request);
        String ip = getClientIp(request);
        String userAgent = request.getHeader("User-Agent");

        Long userId = null;
        if (StringUtils.hasText(accessToken) && jwtTokenProvider.validateToken(accessToken)) {
            userId = jwtTokenProvider.getUserId(accessToken);
        }

        if (userId != null) {
            authService.logout(accessToken, userId, deviceId, ip, userAgent);
        }
        return Result.success("已登出");
    }

    private String getClientIp(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isBlank() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("X-Real-IP");
        }
        if (ip == null || ip.isBlank() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getRemoteAddr();
        }
        if (ip != null && ip.contains(",")) {
            ip = ip.split(",")[0].trim();
        }
        return ip;
    }

    private String extractToken(HttpServletRequest request) {
        String bearer = request.getHeader("Authorization");
        if (StringUtils.hasText(bearer) && bearer.startsWith("Bearer ")) {
            return bearer.substring(7);
        }
        return null;
    }
}