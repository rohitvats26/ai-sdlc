package com.example.invoiceapp.domain;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Locale;

/**
 * Moves an invoice through its lifecycle: DRAFT -> PENDING_APPROVAL -> APPROVED or REJECTED.
 * One invoice at a time, decided as a whole by a single approver.
 */
public class ApprovalService {
    private static final BigDecimal DIRECTOR_LIMIT = new BigDecimal("500000");
    private final Object lock = new Object();
    private final InvoiceRepository repository;

    public ApprovalService(InvoiceRepository repository) {
        this.repository = repository;
    }

    public Invoice submit(String invoiceId) {
        synchronized (lock) {
            Invoice invoice = find(invoiceId);

            if (invoice.getStatus() != InvoiceStatus.DRAFT) {
                throw new InvalidInvoiceStateException(
                        "Invoice %s is %s; only drafts can be submitted.".formatted(invoiceId, invoice.getStatus().label()));
            }

            invoice.setStatus(InvoiceStatus.PENDING_APPROVAL);
            repository.update(invoice);
            return invoice;
        }
    }

    public Invoice approve(String invoiceId, Approver approver) {
        synchronized (lock) {
            Invoice invoice = find(invoiceId);
            ensurePending(invoice);
            ensureValidApprover(invoice, approver);

            BigDecimal amount = invoice.getAmount();
            if (amount.compareTo(DIRECTOR_LIMIT) > 0) {
                return approveLargeInvoice(invoice, approver);
            }

            return approveSingleInvoice(invoice, approver);
        }
    }

    public Invoice approve(String invoiceId, String approver) {
        return approve(invoiceId, new Approver(approver, ApproverRole.MANAGER));
    }

    public Invoice reject(String invoiceId, Approver approver, String reason) {
        synchronized (lock) {
            if (reason == null || reason.isBlank()) {
                throw new IllegalArgumentException("A reason is required to reject an invoice.");
            }

            Invoice invoice = find(invoiceId);
            ensurePending(invoice);

            invoice.setStatus(InvoiceStatus.REJECTED);
            invoice.setDecidedBy(approver == null ? "" : approver.getUsername());
            invoice.setDecidedAt(Instant.now());
            invoice.setDecisionNote(reason);
            repository.update(invoice);
            return invoice;
        }
    }

    public Invoice reject(String invoiceId, String approver, String reason) {
        return reject(invoiceId, new Approver(approver, ApproverRole.MANAGER), reason);
    }

    private Invoice approveSingleInvoice(Invoice invoice, Approver approver) {
        ApprovalPolicy.validate(invoice, approver);
        Instant now = Instant.now();
        invoice.setStatus(InvoiceStatus.APPROVED);
        invoice.setDecidedBy(approver.getUsername());
        invoice.setDecidedAt(now);
        invoice.getApprovals().add(new ApprovalRecord(approver.getUsername(), approver.getRole(), now));
        repository.update(invoice);
        return invoice;
    }

    private Invoice approveLargeInvoice(Invoice invoice, Approver approver) {
        requireApproverIdentity(approver);
        List<ApprovalRecord> approvals = invoice.getApprovals();
        if (approvals.isEmpty()) {
            requireDirector(approver, "first approver above 500,000 must be a Director");
            approvals.add(new ApprovalRecord(approver.getUsername(), approver.getRole(), Instant.now()));
            repository.update(invoice);
            return invoice;
        }

        if (approvals.stream().anyMatch(record -> sameUser(record.username(), approver.getUsername()))) {
            throw new ApprovalRejectedException("Same approver cannot count twice for invoice %s.".formatted(invoice.getId()));
        }
        requireDirector(approver, "second approver must be a Director");

        Instant now = Instant.now();
        approvals.add(new ApprovalRecord(approver.getUsername(), approver.getRole(), now));
        invoice.setStatus(InvoiceStatus.APPROVED);
        invoice.setDecidedBy(approver.getUsername());
        invoice.setDecidedAt(now);
        repository.update(invoice);
        return invoice;
    }

    private static void ensureValidApprover(Invoice invoice, Approver approver) {
        if (approver == null || approver.getUsername() == null || approver.getUsername().isBlank()) {
            throw new ApprovalRejectedException("A valid approver is required.");
        }
        if (approver.getRole() == null) {
            throw new ApprovalRejectedException("Unknown approver role for '%s'.".formatted(approver.getUsername()));
        }
        if (invoice.getAmount() == null || invoice.getAmount().signum() <= 0) {
            throw new ApprovalRejectedException("Invoice %s has an invalid amount: %s.".formatted(invoice.getId(), invoice.getAmount()));
        }
    }

    private static void requireApproverIdentity(Approver approver) {
        if (approver == null || approver.getUsername() == null || approver.getUsername().isBlank()) {
            throw new ApprovalRejectedException("A valid approver is required.");
        }
    }

    private static void requireDirector(Approver approver, String message) {
        if (approver.getRole() != ApproverRole.DIRECTOR) {
            throw new ApprovalRejectedException(message + ".");
        }
    }

    private static boolean sameUser(String left, String right) {
        return left != null && right != null && left.trim().toLowerCase(Locale.ROOT).equals(right.trim().toLowerCase(Locale.ROOT));
    }

    private Invoice find(String invoiceId) {
        return repository.getById(invoiceId)
                .orElseThrow(() -> new InvoiceNotFoundException("Invoice %s was not found.".formatted(invoiceId)));
    }

    private static void ensurePending(Invoice invoice) {
        if (invoice.getStatus() != InvoiceStatus.PENDING_APPROVAL) {
            throw new InvalidInvoiceStateException(
                    "Invoice %s is %s; only pending invoices can be decided.".formatted(invoice.getId(), invoice.getStatus().label()));
        }
    }
}
