package com.company.aiplatform.thirdparty.config;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.web.client.RestClient;

import java.time.Duration;

@Configuration
@RequiredArgsConstructor
public class AIServiceClientConfig {

    private final AIServiceProperties properties;

    @Bean
    public RestClient aiServiceRestClient() {
        return RestClient.builder()
                .baseUrl(properties.getUrl())
                .requestInterceptor(apiKeyInterceptor())
                .build();
    }

    /** X-Api-Key 拦截器：每个请求自动带上认证头 */
    private ClientHttpRequestInterceptor apiKeyInterceptor() {
        return (request, body, execution) -> {
            request.getHeaders().set("X-Api-Key", properties.getApiKey());
            return execution.execute(request, body);
        };
    }
}
