package com.example.invoiceapp.api.security;

import java.io.IOException;

import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

/** Requires a valid bearer token on every /api call except sign-in. */
@Component
public class SessionAuthFilter extends OncePerRequestFilter {

    public static final String SESSION_ATTRIBUTE = "session";
    private static final String BEARER_PREFIX = "Bearer ";

    private final SessionStore sessions;

    public SessionAuthFilter(SessionStore sessions) {
        this.sessions = sessions;
    }

    /** The signed-in user for this request. Only valid inside /api calls that passed the filter. */
    public static UserSession sessionOf(HttpServletRequest request) {
        return (UserSession) request.getAttribute(SESSION_ATTRIBUTE);
    }

    public static String tokenOf(HttpServletRequest request) {
        String header = request.getHeader("Authorization");
        return header != null && header.startsWith(BEARER_PREFIX) ? header.substring(BEARER_PREFIX.length()) : null;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return !path.startsWith("/api") || path.equals("/api/auth/login");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        UserSession session = sessions.get(tokenOf(request));

        if (session == null) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            return;
        }

        request.setAttribute(SESSION_ATTRIBUTE, session);
        chain.doFilter(request, response);
    }
}
