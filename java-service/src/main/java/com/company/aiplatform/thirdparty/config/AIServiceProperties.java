package com.company.aiplatform.thirdparty.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "ai.backend")
public class AIServiceProperties {

    /** Python AI 服务地址 */
    private String url = "http://localhost:8000";

    /** API Key，用于 X-Api-Key 请求头 */
    private String apiKey = "dev-api-key";

    /** 超时配置 */
    private Timeout timeout = new Timeout();

    @Data
    public static class Timeout {
        /** 连接超时（毫秒） */
        private int connect = 5000;
        /** 读取超时（毫秒） */
        private int read = 60000;
        /** 写入超时（毫秒） */
        private int write = 60000;
    }
}
