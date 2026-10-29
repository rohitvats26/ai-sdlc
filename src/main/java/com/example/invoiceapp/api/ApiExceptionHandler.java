package com.example.invoiceapp.api;

import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import com.example.invoiceapp.domain.InvalidInvoiceStateException;
import com.example.invoiceapp.domain.InvoiceNotFoundException;

/** Maps domain failures to HTTP status codes with a JSON body { "error": message }. */
@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(InvoiceNotFoundException.class)
    public ResponseEntity<Map<String, String>> notFound(InvoiceNotFoundException ex) {
        return body(HttpStatus.NOT_FOUND, ex.getMessage());
    }

    @ExceptionHandler(InvalidInvoiceStateException.class)
    public ResponseEntity<Map<String, String>> conflict(InvalidInvoiceStateException ex) {
        return body(HttpStatus.CONFLICT, ex.getMessage());
    }

    @ExceptionHandler({IllegalArgumentException.class, HttpMessageNotReadableException.class})
    public ResponseEntity<Map<String, String>> badRequest(Exception ex) {
        return body(HttpStatus.BAD_REQUEST, ex instanceof IllegalArgumentException ? ex.getMessage() : "Malformed request body.");
    }

    private static ResponseEntity<Map<String, String>> body(HttpStatus status, String message) {
        return ResponseEntity.status(status).body(Map.of("error", message));
    }
}
