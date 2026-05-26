package com.company.aiplatform.auth.controller;

import com.company.aiplatform.auth.service.IAuthService;
import com.company.aiplatform.auth.dto.LoginReq;
import com.company.aiplatform.auth.dto.RefreshTokenReq;
import com.company.aiplatform.auth.dto.RegisterReq;
import com.company.aiplatform.auth.vo.LoginVO;
import com.company.aiplatform.common.result.Result;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;

@Tag(name = "认证管理", description = "用户注册、登录、Token管理")
@RestController
@RequestMapping("/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final IAuthService iAuthService;

    @Operation(summary = "用户注册")
    @PostMapping("/register")
    public Result<Void> register(@Valid @RequestBody RegisterReq req) {
        iAuthService.register(req);
        return Result.success("注册成功");
    }

    @Operation(summary = "用户登录 — 返回 Access Token + Refresh Token")
    @PostMapping("/login")
    public Result<LoginVO> login(@Valid @RequestBody LoginReq req, HttpServletRequest request) {
        String ip = getClientIp(request);
        String userAgent = request.getHeader("User-Agent");
        LoginVO vo = iAuthService.login(req, ip, userAgent);
        return Result.success(vo);
    }

    @Operation(summary = "刷新Token — 传入refreshToken")
    @PostMapping("/refresh")
    public Result<LoginVO> refresh(@Valid @RequestBody RefreshTokenReq req, HttpServletRequest request) {
        String ip = getClientIp(request);
        String userAgent = request.getHeader("User-Agent");
        LoginVO vo = iAuthService.refreshToken(req.getRefreshToken(), ip, userAgent);
        return Result.success(vo);
    }

    @Operation(summary = "退出登录 — Access Token 加入黑名单，Refresh Token 从 Redis 删除")
    @PostMapping("/logout")
    public Result<Void> logout(@RequestBody(required = false) RefreshTokenReq req,
                               HttpServletRequest request) {
        String accessToken = extractToken(request);
        String refreshToken = req != null ? req.getRefreshToken() : null;
        String ip = getClientIp(request);
        String userAgent = request.getHeader("User-Agent");
        iAuthService.logout(accessToken, refreshToken, ip, userAgent);
        return Result.success("已登出");
    }

    // 获取客户端IP地址
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

    // 从请求头中提取Token
    private String extractToken(HttpServletRequest request) {
        String bearer = request.getHeader("Authorization");
        if (StringUtils.hasText(bearer) && bearer.startsWith("Bearer ")) {
            return bearer.substring(7);
        }
        return null;
    }
}