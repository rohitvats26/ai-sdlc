package com.example.invoiceapp.api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

/** Request-to-response check of sign-in, role checks and the JSON shape the UI relies on. */
@SpringBootTest
@AutoConfigureMockMvc
class InvoiceApiTest {

    @Autowired
    private MockMvc mvc;

    private String tokenFor(String username) throws Exception {
        String body = mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"%s\",\"password\":\"ChangeMe123!\"}".formatted(username)))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        return body.replaceAll(".*\"token\":\"([^\"]+)\".*", "$1");
    }

    @Test
    void invoicesNeedSignIn() throws Exception {
        mvc.perform(get("/api/invoices")).andExpect(status().isUnauthorized());
    }

    @Test
    void wrongPasswordIsRefused() throws Exception {
        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"demo.approver\",\"password\":\"nope\"}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void seededPendingInvoiceHasTheStatusNameTheUiExpects() throws Exception {
        mvc.perform(get("/api/invoices/INV-1001").header("Authorization", "Bearer " + tokenFor("demo.approver")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("PendingApproval"))
                .andExpect(jsonPath("$.customerName").value("Lakeside School District"));
    }

    @Test
    void onlyAdminsMayDelete() throws Exception {
        mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete("/api/invoices/INV-1005")
                        .header("Authorization", "Bearer " + tokenFor("demo.approver")))
                .andExpect(status().isForbidden());
    }
}
