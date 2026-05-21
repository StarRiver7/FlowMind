package com.enterprise.aiagent.domain.model.req;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * 注册请求
 */
@Data
public class RegisterReq {

    @NotBlank(message = "用户名不能为空")
    @Size(min = 2, max = 64, message = "用户名长度2-64位")
    private String username;

    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 128, message = "密码长度6-128位")
    private String password;

    @Email(message = "邮箱格式不正确")
    private String email;

    @Size(max = 64, message = "昵称最长64位")
    private String nickname;
}
