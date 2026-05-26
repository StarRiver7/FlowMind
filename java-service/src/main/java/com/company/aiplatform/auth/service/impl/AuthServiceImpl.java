package com.company.aiplatform.auth.service.impl;

import com.company.aiplatform.auth.dto.LoginReq;
import com.company.aiplatform.auth.dto.RegisterReq;
import com.company.aiplatform.auth.entity.LoginLog;
import com.company.aiplatform.auth.entity.User;
import com.company.aiplatform.auth.entity.UserRole;
import com.company.aiplatform.auth.mapper.LoginLogMapper;
import com.company.aiplatform.auth.mapper.UserMapper;
import com.company.aiplatform.auth.mapper.UserRoleMapper;
import com.company.aiplatform.auth.security.JwtTokenProvider;
import com.company.aiplatform.auth.service.IAuthService;
import com.company.aiplatform.auth.service.IRefreshTokenService;
import com.company.aiplatform.auth.service.ITokenBlacklistService;
import com.company.aiplatform.auth.vo.LoginVO;
import com.company.aiplatform.common.enums.ResultCode;
import com.company.aiplatform.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDateTime;
import java.util.HexFormat;
import java.util.List;


@Slf4j
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements IAuthService {

    private final UserMapper userMapper;
    private final UserRoleMapper userRoleMapper;
    private final LoginLogMapper loginLogMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final IRefreshTokenService refreshTokenService;
    private final ITokenBlacklistService tokenBlacklistService;

    @Override
    @Transactional
    public void register(RegisterReq req) {
        if (userMapper.findByUsername(req.getUsername()).isPresent()) {
            throw new BusinessException(ResultCode.BUSINESS_ERROR, "用户名已存在");
        }
        if (req.getEmail() != null && userMapper.findByEmail(req.getEmail()).isPresent()) {
            throw new BusinessException(ResultCode.BUSINESS_ERROR, "邮箱已被注册");
        }

        User user = new User();
        user.setUsername(req.getUsername());
        user.setPassword(passwordEncoder.encode(req.getPassword()));
        user.setEmail(req.getEmail());
        user.setNickname(req.getNickname() != null ? req.getNickname() : req.getUsername());
        user.setStatus(1);
        userMapper.insert(user);

        UserRole ur = new UserRole();
        ur.setUserId(user.getId());
        ur.setRoleId(4L);
        ur.setCreateTime(LocalDateTime.now());
        userRoleMapper.insert(ur);

        log.info("【用户注册】: username={}, id={}", user.getUsername(), user.getId());
    }

    /**
     * 用户登录 — 生成双 Token
     * <ul>
     *   <li>Access Token：无状态 JWT，15min</li>
     *   <li>Refresh Token：{userId}:{uuid} 格式，存入 Redis</li>
     *   <li>deviceId：自动从 User-Agent 推导，支持同浏览器自动续期</li>
     * </ul>
     */
    @Override
    @Transactional
    public LoginVO login(LoginReq req, String ip, String userAgent) {
        // 支持邮箱登录：优先使用邮箱查找，否则使用用户名
        User user;
        if (req.getEmail() != null && !req.getEmail().isBlank()) {
            user = userMapper.findByEmail(req.getEmail())
                    .orElseThrow(() -> new BusinessException(ResultCode.UNAUTHORIZED, "邮箱或密码错误"));
        } else {
            user = userMapper.findByUsername(req.getUsername())
                    .orElseThrow(() -> new BusinessException(ResultCode.UNAUTHORIZED, "用户名或密码错误"));
        }

        if (user.getStatus() == 0) {
            recordLoginLog(user.getId(), req.getUsername(), "LOGIN", ip, userAgent, 0, "用户已被禁用");
            throw new BusinessException(ResultCode.UNAUTHORIZED, "用户已被禁用，请联系管理员");
        }

        if (!passwordEncoder.matches(req.getPassword(), user.getPassword())) {
            recordLoginLog(user.getId(), req.getUsername(), "LOGIN", ip, userAgent, 0, "密码错误");
            throw new BusinessException(ResultCode.UNAUTHORIZED, "用户名或密码错误");
        }

        // 更新用户登录信息
        user.setLastLoginTime(LocalDateTime.now());
        user.setLastLoginIp(ip);
        userMapper.updateById(user);

        String deviceId = deriveDeviceId(userAgent);

        // 获取用户角色
        List<String> roles = userMapper.findRoleCodesByUserId(user.getId());
        // 生成 Access Token
        String accessToken = jwtTokenProvider.generateAccessToken(user.getId(), user.getUsername(), roles);

        // 生成 Refresh Token
        // Refresh Token 格式：{userId}:{uuid}，后端可自解析 userId
        String refreshToken = refreshTokenService.generateRefreshToken(user.getId(), deviceId);

        recordLoginLog(user.getId(), user.getUsername(), "LOGIN", ip, userAgent, 1, null);
        log.info("用户登录: username={}, roles={}, deviceId={}", user.getUsername(), roles, deviceId);

        return LoginVO.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .expiresIn(jwtTokenProvider.getExpiration() / 1000)
                .userInfo(LoginVO.UserInfo.builder()
                        .id(user.getId())
                        .username(user.getUsername())
                        .nickname(user.getNickname())
                        .email(user.getEmail())
                        .avatarUrl(user.getAvatarUrl())
                        .build())
                .build();
    }

    /**
     * 刷新 Access Token
     * <p>从 refreshToken 中自动解析 userId，从 User-Agent 自动推导 deviceId</p>
     *
     * @param refreshToken 当前的 Refresh Token
     * @param ip           客户端 IP
     * @param userAgent    客户端 User-Agent（用于推导 deviceId）
     * @return 新的 Token 对
     */

    /**
     * 刷新 Access Token（滑动刷新）
     * <p>
     * 验证 Refresh Token → 签发新 Access Token → 必要时延长 Redis TTL。
     * Refresh Token 值不变（不轮换），避免并发竞态。
     * </p>
     */
    @Override
    @Transactional
    public LoginVO refreshToken(String refreshToken, String ip, String userAgent) {
        String deviceId = deriveDeviceId(userAgent);

        // 验证 Refresh Token 并执行滑动刷新（TTL < 1/4 时自动延长）
        if (!refreshTokenService.validateAndExtendTtl(refreshToken, deviceId)) {
            Long userId = refreshTokenService.parseUserId(refreshToken);
            String username = userId != null ? getUserName(userId) : "unknown";
            recordLoginLog(userId, username, "REFRESH", ip, userAgent, 0, "Refresh Token无效");
            throw new BusinessException(ResultCode.UNAUTHORIZED, "refreshToken无效或已过期");
        }

        Long userId = refreshTokenService.parseUserId(refreshToken);
        User user = userMapper.selectById(userId);
        if (user == null || user.getStatus() == 0) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "用户不存在或已禁用");
        }

        List<String> roles = userMapper.findRoleCodesByUserId(userId);
        String newAccessToken = jwtTokenProvider.generateAccessToken(userId, user.getUsername(), roles);

        recordLoginLog(userId, user.getUsername(), "REFRESH", ip, userAgent, 1, null);
        log.info("Token 被刷新: userId={}, deviceId={}", userId, deviceId);

        // refreshToken 值不变，原样返回
        return LoginVO.builder()
                .accessToken(newAccessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .expiresIn(jwtTokenProvider.getExpiration() / 1000)
                .userInfo(LoginVO.UserInfo.builder()
                        .id(user.getId())
                        .username(user.getUsername())
                        .nickname(user.getNickname())
                        .email(user.getEmail())
                        .avatarUrl(user.getAvatarUrl())
                        .build())
                .build();
    }

    /**
     * 登出 — 双重失效
     * <p>Access Token → 黑名单 / Refresh Token → Redis 删除</p>
     *
     * @param accessToken  当前 Access Token（从请求头提取）
     * @param refreshToken Refresh Token（可选，传入时精确删除）
     * @param ip           客户端 IP
     * @param userAgent    客户端 User-Agent
     */
    @Override
    public void logout(String accessToken, String refreshToken, String ip, String userAgent) {
        // Access Token 加入黑名单
        if (accessToken != null && jwtTokenProvider.validateToken(accessToken)) {
            String tokenId = jwtTokenProvider.getTokenId(accessToken);
            tokenBlacklistService.blacklist(tokenId, jwtTokenProvider.getExpirationDate(accessToken));
        }

        // Refresh Token 从 Redis 删除
        if (refreshToken != null && !refreshToken.isBlank()) {
            String deviceId = deriveDeviceId(userAgent);
            refreshTokenService.deleteRefreshToken(refreshToken, deviceId);
        }

        // Access Token 中提取 userId 用于日志
        Long userId = null;
        String username = "unknown";
        if (accessToken != null && jwtTokenProvider.validateToken(accessToken)) {
            userId = jwtTokenProvider.getUserId(accessToken);
            username = jwtTokenProvider.getUsername(accessToken);
        }
        recordLoginLog(userId, username, "LOGOUT", ip, userAgent, 1, null);
        log.info("用户登出: userId={}", userId);
    }

    private void recordLoginLog(Long userId, String username, String loginType,
                                String ip, String userAgent, int status, String failReason) {
        LoginLog logEntry = new LoginLog();
        logEntry.setUserId(userId);
        logEntry.setUsername(username);
        logEntry.setLoginType(loginType);
        logEntry.setIpAddress(ip);
        logEntry.setUserAgent(userAgent);
        logEntry.setStatus(status);
        logEntry.setFailReason(failReason);
        loginLogMapper.insert(logEntry);
    }

    private String getUserName(Long userId) {
        User user = userMapper.selectById(userId);
        return user != null ? user.getUsername() : String.valueOf(userId);
    }

    /**
     * 从 User-Agent 推导设备标识（SHA-256 前 16 位）
     * <p>同一浏览器同一版本 → 相同 deviceId → 自动命中同一 Redis Key</p>
     */
    private String deriveDeviceId(String userAgent) {
        if (userAgent == null || userAgent.isBlank()) {
            return "unknown";
        }
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(userAgent.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash).substring(0, 16);
        } catch (NoSuchAlgorithmException e) {
            return Integer.toHexString(userAgent.hashCode());
        }
    }
}