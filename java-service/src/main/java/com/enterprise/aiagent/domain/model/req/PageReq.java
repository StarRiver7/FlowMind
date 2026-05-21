package com.enterprise.aiagent.domain.model.req;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Data;

/**
 * 分页请求基类
 */
@Data
public class PageReq {

    @Min(value = 1, message = "页码最小为1")
    private Integer page = 1;

    @Min(value = 1, message = "每页最少1条")
    @Max(value = 500, message = "每页最多500条")
    private Integer pageSize = 20;
}
