package com.example.invoiceapp.api.security;

import java.util.List;

import org.springframework.boot.context.properties.ConfigurationProperties;

/** Demo accounts from application.yml (prefix "demo"). Local, in-memory app only. */
@ConfigurationProperties(prefix = "demo")
public record DemoProperties(List<DemoUser> users) {

    public record DemoUser(String username, String password, String role) {
    }

    public DemoProperties {
        users = users == null ? List.of() : List.copyOf(users);
    }
}
