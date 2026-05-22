package com.company.aiplatform.common.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum ResultCode {

    SUCCESS(200, "操作成功"),
    BAD_REQUEST(400, "参数校验失败"),
    UNAUTHORIZED(401, "未认证，请先登录"),
    FORBIDDEN(403, "无权限访问"),
    NOT_FOUND(404, "资源不存在"),
    TOO_MANY_REQUESTS(429, "请求频率超限"),
    INTERNAL_ERROR(500, "服务器内部错误"),
    AI_SERVICE_UNAVAILABLE(503, "AI服务暂不可用"),
    BUSINESS_ERROR(1000, "业务处理异常");

    private final int code;
    private final String message;
}
