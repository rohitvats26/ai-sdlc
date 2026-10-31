package com.example.invoiceapp.domain;

import java.util.Locale;

public class Approver {
    private final String username;
    private final ApproverRole role;

    public Approver(String username, ApproverRole role) {
        this.username = username == null ? "" : username.trim();
        this.role = role;
    }

    public String getUsername() {
        return username;
    }

    public ApproverRole getRole() {
        return role;
    }

    public String normalizedUsername() {
        return username.toLowerCase(Locale.ROOT).trim();
    }

    public boolean sameUserAs(Approver other) {
        if (other == null) {
            return false;
        }
        return normalizedUsername().equals(other.normalizedUsername());
    }

}
