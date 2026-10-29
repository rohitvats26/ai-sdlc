package com.example.invoiceapp.api.security;

import java.security.SecureRandom;
import java.util.HexFormat;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.stereotype.Component;

/** Keeps signed-in sessions in memory, keyed by an opaque bearer token. */
@Component
public class SessionStore {
    private final Map<String, UserSession> sessions = new ConcurrentHashMap<>();
    private final SecureRandom random = new SecureRandom();

    public String create(UserSession session) {
        byte[] bytes = new byte[16];
        random.nextBytes(bytes);
        String token = HexFormat.of().withUpperCase().formatHex(bytes);
        sessions.put(token, session);
        return token;
    }

    public UserSession get(String token) {
        return token == null ? null : sessions.get(token);
    }

    public void remove(String token) {
        sessions.remove(token);
    }
}
