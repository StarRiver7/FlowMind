package com.enterprise.aiagent.infrastructure.security;

import com.enterprise.aiagent.infrastructure.cache.TokenBlacklistService;
import com.enterprise.aiagent.infrastructure.common.Result;
import com.enterprise.aiagent.domain.enums.ResultCode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * JWT 认证过滤器 — 每个请求拦截一次，从 Authorization header 提取并校验 Token
 * <p>
 * 认证链路：提取 Bearer Token → 校验签名/过期 → 检查黑名单 → 加载用户 → 设置 SecurityContext
 * </p>
 *
 * @see TokenBlacklistService
 * @see JwtTokenProvider
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenProvider jwtTokenProvider;
    private final UserDetailsServiceImpl userDetailsService;
    private final TokenBlacklistService tokenBlacklistService;
    private final ObjectMapper objectMapper;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        try {
            String token = extractToken(request);
            if (!StringUtils.hasText(token)) {
                filterChain.doFilter(request, response);
                return;
            }

            // 第一步：验证 Token 签名和有效期
            if (!jwtTokenProvider.validateToken(token)) {
                log.debug("JWT signature/expiry validation failed");
                filterChain.doFilter(request, response);
                return;
            }

            // 第二步：检查黑名单（防御纵深：即使 Token 未过期，仍可被主动撤销）
            String tokenId = jwtTokenProvider.getTokenId(token);
            if (tokenBlacklistService.isBlacklisted(tokenId)) {
                log.warn("Blacklisted token rejected: jti={}", tokenId);
                SecurityContextHolder.clearContext();
                filterChain.doFilter(request, response);
                return;
            }

            // 第三步：加载用户并设置认证上下文
            String username = jwtTokenProvider.getUsername(token);
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);

            UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
            authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));

            SecurityContextHolder.getContext().setAuthentication(authentication);
        } catch (Exception e) {
            log.debug("JWT authentication failed: {}", e.getMessage());
            SecurityContextHolder.clearContext();
        }

        filterChain.doFilter(request, response);
    }

    /**
     * 从请求头提取 Bearer Token（遵循全局规则 6.4 节）
     */
    private String extractToken(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}