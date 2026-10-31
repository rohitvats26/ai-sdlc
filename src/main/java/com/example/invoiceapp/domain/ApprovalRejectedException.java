package com.example.invoiceapp.domain;

public class ApprovalRejectedException extends RuntimeException {
    public ApprovalRejectedException(String message) {
        super(message);
    }
}
