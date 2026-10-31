package com.example.invoiceapp.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import org.junit.jupiter.api.Test;

class ApprovalServiceTest {

    private static Invoice invoiceWith(String id, BigDecimal amount, InvoiceStatus status) {
        return new Invoice(id, "Test School", amount, status);
    }

    private static ApprovalService serviceFor(Invoice... invoices) {
        return new ApprovalService(new FakeInvoiceRepository(invoices));
    }

    private static void assertUnchanged(Invoice before, Invoice after) {
        assertThat(after.getStatus()).isEqualTo(before.getStatus());
        assertThat(after.getAmount()).isEqualByComparingTo(before.getAmount());
        assertThat(after.getDecidedBy()).isEqualTo(before.getDecidedBy());
        assertThat(after.getDecidedAt()).isEqualTo(before.getDecidedAt());
        assertThat(after.getDecisionNote()).isEqualTo(before.getDecisionNote());
        assertThat(after.getApprovals()).isEqualTo(before.getApprovals());
    }

    @Test
    void submit_movesDraftToPendingApproval() {
        Invoice result = serviceFor(invoiceWith("INV-1", new BigDecimal("100.00"), InvoiceStatus.DRAFT)).submit("INV-1");

        assertThat(result.getStatus()).isEqualTo(InvoiceStatus.PENDING_APPROVAL);
    }

    @Test
    void submit_rejectsInvoiceThatIsNotADraft() {
        ApprovalService service = serviceFor(invoiceWith("INV-1", new BigDecimal("100.00"), InvoiceStatus.APPROVED));

        assertThatThrownBy(() -> service.submit("INV-1")).isInstanceOf(InvalidInvoiceStateException.class);
    }

    @Test
    void manager_canApproveAt50000Boundary() {
        ApprovalService service = serviceFor(invoiceWith("INV-1", new BigDecimal("50000.00"), InvoiceStatus.PENDING_APPROVAL));

        Invoice result = service.approve("INV-1", new Approver("demo.manager", ApproverRole.MANAGER));

        assertThat(result.getStatus()).isEqualTo(InvoiceStatus.APPROVED);
        assertThat(result.getDecidedBy()).isEqualTo("demo.manager");
        assertThat(result.getDecidedAt()).isNotNull();
        assertThat(result.getApprovals()).hasSize(1);
    }

    @Test
    void director_canApproveAt500000Boundary() {
        ApprovalService service = serviceFor(invoiceWith("INV-1", new BigDecimal("500000.00"), InvoiceStatus.PENDING_APPROVAL));

        Invoice result = service.approve("INV-1", new Approver("demo.director", ApproverRole.DIRECTOR));

        assertThat(result.getStatus()).isEqualTo(InvoiceStatus.APPROVED);
        assertThat(result.getDecidedBy()).isEqualTo("demo.director");
    }

    @Test
    void manager_rejectedAbove50000WithoutMutation() {
        Invoice invoice = invoiceWith("INV-1", new BigDecimal("50000.01"), InvoiceStatus.PENDING_APPROVAL);
        ApprovalService service = serviceFor(invoice);
        Invoice snapshot = new Invoice("INV-1", invoice.getCustomerName(), invoice.getAmount(), invoice.getStatus());
        snapshot.setDecisionNote(invoice.getDecisionNote());
        snapshot.setDecidedBy(invoice.getDecidedBy());
        snapshot.setDecidedAt(invoice.getDecidedAt());
        snapshot.setApprovals(invoice.getApprovals());

        assertThatThrownBy(() -> service.approve("INV-1", new Approver("demo.manager", ApproverRole.MANAGER)))
                .isInstanceOf(ApprovalRejectedException.class)
                .hasMessageContaining("INV-1")
                .hasMessageContaining("50000")
                .hasMessageContaining("50000.01");
        assertUnchanged(snapshot, invoice);
    }

    @Test
    void manager_rejectedAsFirstApproverAbove500000WithoutMutation() {
        Invoice invoice = invoiceWith("INV-1", new BigDecimal("500000.01"), InvoiceStatus.PENDING_APPROVAL);
        ApprovalService service = serviceFor(invoice);
        Invoice snapshot = new Invoice("INV-1", invoice.getCustomerName(), invoice.getAmount(), invoice.getStatus());
        snapshot.setDecisionNote(invoice.getDecisionNote());
        snapshot.setDecidedBy(invoice.getDecidedBy());
        snapshot.setDecidedAt(invoice.getDecidedAt());
        snapshot.setApprovals(invoice.getApprovals());

        assertThatThrownBy(() -> service.approve("INV-1", new Approver("demo.manager", ApproverRole.MANAGER)))
                .isInstanceOf(ApprovalRejectedException.class)
                .hasMessageContaining("first approver above 500,000 must be a Director");
        assertUnchanged(snapshot, invoice);
    }

    @Test
    void approve_rejectsBlankApproverWithoutMutation() {
        Invoice invoice = invoiceWith("INV-1", new BigDecimal("50000.00"), InvoiceStatus.PENDING_APPROVAL);
        ApprovalService service = serviceFor(invoice);
        Invoice snapshot = new Invoice("INV-1", invoice.getCustomerName(), invoice.getAmount(), invoice.getStatus());
        snapshot.setDecisionNote(invoice.getDecisionNote());
        snapshot.setDecidedBy(invoice.getDecidedBy());
        snapshot.setDecidedAt(invoice.getDecidedAt());
        snapshot.setApprovals(invoice.getApprovals());

        assertThatThrownBy(() -> service.approve("INV-1", new Approver("   ", ApproverRole.MANAGER)))
                .isInstanceOf(ApprovalRejectedException.class)
                .hasMessageContaining("valid approver");
        assertUnchanged(snapshot, invoice);
    }

    @Test
    void approve_rejectsUnknownRoleWithoutMutation() {
        Invoice invoice = invoiceWith("INV-1", new BigDecimal("50000.00"), InvoiceStatus.PENDING_APPROVAL);
        ApprovalService service = serviceFor(invoice);
        Invoice snapshot = new Invoice("INV-1", invoice.getCustomerName(), invoice.getAmount(), invoice.getStatus());
        snapshot.setDecisionNote(invoice.getDecisionNote());
        snapshot.setDecidedBy(invoice.getDecidedBy());
        snapshot.setDecidedAt(invoice.getDecidedAt());
        snapshot.setApprovals(invoice.getApprovals());

        assertThatThrownBy(() -> service.approve("INV-1", new Approver("demo.manager", null)))
                .isInstanceOf(ApprovalRejectedException.class)
                .hasMessageContaining("Unknown approver role");
        assertUnchanged(snapshot, invoice);
    }

    @Test
    void approve_rejectsInvalidAmountWithoutMutation() {
        Invoice invoice = invoiceWith("INV-1", new BigDecimal("0.00"), InvoiceStatus.PENDING_APPROVAL);
        ApprovalService service = serviceFor(invoice);
        Invoice snapshot = new Invoice("INV-1", invoice.getCustomerName(), invoice.getAmount(), invoice.getStatus());
        snapshot.setDecisionNote(invoice.getDecisionNote());
        snapshot.setDecidedBy(invoice.getDecidedBy());
        snapshot.setDecidedAt(invoice.getDecidedAt());
        snapshot.setApprovals(invoice.getApprovals());

        assertThatThrownBy(() -> service.approve("INV-1", new Approver("demo.director", ApproverRole.DIRECTOR)))
                .isInstanceOf(ApprovalRejectedException.class)
                .hasMessageContaining("invalid amount");
        assertUnchanged(snapshot, invoice);
    }

    @Test
    void approve_rejectsInvoiceThatIsStillADraft() {
        ApprovalService service = serviceFor(invoiceWith("INV-1", new BigDecimal("100.00"), InvoiceStatus.DRAFT));

        assertThatThrownBy(() -> service.approve("INV-1", new Approver("demo.manager", ApproverRole.MANAGER)))
                .isInstanceOf(InvalidInvoiceStateException.class);
    }

    @Test
    void approve_throwsWhenInvoiceDoesNotExist() {
        ApprovalService service = serviceFor();

        assertThatThrownBy(() -> service.approve("INV-404", new Approver("demo.manager", ApproverRole.MANAGER)))
                .isInstanceOf(InvoiceNotFoundException.class);
    }

    @Test
    void reject_recordsReasonAndApprover() {
        ApprovalService service = serviceFor(invoiceWith("INV-1", new BigDecimal("100.00"), InvoiceStatus.PENDING_APPROVAL));

        Invoice result = service.reject("INV-1", "demo.manager", "Duplicate invoice");

        assertThat(result.getStatus()).isEqualTo(InvoiceStatus.REJECTED);
        assertThat(result.getDecisionNote()).isEqualTo("Duplicate invoice");
    }

    @Test
    void reject_requiresAReason() {
        ApprovalService service = serviceFor(invoiceWith("INV-1", new BigDecimal("100.00"), InvoiceStatus.PENDING_APPROVAL));

        assertThatThrownBy(() -> service.reject("INV-1", "demo.manager", "  ")).isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void firstApprovalAbove500000_keepsInvoicePending() {
        Invoice invoice = invoiceWith("INV-1", new BigDecimal("600000.00"), InvoiceStatus.PENDING_APPROVAL);
        ApprovalService service = serviceFor(invoice);

        Invoice result = service.approve("INV-1", new Approver("demo.director", ApproverRole.DIRECTOR));

        assertThat(result.getStatus()).isEqualTo(InvoiceStatus.PENDING_APPROVAL);
        assertThat(result.getDecidedBy()).isNull();
        assertThat(result.getDecidedAt()).isNull();
        assertThat(result.getApprovals()).hasSize(1);
    }

    @Test
    void secondDirectorCompletesApprovalAbove500000() {
        Invoice invoice = invoiceWith("INV-1", new BigDecimal("600000.00"), InvoiceStatus.PENDING_APPROVAL);
        ApprovalService service = serviceFor(invoice);
        service.approve("INV-1", new Approver("demo.director", ApproverRole.DIRECTOR));

        Invoice result = service.approve("INV-1", new Approver("demo.director2", ApproverRole.DIRECTOR));

        assertThat(result.getStatus()).isEqualTo(InvoiceStatus.APPROVED);
        assertThat(result.getDecidedBy()).isEqualTo("demo.director2");
        assertThat(result.getDecidedAt()).isNotNull();
        assertThat(result.getApprovals()).hasSize(2);
    }

    @Test
    void managerCannotBeSecondApproverAbove500000() {
        Invoice invoice = invoiceWith("INV-1", new BigDecimal("600000.00"), InvoiceStatus.PENDING_APPROVAL);
        ApprovalService service = serviceFor(invoice);
        service.approve("INV-1", new Approver("demo.director", ApproverRole.DIRECTOR));
        Invoice snapshot = new Invoice("INV-1", invoice.getCustomerName(), invoice.getAmount(), invoice.getStatus());
        snapshot.setDecisionNote(invoice.getDecisionNote());
        snapshot.setDecidedBy(invoice.getDecidedBy());
        snapshot.setDecidedAt(invoice.getDecidedAt());
        snapshot.setApprovals(invoice.getApprovals());

        assertThatThrownBy(() -> service.approve("INV-1", new Approver("demo.manager", ApproverRole.MANAGER)))
                .isInstanceOf(ApprovalRejectedException.class)
                .hasMessageContaining("second approver must be a Director");
        assertUnchanged(snapshot, invoice);
    }

    @Test
    void sameUserCannotCountTwiceAbove500000() {
        Invoice invoice = invoiceWith("INV-1", new BigDecimal("600000.00"), InvoiceStatus.PENDING_APPROVAL);
        ApprovalService service = serviceFor(invoice);
        service.approve("INV-1", new Approver("  demo.director  ", ApproverRole.DIRECTOR));
        Invoice snapshot = new Invoice("INV-1", invoice.getCustomerName(), invoice.getAmount(), invoice.getStatus());
        snapshot.setDecisionNote(invoice.getDecisionNote());
        snapshot.setDecidedBy(invoice.getDecidedBy());
        snapshot.setDecidedAt(invoice.getDecidedAt());
        snapshot.setApprovals(invoice.getApprovals());

        assertThatThrownBy(() -> service.approve("INV-1", new Approver("Demo.Director", ApproverRole.DIRECTOR)))
                .isInstanceOf(ApprovalRejectedException.class)
                .hasMessageContaining("Same approver cannot count twice");
        assertUnchanged(snapshot, invoice);
    }

    @Test
    void concurrent_sameUserApproval_isRecordedOnce() throws Exception {
        Invoice invoice = invoiceWith("INV-1", new BigDecimal("600000.00"), InvoiceStatus.PENDING_APPROVAL);
        ApprovalService service = serviceFor(invoice);
        ExecutorService executor = Executors.newFixedThreadPool(2);
        CountDownLatch ready = new CountDownLatch(2);
        CountDownLatch start = new CountDownLatch(1);
        List<Throwable> failures = new ArrayList<>();

        for (int i = 0; i < 2; i++) {
            executor.submit(() -> {
                ready.countDown();
                try {
                    start.await();
                    service.approve("INV-1", new Approver(" demo.director ", ApproverRole.DIRECTOR));
                } catch (Throwable ex) {
                    failures.add(ex);
                }
            });
        }

        ready.await();
        start.countDown();
        executor.shutdown();
        assertThat(executor.awaitTermination(5, TimeUnit.SECONDS)).isTrue();
        assertThat(invoice.getApprovals()).hasSize(1);
        assertThat(invoice.getStatus()).isEqualTo(InvoiceStatus.PENDING_APPROVAL);
        assertThat(failures).hasSize(1);
    }
}
