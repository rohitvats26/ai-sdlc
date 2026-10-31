package com.example.invoiceapp.domain;

import java.util.Locale;
import java.util.Optional;

public enum ApproverRole {
    MANAGER,
    DIRECTOR,
    APPROVER,
    ADMIN;

    public static Optional<ApproverRole> parse(String value) {
        if (value == null || value.isBlank()) {
            return Optional.empty();
        }
        String normalized = value.trim().replace(' ', '_').replace('-', '_').toUpperCase(Locale.ROOT);
        for (ApproverRole role : values()) {
            if (role.name().equals(normalized)) {
                return Optional.of(role);
            }
        }
        return Optional.empty();
    }
}
