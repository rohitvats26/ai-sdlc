package com.example.invoiceapp.infra;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;

import org.springframework.stereotype.Repository;

import com.example.invoiceapp.domain.Invoice;
import com.example.invoiceapp.domain.InvoiceRepository;
import com.example.invoiceapp.domain.InvoiceStatus;

/** In-memory store so the demo app runs with no database. Seeded with a few invoices. Returns live instances. */
@Repository
public class InMemoryInvoiceRepository implements InvoiceRepository {

    private final List<Invoice> invoices = new ArrayList<>();
    private int nextNumber = 1006;

    public InMemoryInvoiceRepository() {
        invoices.add(new Invoice("INV-1001", "Lakeside School District", new BigDecimal("4250.00"), InvoiceStatus.PENDING_APPROVAL));
        invoices.add(new Invoice("INV-1002", "Hilltop Academy", new BigDecimal("980.50"), InvoiceStatus.PENDING_APPROVAL));
        Invoice approved = new Invoice("INV-1003", "Riverside Charter", new BigDecimal("12300.00"), InvoiceStatus.APPROVED);
        approved.setDecidedBy("demo.approver");
        approved.setDecidedAt(Instant.now().minus(2, ChronoUnit.DAYS));
        invoices.add(approved);
        invoices.add(new Invoice("INV-1004", "Oakwood Independent", new BigDecimal("615.75"), InvoiceStatus.PENDING_APPROVAL));
        invoices.add(new Invoice("INV-1005", "Maple Grove Prep", new BigDecimal("310.00"), InvoiceStatus.DRAFT));
    }

    @Override
    public synchronized List<Invoice> getAll() {
        return new ArrayList<>(invoices);
    }

    @Override
    public synchronized Optional<Invoice> getById(String id) {
        return invoices.stream().filter(invoice -> invoice.getId().equals(id)).findFirst();
    }

    @Override
    public synchronized List<Invoice> getByIds(Collection<String> ids) {
        Set<String> wanted = Set.copyOf(ids);
        return invoices.stream().filter(invoice -> wanted.contains(invoice.getId())).collect(Collectors.toList());
    }

    @Override
    public synchronized Invoice add(Invoice invoice) {
        if (invoice.getId() == null || invoice.getId().isEmpty()) {
            invoice.setId("INV-" + nextNumber++);
        }
        invoices.add(invoice);
        return invoice;
    }

    @Override
    public synchronized void update(Invoice invoice) {
        for (int i = 0; i < invoices.size(); i++) {
            if (invoices.get(i).getId().equals(invoice.getId())) {
                invoices.set(i, invoice);
                return;
            }
        }
    }

    @Override
    public synchronized boolean remove(String id) {
        return invoices.removeIf(invoice -> invoice.getId().equals(id));
    }
}
