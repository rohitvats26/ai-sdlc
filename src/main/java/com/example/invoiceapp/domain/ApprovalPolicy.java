package com.example.invoiceapp.domain;

import java.math.BigDecimal;

public final class ApprovalPolicy {
    private static final BigDecimal MANAGER_LIMIT = new BigDecimal("50000");
    private static final BigDecimal DIRECTOR_LIMIT = new BigDecimal("500000");

    private ApprovalPolicy() {
    }

    public static void validate(Invoice invoice, Approver approver) {
        if (invoice == null) {
            throw new ApprovalRejectedException("Invoice is required.");
        }
        if (approver == null || approver.getUsername() == null || approver.getUsername().isBlank()) {
            throw new ApprovalRejectedException("A valid approver is required.");
        }
        if (approver.getRole() == null) {
            throw new ApprovalRejectedException("Unknown approver role for '%s'.".formatted(approver.getUsername()));
        }
        BigDecimal amount = invoice.getAmount();
        if (amount == null || amount.signum() <= 0) {
            throw new ApprovalRejectedException("Invoice %s has an invalid amount: %s.".formatted(invoice.getId(), amount));
        }

        if (amount.compareTo(MANAGER_LIMIT) <= 0) {
            if (approver.getRole() == ApproverRole.MANAGER || approver.getRole() == ApproverRole.DIRECTOR) {
                return;
            }
            throw new ApprovalRejectedException(
                    "Invoice %s amount %s exceeds the %s approval limit for approver role %s."
                            .formatted(invoice.getId(), amount, MANAGER_LIMIT, approver.getRole()));
        }

        if (amount.compareTo(DIRECTOR_LIMIT) <= 0) {
            if (approver.getRole() == ApproverRole.DIRECTOR) {
                return;
            }
            throw new ApprovalRejectedException(
                    "Invoice %s amount %s exceeds the %s approval limit for approver role %s."
                            .formatted(invoice.getId(), amount, MANAGER_LIMIT, approver.getRole()));
        }

        throw new ApprovalRejectedException(
                "Invoice %s amount %s exceeds the 500,000 approval limit for all roles."
                        .formatted(invoice.getId(), amount));
    }
}
