package com.enterprise.aiagent.domain.model.req;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

/**
 * 用户角色分配请求
 */
@Data
public class AssignRoleReq {

    @NotNull(message = "用户ID不能为空")
    private Long userId;

    @NotEmpty(message = "角色列表不能为空")
    private List<Long> roleIds;
}
