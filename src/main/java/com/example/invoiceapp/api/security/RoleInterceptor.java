package com.example.invoiceapp.api.security;

import java.util.Arrays;

import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

/** Enforces @RequireRole on controller methods (method-level wins over class-level). */
public class RoleInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        if (!(handler instanceof HandlerMethod method)) {
            return true;
        }

        RequireRole required = method.getMethodAnnotation(RequireRole.class);
        if (required == null) {
            required = method.getBeanType().getAnnotation(RequireRole.class);
        }
        if (required == null) {
            return true;
        }

        UserSession session = SessionAuthFilter.sessionOf(request);
        if (session == null || !Arrays.asList(required.value()).contains(session.role())) {
            response.setStatus(HttpServletResponse.SC_FORBIDDEN);
            return false;
        }
        return true;
    }
}
