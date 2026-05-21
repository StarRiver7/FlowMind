package com.enterprise.aiagent.application.service;

import com.enterprise.aiagent.domain.enums.ResultCode;
import com.enterprise.aiagent.domain.model.entity.LoginLog;
import com.enterprise.aiagent.domain.model.entity.User;
import com.enterprise.aiagent.domain.model.entity.UserRole;
import com.enterprise.aiagent.domain.model.req.LoginReq;
import com.enterprise.aiagent.domain.model.req.RegisterReq;
import com.enterprise.aiagent.domain.model.vo.LoginVO;
import com.enterprise.aiagent.domain.repository.LoginLogMapper;
import com.enterprise.aiagent.domain.repository.UserMapper;
import com.enterprise.aiagent.domain.repository.UserRoleMapper;
import com.enterprise.aiagent.infrastructure.cache.RefreshTokenService;
import com.enterprise.aiagent.infrastructure.cache.TokenBlacklistService;
import com.enterprise.aiagent.infrastructure.common.BusinessException;
import com.enterprise.aiagent.infrastructure.security.JwtTokenProvider;
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

/**
 * 认证服务 — 注册、登录、Token刷新、登出
 *
 * <p>企业级混合认证架构：</p>
 * <ul>
 *   <li>Access Token：无状态 JWT，短有效期（15min），通过 Bearer header 传递</li>
 *   <li>Refresh Token：不透明令牌，存入 Redis，服务端可控，支持滑动刷新与强制失效</li>
 *   <li>Token 黑名单：登出时将 Access Token 的 jti 加入 Redis 黑名单，阻止重用</li>
 * </ul>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserMapper userMapper;
    private final UserRoleMapper userRoleMapper;
    private final LoginLogMapper loginLogMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final RefreshTokenService refreshTokenService;
    private final TokenBlacklistService tokenBlacklistService;

    /**
     * 用户注册 — 默认分配 employee 角色（role_id = 4）
     */
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
        userMapper.insert((User) user);

        UserRole ur = new UserRole();
        ur.setUserId(user.getId());
        ur.setRoleId(4L);
        ur.setCreateTime(LocalDateTime.now());
        userRoleMapper.insert((UserRole) ur);

        log.info("User registered: username={}, id={}", user.getUsername(), user.getId());
    }

    /**
     * 用户登录 — 生成双 Token
     * <ul>
     *   <li>Access Token：无状态 JWT，有效期 15 分钟，通过 Bearer header 传递</li>
     *   <li>Refresh Token：不透明 UUID，存入 Redis（Key: refresh_token:{userId}:{deviceId}），有效期 7 天</li>
     * </ul>
     */
    @Transactional
    public LoginVO login(LoginReq req, String ip, String userAgent) {
        User user = userMapper.findByUsername(req.getUsername())
                .orElseThrow(() -> new BusinessException(ResultCode.UNAUTHORIZED, "用户名或密码错误"));

        if (user.getStatus() == 0) {
            recordLoginLog(user.getId(), req.getUsername(), "LOGIN", ip, userAgent, 0, "用户已被禁用");
            throw new BusinessException(ResultCode.UNAUTHORIZED, "用户已被禁用，请联系管理员");
        }

        if (!passwordEncoder.matches(req.getPassword(), user.getPassword())) {
            recordLoginLog(user.getId(), req.getUsername(), "LOGIN", ip, userAgent, 0, "密码错误");
            throw new BusinessException(ResultCode.UNAUTHORIZED, "用户名或密码错误");
        }

        // 更新最后登录信息
        user.setLastLoginTime(LocalDateTime.now());
        user.setLastLoginIp(ip);
        userMapper.updateById(user);

        // 确定 deviceId：优先使用客户端传入值，否则从 User-Agent 生成
        String deviceId = resolveDeviceId(req.getDeviceId(), userAgent);

        // 生成 Access Token（无状态 JWT）
        List<String> roles = userMapper.findRoleCodesByUserId(user.getId());
        String accessToken = jwtTokenProvider.generateAccessToken(user.getId(), user.getUsername(), roles);

        // 生成 Refresh Token（不透明，存入 Redis）
        String refreshToken = refreshTokenService.createRefreshToken(user.getId(), deviceId);

        recordLoginLog(user.getId(), user.getUsername(), "LOGIN", ip, userAgent, 1, null);

        log.info("用户登录: username={}, roles={}, deviceId={}", user.getUsername(), roles, deviceId);

        return LoginVO.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .deviceId(deviceId)
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
     * <p>
     * 流程：Redis 验证 Refresh Token → 原子轮换新 Refresh Token → 签发新 Access Token
     * </p>
     *
     * @param userId       用户ID（用于 Redis Key 定位）
     * @param deviceId     设备标识
     * @param refreshToken 当前的 Refresh Token
     * @param ip           客户端 IP
     * @param userAgent    客户端 User-Agent
     * @return 新的 Token 对
     */
    @Transactional
    public LoginVO refreshToken(Long userId, String deviceId, String refreshToken,
                                String ip, String userAgent) {
        // 验证用户状态
        User user = userMapper.selectById(userId);
        if (user == null || user.getStatus() == 0) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "用户不存在或已禁用");
        }

        // Redis 原子验证 + 轮换 Refresh Token
        String newRefreshToken = refreshTokenService.rotateRefreshToken(userId, deviceId, refreshToken);
        if (newRefreshToken == null) {
            recordLoginLog(userId, user.getUsername(), "REFRESH", ip, userAgent, 0, "Refresh Token无效");
            throw new BusinessException(ResultCode.UNAUTHORIZED, "refreshToken无效或已过期");
        }

        // 签发新 Access Token
        List<String> roles = userMapper.findRoleCodesByUserId(userId);
        String newAccessToken = jwtTokenProvider.generateAccessToken(userId, user.getUsername(), roles);

        recordLoginLog(userId, user.getUsername(), "REFRESH", ip, userAgent, 1, null);

        log.info("Token refreshed: userId={}, deviceId={}", userId, deviceId);

        return LoginVO.builder()
                .accessToken(newAccessToken)
                .refreshToken(newRefreshToken)
                .deviceId(deviceId)
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
     * 登出 — 双重失效机制
     * <ul>
     *   <li>将当前 Access Token 加入 Redis 黑名单（阻止重用）</li>
     *   <li>删除 Redis 中的 Refresh Token（阻止续期）</li>
     * </ul>
     *
     * @param accessToken  当前 Access Token（用于提取 jti 加入黑名单）
     * @param userId       用户ID
     * @param deviceId     设备标识（可选，传入时精确删除该设备 Refresh Token）
     * @param ip           客户端 IP
     * @param userAgent    客户端 User-Agent
     */
    public void logout(String accessToken, Long userId, String deviceId,
                       String ip, String userAgent) {
        // 将 Access Token 加入黑名单
        if (accessToken != null && jwtTokenProvider.validateToken(accessToken)) {
            String tokenId = jwtTokenProvider.getTokenId(accessToken);
            tokenBlacklistService.blacklist(tokenId, jwtTokenProvider.getExpirationDate(accessToken));
        }

        // 删除 Refresh Token（精确到设备或全部设备）
        if (deviceId != null && !deviceId.isBlank()) {
            refreshTokenService.deleteRefreshToken(userId, deviceId);
        } else {
            refreshTokenService.deleteAllUserTokens(userId);
        }

        User user = userMapper.selectById(userId);
        String username = user != null ? user.getUsername() : String.valueOf(userId);
        recordLoginLog(userId, username, "LOGOUT", ip, userAgent, 1, null);

        log.info("User logged out: userId={}, deviceId={}", userId,
                deviceId != null ? deviceId : "ALL");
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
        loginLogMapper.insert((LoginLog) logEntry);
    }

    /**
     * 解析设备标识
     * <p>优先使用客户端传入的 deviceId，否则对 User-Agent 做 SHA-256 取前 16 位</p>
     */
    private String resolveDeviceId(String clientDeviceId, String userAgent) {
        if (clientDeviceId != null && !clientDeviceId.isBlank()) {
            return clientDeviceId;
        }
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