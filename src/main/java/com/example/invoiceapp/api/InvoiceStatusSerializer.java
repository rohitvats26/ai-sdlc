package com.example.invoiceapp.api;

import java.io.IOException;

import org.springframework.boot.jackson.JsonComponent;

import com.example.invoiceapp.domain.InvoiceStatus;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.JsonSerializer;
import com.fasterxml.jackson.databind.SerializerProvider;

/** Writes statuses as "Draft", "PendingApproval", "Approved", "Rejected", which the UI expects. */
@JsonComponent
public class InvoiceStatusSerializer extends JsonSerializer<InvoiceStatus> {
    @Override
    public void serialize(InvoiceStatus value, JsonGenerator generator, SerializerProvider provider) throws IOException {
        generator.writeString(value.label());
    }
}
