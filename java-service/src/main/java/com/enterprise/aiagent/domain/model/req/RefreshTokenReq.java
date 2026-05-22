package com.enterprise.aiagent.domain.model.req;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Token刷新请求 — 仅需传入 refreshToken，userId由后端自动解析
 */
@Data
public class RefreshTokenReq {

    @NotBlank(message = "refreshToken不能为空")
    private String refreshToken;
}