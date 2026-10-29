package com.example.invoiceapp.api;

import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.invoiceapp.api.security.DemoProperties;
import com.example.invoiceapp.api.security.SessionAuthFilter;
import com.example.invoiceapp.api.security.SessionStore;
import com.example.invoiceapp.api.security.UserSession;

import jakarta.servlet.http.HttpServletRequest;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    public record LoginRequest(String username, String password) {
    }

    public record LoginResponse(String token, String username, String role) {
    }

    private final DemoProperties demo;
    private final SessionStore sessions;

    public AuthController(DemoProperties demo, SessionStore sessions) {
        this.demo = demo;
        this.sessions = sessions;
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest request) {
        for (DemoProperties.DemoUser user : demo.users()) {
            if (user.username().equals(request.username()) && user.password().equals(request.password())) {
                String token = sessions.create(new UserSession(user.username(), user.role()));
                return ResponseEntity.ok(new LoginResponse(token, user.username(), user.role()));
            }
        }
        return ResponseEntity.status(401).body(Map.of("error", "Invalid username or password."));
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout(HttpServletRequest request) {
        String token = SessionAuthFilter.tokenOf(request);
        if (token != null) {
            sessions.remove(token);
        }
        return ResponseEntity.noContent().build();
    }
}
