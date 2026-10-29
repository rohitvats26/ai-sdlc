package com.example.invoiceapp.domain;

/** The invoice is not in a state that allows the action. Mapped to HTTP 409. */
public class InvalidInvoiceStateException extends RuntimeException {
    public InvalidInvoiceStateException(String message) {
        super(message);
    }
}
