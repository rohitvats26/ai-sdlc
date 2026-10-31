package com.example.invoiceapp.api;

import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.invoiceapp.api.security.RequireRole;
import com.example.invoiceapp.api.security.SessionAuthFilter;
import com.example.invoiceapp.api.security.UserSession;
import com.example.invoiceapp.domain.ApprovalService;
import com.example.invoiceapp.domain.Approver;
import com.example.invoiceapp.domain.ApproverRole;
import com.example.invoiceapp.domain.Invoice;

import jakarta.servlet.http.HttpServletRequest;

@RestController
@RequestMapping("/api/approvals")
@RequireRole({"Manager", "Director", "Admin"})
public class ApprovalsController {

    public record RejectRequest(String reason) {
    }

    private final ApprovalService approvals;

    public ApprovalsController(ApprovalService approvals) {
        this.approvals = approvals;
    }

    @PostMapping("/{invoiceId}/approve")
    public Invoice approve(@PathVariable String invoiceId, HttpServletRequest request) {
        UserSession session = SessionAuthFilter.sessionOf(request);
        ApproverRole role = ApproverRole.parse(session.role()).orElseThrow(
                () -> new IllegalArgumentException("Unknown approver role '%s'.".formatted(session.role())));
        return approvals.approve(invoiceId, new Approver(session.username(), role));
    }

    @PostMapping("/{invoiceId}/reject")
    public Invoice reject(@PathVariable String invoiceId, @RequestBody RejectRequest body, HttpServletRequest request) {
        UserSession session = SessionAuthFilter.sessionOf(request);
        ApproverRole role = ApproverRole.parse(session.role()).orElseThrow(
                () -> new IllegalArgumentException("Unknown approver role '%s'.".formatted(session.role())));
        return approvals.reject(invoiceId, new Approver(session.username(), role), body.reason());
    }
}
