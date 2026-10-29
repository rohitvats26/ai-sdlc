package com.example.invoiceapp.api;

import java.math.BigDecimal;
import java.net.URI;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.invoiceapp.api.security.RequireRole;
import com.example.invoiceapp.domain.ApprovalService;
import com.example.invoiceapp.domain.Invoice;
import com.example.invoiceapp.domain.InvoiceRepository;
import com.example.invoiceapp.domain.InvoiceStatus;

@RestController
@RequestMapping("/api/invoices")
public class InvoicesController {

    public record CreateInvoiceRequest(String customerName, BigDecimal amount) {
    }

    private final InvoiceRepository repository;
    private final ApprovalService approvals;

    public InvoicesController(InvoiceRepository repository, ApprovalService approvals) {
        this.repository = repository;
        this.approvals = approvals;
    }

    @GetMapping
    public ResponseEntity<?> getAll(@RequestParam(required = false) String status) {
        List<Invoice> invoices = repository.getAll();

        if (status != null && !status.isEmpty()) {
            Optional<InvoiceStatus> parsed = InvoiceStatus.parse(status);
            if (parsed.isEmpty()) {
                return ResponseEntity.badRequest().body(Map.of("error", "Unknown status '%s'.".formatted(status)));
            }
            invoices = invoices.stream().filter(invoice -> invoice.getStatus() == parsed.get()).toList();
        }

        return ResponseEntity.ok(invoices);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Invoice> getById(@PathVariable String id) {
        return repository.getById(id).map(ResponseEntity::ok).orElseGet(() -> ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<?> create(@RequestBody CreateInvoiceRequest request) {
        if (request.customerName() == null || request.customerName().isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "Customer name is required."));
        }
        if (request.amount() == null || request.amount().signum() <= 0) {
            return ResponseEntity.badRequest().body(Map.of("error", "Amount must be greater than zero."));
        }

        Invoice invoice = new Invoice();
        invoice.setCustomerName(request.customerName().trim());
        invoice.setAmount(request.amount());
        Invoice saved = repository.add(invoice);

        return ResponseEntity.created(URI.create("/api/invoices/" + saved.getId())).body(saved);
    }

    @PostMapping("/{id}/submit")
    public Invoice submit(@PathVariable String id) {
        return approvals.submit(id);
    }

    @DeleteMapping("/{id}")
    @RequireRole("Admin")
    public ResponseEntity<Void> delete(@PathVariable String id) {
        return repository.remove(id) ? ResponseEntity.noContent().build() : ResponseEntity.notFound().build();
    }
}
