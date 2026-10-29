package com.example.invoiceapp.domain;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Optional;

/** Simple list-backed repository for unit tests. Returns live instances, like the real in-memory one. */
class FakeInvoiceRepository implements InvoiceRepository {
    private final List<Invoice> invoices = new ArrayList<>();

    FakeInvoiceRepository(Invoice... seed) {
        invoices.addAll(List.of(seed));
    }

    @Override
    public List<Invoice> getAll() {
        return new ArrayList<>(invoices);
    }

    @Override
    public Optional<Invoice> getById(String id) {
        return invoices.stream().filter(invoice -> invoice.getId().equals(id)).findFirst();
    }

    @Override
    public List<Invoice> getByIds(Collection<String> ids) {
        return invoices.stream().filter(invoice -> ids.contains(invoice.getId())).toList();
    }

    @Override
    public Invoice add(Invoice invoice) {
        invoices.add(invoice);
        return invoice;
    }

    @Override
    public void update(Invoice invoice) {
        // live instances: nothing to copy
    }

    @Override
    public boolean remove(String id) {
        return invoices.removeIf(invoice -> invoice.getId().equals(id));
    }
}
