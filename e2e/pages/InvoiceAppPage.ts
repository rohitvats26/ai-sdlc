import { type Locator, type Page } from '@playwright/test';

export class InvoiceAppPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('/');
  }

  async login(username: string, password = 'ChangeMe123!') {
    await this.page.getByLabel('Username').fill(username);
    await this.page.getByLabel('Password').fill(password);
    await this.page.getByRole('button', { name: 'Sign in' }).click();
  }

  async signOut() {
    await this.page.getByRole('button', { name: 'Sign out' }).click();
  }

  async openInvoicesTab() {
    await this.page.getByRole('tab', { name: 'Invoices' }).click();
  }

  async openApprovalsTab() {
    await this.page.getByRole('tab', { name: 'Approvals' }).click();
  }

  async createInvoice(customerName: string, amount: string) {
    await this.page.getByLabel('Customer name').fill(customerName);
    await this.page.getByLabel('Amount').fill(amount);
    await this.page.getByRole('button', { name: 'Create invoice' }).click();
  }

  async submitInvoiceForCustomer(customerName: string) {
    const row = this.invoiceRow(customerName);
    await row.getByRole('button', { name: /Submit invoice .* for approval/ }).click();
  }

  async approveForCustomer(customerName: string) {
    await this.openApprovalsTab();
    const listItem = this.page.getByRole('listitem').filter({ hasText: customerName });
    await listItem.getByRole('button', { name: /Approve invoice .+/ }).click();
  }

  invoiceRow(customerName: string): Locator {
    return this.page.getByRole('row').filter({ hasText: customerName });
  }
}
