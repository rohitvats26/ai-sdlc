package com.example.invoiceapp.api;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import com.example.invoiceapp.api.security.RoleInterceptor;
import com.example.invoiceapp.domain.ApprovalService;
import com.example.invoiceapp.domain.InvoiceRepository;

/** Wires the framework-free domain classes into Spring and registers the role check. */
@Configuration
public class AppConfig implements WebMvcConfigurer {

    @Bean
    public ApprovalService approvalService(InvoiceRepository repository) {
        return new ApprovalService(repository);
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new RoleInterceptor()).addPathPatterns("/api/**");
    }
}
