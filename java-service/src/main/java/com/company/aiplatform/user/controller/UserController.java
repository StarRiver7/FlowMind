package com.company.aiplatform.user.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.company.aiplatform.auth.dto.AssignRoleReq;
import com.company.aiplatform.auth.vo.LoginVO;
import com.company.aiplatform.user.service.IUserService;
import com.company.aiplatform.user.vo.UserVO;
import com.company.aiplatform.annotation.CurrentUserId;
import com.company.aiplatform.common.result.Result;
import com.company.aiplatform.auth.security.JwtTokenProvider;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.security.Principal;

/**
 * 用户管理接口 — 需要 admin 角色
 */
@Tag(name = "用户管理", description = "用户CRUD、角色分配")
@RestController
@RequestMapping("/api/v1/admin/users")
@RequiredArgsConstructor
public class UserController {

    private final IUserService iUserService;

    @Operation(summary = "用户列表（分页）")
    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    public Result<IPage<UserVO>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) String keyword) {
        IPage<UserVO> result = iUserService.listUsers(page, pageSize, keyword);
        return Result.success(result);
    }

    @Operation(summary = "用户详情")
    @GetMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<UserVO> detail(@PathVariable Long id) {
        UserVO vo = iUserService.getUserDetail(id);
        return Result.success(vo);
    }

    @Operation(summary = "分配角色")
    @PostMapping("/roles")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<Void> assignRoles(@Valid @RequestBody AssignRoleReq req) {
        iUserService.assignRoles(req);
        return Result.success("角色分配成功");
    }

    @Operation(summary = "启用/禁用用户")
    @PutMapping("/{id}/status")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<Void> toggleStatus(@PathVariable Long id, @RequestParam Integer status) {
        iUserService.toggleUserStatus(id, status);
        return Result.success(status == 1 ? "用户已启用" : "用户已禁用");
    }

    @Operation(
        summary = "获取当前用户信息",
        description = "获取当前登录用户的基本信息，需要从请求头携带 Token"
    )
    @GetMapping("/me")
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public Result<LoginVO.UserInfo> currentUser(Principal principal) {
        return Result.success(iUserService.getCurrentUser(principal));
    }
}
