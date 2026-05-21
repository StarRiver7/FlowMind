package com.enterprise.aiagent.infrastructure.common;

import com.enterprise.aiagent.domain.enums.ResultCode;
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;

import java.io.Serializable;

@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Result<T> implements Serializable {

    private int code;
    private String message;
    private T data;
    private long timestamp;
    private String traceId;

    private Result() {
        this.timestamp = System.currentTimeMillis();
    }

    public static <T> Result<T> success() {
        Result<T> r = new Result<>();
        r.code = ResultCode.SUCCESS.getCode();
        r.message = ResultCode.SUCCESS.getMessage();
        return r;
    }

    public static <T> Result<T> success(T data) {
        Result<T> r = success();
        r.data = data;
        return r;
    }


    /**
     * 成功返回 — 仅带消息，无数据体
     */
    public static Result<Void> success(String message) {
        Result<Void> r = new Result<>();
        r.code = ResultCode.SUCCESS.getCode();
        r.message = message;
        return r;
    }

    public static <T> Result<T> success(String message, T data) {
        Result<T> r = success(data);
        r.message = message;
        return r;
    }

    public static <T> Result<T> fail(ResultCode resultCode) {
        Result<T> r = new Result<>();
        r.code = resultCode.getCode();
        r.message = resultCode.getMessage();
        return r;
    }

    public static <T> Result<T> fail(ResultCode resultCode, String message) {
        Result<T> r = fail(resultCode);
        r.message = message;
        return r;
    }

    public static <T> Result<T> fail(int code, String message) {
        Result<T> r = new Result<>();
        r.code = code;
        r.message = message;
        return r;
    }
}
