package com.company.aiplatform.thirdparty.config;

import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import io.netty.handler.timeout.WriteTimeoutHandler;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.ExchangeFilterFunction;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;
import java.util.concurrent.TimeUnit;

/**
 * AI 服务客户端配置类
 * <p>
 * 负责创建和配置 WebClient，用于与 Python AI 后端服务通信
 * </p>
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
public class AIServiceClientConfig {

    @Value("${ai.backend.url}")
    private String aiBackendUrl;

    @Value("${ai.backend.timeout.connect:5000}")
    private int connectTimeout;

    @Value("${ai.backend.api-key}")
    private String apiKey;

    @Value("${ai.backend.timeout.read:60000}")
    private int readTimeout;

    @Value("${ai.backend.timeout.write:60000}")
    private int writeTimeout;

    /**
     * 创建 WebClient Bean
     * <p>
     * 配置内容包括：
     * <ul>
     *     <li>基础 URL：AI 后端服务地址</li>
     *     <li>超时控制：连接超时、读取超时、写入超时</li>
     *     <li>自动认证：每个请求自动添加 API Key</li>
     *     <li>日志记录：记录请求和响应信息</li>
     * </ul>
     * </p>
     *
     * @return 配置好的 WebClient 实例
     */
    @Bean
    public WebClient aiBackendWebClient() {
        HttpClient httpClient = HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, connectTimeout)
                .doOnConnected(conn -> conn
                        .addHandlerLast(new ReadTimeoutHandler(readTimeout, TimeUnit.MILLISECONDS))
                        .addHandlerLast(new WriteTimeoutHandler(writeTimeout, TimeUnit.MILLISECONDS)))
                .responseTimeout(Duration.ofMillis(readTimeout));

        return WebClient.builder()
                .baseUrl(aiBackendUrl)
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .filter(apiKeyFilter())   // 自动添加 API Key 认证
                .filter(logRequest())     // 记录请求日志
                .filter(logResponse())    // 记录响应日志
                .build();
    }

    /**
     * API Key 认证过滤器
     * <p>
     * 为每个 HTTP 请求自动添加 X-Api-Key 请求头
     * </p>
     *
     * @return 请求处理器过滤器
     */
    private ExchangeFilterFunction apiKeyFilter() {
        return ExchangeFilterFunction.ofRequestProcessor(clientRequest -> {
            return Mono.just(
                    org.springframework.web.reactive.function.client.ClientRequest.from(clientRequest)
                            .header("X-Api-Key", apiKey)
                            .build()
            );
        });
    }

    /**
     * 请求日志过滤器
     * <p>
     * 记录每个 HTTP 请求的方法和 URL
     * </p>
     *
     * @return 请求处理器过滤器
     */
    private ExchangeFilterFunction logRequest() {
        return ExchangeFilterFunction.ofRequestProcessor(clientRequest -> {
            log.info("请求: {} {}", clientRequest.method(), clientRequest.url());
            clientRequest.headers().forEach((name, values) ->
                    values.forEach(value -> log.info("{}: {}", name, value)));
            return Mono.just(clientRequest);
        });
    }

    /**
     * 响应日志过滤器
     * <p>
     * 记录每个 HTTP 响应的状态码，错误响应会记录详细信息
     * </p>
     *
     * @return 响应处理器过滤器
     */
    private ExchangeFilterFunction logResponse() {
        return ExchangeFilterFunction.ofResponseProcessor(clientResponse -> {
            log.info("响应状态: {}", clientResponse.statusCode());
            if (clientResponse.statusCode().isError()) {
                return clientResponse.createException()
                        .flatMap(ex -> {
                            log.error("请求失败: {} {}", clientResponse.statusCode(), ex.getMessage());
                            return Mono.just(clientResponse);
                        });
            }
            return Mono.just(clientResponse);
        });
    }
}
