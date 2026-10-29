package com.example.invoiceapp.domain;

/** The invoice id does not exist. Mapped to HTTP 404. */
public class InvoiceNotFoundException extends RuntimeException {
    public InvoiceNotFoundException(String message) {
        super(message);
    }
}
