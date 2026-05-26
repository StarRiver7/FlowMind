package com.company.aiplatform.auth.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * 登录请求
 */
@Data
@Schema(description = "登录请求参数")
public class LoginReq {

    @Schema(description = "用户名", example = "admin")
    private String username;

    @Size(max = 128, message = "邮箱最长128位")
    @Schema(description = "邮箱（邮箱登录时使用）", example = "admin@flowmind.com")
    private String email;

    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 128, message = "密码长度6-128位")
    @Schema(description = "密码", example = "123456")
    private String password;
}