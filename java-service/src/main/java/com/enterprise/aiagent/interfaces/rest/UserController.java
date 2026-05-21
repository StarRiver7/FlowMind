package com.enterprise.aiagent.interfaces.rest;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.enterprise.aiagent.application.service.UserService;
import com.enterprise.aiagent.domain.model.req.AssignRoleReq;
import com.enterprise.aiagent.domain.model.vo.LoginVO;
import com.enterprise.aiagent.domain.model.vo.UserVO;
import com.enterprise.aiagent.infrastructure.common.Result;
import com.enterprise.aiagent.infrastructure.security.JwtTokenProvider;
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

    private final UserService userService;
    private final JwtTokenProvider jwtTokenProvider;

    @Operation(summary = "用户列表（分页）")
    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    public Result<IPage<UserVO>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) String keyword) {
        IPage<UserVO> result = userService.listUsers(page, pageSize, keyword);
        return Result.success(result);
    }

    @Operation(summary = "用户详情")
    @GetMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<UserVO> detail(@PathVariable Long id) {
        UserVO vo = userService.getUserDetail(id);
        return Result.success(vo);
    }

    @Operation(summary = "分配角色")
    @PostMapping("/roles")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<Void> assignRoles(@Valid @RequestBody AssignRoleReq req) {
        userService.assignRoles(req);
        return Result.success("角色分配成功");
    }

    @Operation(summary = "启用/禁用用户")
    @PutMapping("/{id}/status")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<Void> toggleStatus(@PathVariable Long id, @RequestParam Integer status) {
        userService.toggleUserStatus(id, status);
        return Result.success(status == 1 ? "用户已启用" : "用户已禁用");
    }

    @Operation(summary = "获取当前用户信息")
    @GetMapping("/me")
    public Result<LoginVO.UserInfo> currentUser(Principal principal) {
        // 从 JWT 返回当前用户基本信息
        return Result.success(LoginVO.UserInfo.builder()
                .username(principal.getName())
                .build());
    }
}
