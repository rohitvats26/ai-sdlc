package com.example.invoiceapp.domain;

import java.util.Collection;
import java.util.List;
import java.util.Optional;

public interface InvoiceRepository {
    List<Invoice> getAll();

    Optional<Invoice> getById(String id);

    List<Invoice> getByIds(Collection<String> ids);

    Invoice add(Invoice invoice);

    void update(Invoice invoice);

    boolean remove(String id);
}
