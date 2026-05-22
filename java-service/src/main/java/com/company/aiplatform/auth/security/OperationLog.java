package com.company.aiplatform.auth.security;

import java.lang.annotation.*;

/**
 * 操作日志注解 — 标记需要记录操作日志的方法
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface OperationLog {

    /** 操作类型 */
    String type() default "OTHER";

    /** 操作描述 */
    String value() default "";
}
