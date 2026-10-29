package com.example.invoiceapp.domain;

import java.time.Instant;

/**
 * Moves an invoice through its lifecycle: DRAFT -> PENDING_APPROVAL -> APPROVED or REJECTED.
 * One invoice at a time, decided as a whole by a single approver.
 */
public class ApprovalService {

    private final InvoiceRepository repository;

    public ApprovalService(InvoiceRepository repository) {
        this.repository = repository;
    }

    public Invoice submit(String invoiceId) {
        Invoice invoice = find(invoiceId);

        if (invoice.getStatus() != InvoiceStatus.DRAFT) {
            throw new InvalidInvoiceStateException(
                    "Invoice %s is %s; only drafts can be submitted.".formatted(invoiceId, invoice.getStatus().label()));
        }

        invoice.setStatus(InvoiceStatus.PENDING_APPROVAL);
        repository.update(invoice);
        return invoice;
    }

    public Invoice approve(String invoiceId, String approver) {
        Invoice invoice = find(invoiceId);
        ensurePending(invoice);

        invoice.setStatus(InvoiceStatus.APPROVED);
        invoice.setDecidedBy(approver);
        invoice.setDecidedAt(Instant.now());
        repository.update(invoice);
        return invoice;
    }

    public Invoice reject(String invoiceId, String approver, String reason) {
        if (reason == null || reason.isBlank()) {
            throw new IllegalArgumentException("A reason is required to reject an invoice.");
        }

        Invoice invoice = find(invoiceId);
        ensurePending(invoice);

        invoice.setStatus(InvoiceStatus.REJECTED);
        invoice.setDecidedBy(approver);
        invoice.setDecidedAt(Instant.now());
        invoice.setDecisionNote(reason);
        repository.update(invoice);
        return invoice;
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
