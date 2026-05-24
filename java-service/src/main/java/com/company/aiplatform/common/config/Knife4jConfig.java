package com.company.aiplatform.common.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Knife4j / Swagger 配置
 * <p>
 * 配置全局 Bearer Token 认证，所有接口默认需要携带 Token
 * </p>
 */
@Configuration
public class Knife4jConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("Enterprise AI Agent Platform API")
                        .version("1.0.0")
                        .description("企业级AI Agent智能办公平台 — Java Core Backend")
                        .contact(new Contact()
                                .name("Enterprise AI Team"))
                        .license(new License()
                                .name("Proprietary")))
                // 全局安全要求：所有接口都需要 Bearer Token
                .addSecurityItem(new SecurityRequirement().addList("BearerAuthentication"))
                .components(new io.swagger.v3.oas.models.Components()
                        .addSecuritySchemes("BearerAuthentication", new SecurityScheme()
                                .name("Authorization")
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")
                                .in(SecurityScheme.In.HEADER)
                                .description("请输入 JWT Token（不包含 'Bearer ' 前缀），例如：eyJhbGciOiJIUzI1NiJ9...")));
    }
}
