package com.example.invoiceapp.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.math.BigDecimal;

import org.junit.jupiter.api.Test;

class ApprovalServiceTest {

    private static Invoice invoiceWith(String id, InvoiceStatus status) {
        return new Invoice(id, "Test School", new BigDecimal("100.00"), status);
    }

    private static ApprovalService serviceFor(Invoice... invoices) {
        return new ApprovalService(new FakeInvoiceRepository(invoices));
    }

    @Test
    void submit_movesDraftToPendingApproval() {
        Invoice result = serviceFor(invoiceWith("INV-1", InvoiceStatus.DRAFT)).submit("INV-1");

        assertThat(result.getStatus()).isEqualTo(InvoiceStatus.PENDING_APPROVAL);
    }

    @Test
    void submit_rejectsInvoiceThatIsNotADraft() {
        ApprovalService service = serviceFor(invoiceWith("INV-1", InvoiceStatus.APPROVED));

        assertThatThrownBy(() -> service.submit("INV-1")).isInstanceOf(InvalidInvoiceStateException.class);
    }

    @Test
    void approve_setsStatusApproverAndTimestamp() {
        ApprovalService service = serviceFor(invoiceWith("INV-1", InvoiceStatus.PENDING_APPROVAL));

        Invoice result = service.approve("INV-1", "demo.approver");

        assertThat(result.getStatus()).isEqualTo(InvoiceStatus.APPROVED);
        assertThat(result.getDecidedBy()).isEqualTo("demo.approver");
        assertThat(result.getDecidedAt()).isNotNull();
    }

    @Test
    void approve_rejectsInvoiceThatIsStillADraft() {
        ApprovalService service = serviceFor(invoiceWith("INV-1", InvoiceStatus.DRAFT));

        assertThatThrownBy(() -> service.approve("INV-1", "demo.approver")).isInstanceOf(InvalidInvoiceStateException.class);
    }

    @Test
    void approve_throwsWhenInvoiceDoesNotExist() {
        ApprovalService service = serviceFor();

        assertThatThrownBy(() -> service.approve("INV-404", "demo.approver")).isInstanceOf(InvoiceNotFoundException.class);
    }

    @Test
    void reject_recordsReasonAndApprover() {
        ApprovalService service = serviceFor(invoiceWith("INV-1", InvoiceStatus.PENDING_APPROVAL));

        Invoice result = service.reject("INV-1", "demo.approver", "Duplicate invoice");

        assertThat(result.getStatus()).isEqualTo(InvoiceStatus.REJECTED);
        assertThat(result.getDecisionNote()).isEqualTo("Duplicate invoice");
    }

    @Test
    void reject_requiresAReason() {
        ApprovalService service = serviceFor(invoiceWith("INV-1", InvoiceStatus.PENDING_APPROVAL));

        assertThatThrownBy(() -> service.reject("INV-1", "demo.approver", "  ")).isInstanceOf(IllegalArgumentException.class);
    }
}
