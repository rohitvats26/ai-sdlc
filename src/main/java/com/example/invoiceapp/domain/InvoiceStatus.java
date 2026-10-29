package com.example.invoiceapp.domain;

import java.util.Optional;

/** Lifecycle: DRAFT -> PENDING_APPROVAL -> APPROVED or REJECTED. */
public enum InvoiceStatus {
    DRAFT("Draft"),
    PENDING_APPROVAL("PendingApproval"),
    APPROVED("Approved"),
    REJECTED("Rejected");

    private final String label;

    InvoiceStatus(String label) {
        this.label = label;
    }

    /** The name used in the JSON API and the UI, for example "PendingApproval". */
    public String label() {
        return label;
    }

    /** Parses a label or enum name, ignoring case, spaces and underscores. */
    public static Optional<InvoiceStatus> parse(String text) {
        if (text == null) {
            return Optional.empty();
        }
        String wanted = normalise(text);
        for (InvoiceStatus status : values()) {
            if (normalise(status.name()).equals(wanted) || normalise(status.label).equals(wanted)) {
                return Optional.of(status);
            }
        }
        return Optional.empty();
    }

    private static String normalise(String value) {
        return value.replace("_", "").replace(" ", "").toLowerCase();
    }
}
