package com.company.aiplatform.user.vo;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 用户详情 VO — 含角色列表
 */
@Data
@Builder
public class UserVO {

    private Long id;
    private String username;
    private String nickname;
    private String email;
    private String phone;
    private String avatarUrl;
    private Integer status;
    private LocalDateTime lastLoginTime;
    private List<String> roles;
    private LocalDateTime createTime;
}
