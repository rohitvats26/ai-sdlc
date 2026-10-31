import { expect, test } from '@playwright/test';
import { InvoiceAppPage } from '../pages/InvoiceAppPage';

function uniqueCustomer(label: string) {
  return `E2E ${label} ${Date.now()}`;
}

test('refused: manager cannot approve 50,000.01', async ({ page }) => {
  const app = new InvoiceAppPage(page);
  await app.goto();
  await app.login('demo.manager');

  const customer = uniqueCustomer('refused');
  await app.createInvoice(customer, '50000.01');
  await app.submitInvoiceForCustomer(customer);

  await app.openInvoicesTab();
  const invoiceRow = app.invoiceRow(customer);
  await expect(invoiceRow).toContainText('Pending Approval');
  await expect(invoiceRow).toContainText('$50,000.01');
  await expect(invoiceRow).toContainText('0 of 1');

  await app.approveForCustomer(customer);

  const decisionError = page.getByRole('alert');
  await expect(decisionError).toContainText(/exceeds|permission/i);
  await app.openInvoicesTab();
  await expect(invoiceRow).toContainText('Pending Approval');
  await expect(invoiceRow).toContainText('$50,000.01');
  await expect(invoiceRow).toContainText('0 of 1');
});

test('control: director approves the same amount', async ({ page }) => {
  const app = new InvoiceAppPage(page);
  await app.goto();
  await app.login('demo.director');

  const customer = uniqueCustomer('control');
  await app.createInvoice(customer, '50000.01');
  await app.submitInvoiceForCustomer(customer);
  await app.approveForCustomer(customer);
  await app.openInvoicesTab();

  const invoiceRow = app.invoiceRow(customer);
  await expect(invoiceRow).toContainText('Approved');
  await expect(invoiceRow).toContainText('$50,000.01');
  await expect(invoiceRow).toContainText('1 of 1');
});

test('two directors are needed above 500,000', async ({ page }) => {
  const app = new InvoiceAppPage(page);
  await app.goto();
  await app.login('demo.director');

  const customer = uniqueCustomer('large');
  await app.createInvoice(customer, '600000');
  await app.submitInvoiceForCustomer(customer);
  await app.approveForCustomer(customer);
  await app.openInvoicesTab();

  const invoiceRow = app.invoiceRow(customer);
  await expect(invoiceRow).toContainText('1 of 2');

  await app.approveForCustomer(customer);
  await expect(page.getByRole('alert')).toContainText(/same approver|duplicate|different|exceeds|permission/i);
  await app.openInvoicesTab();
  await expect(invoiceRow).toContainText('1 of 2');

  await app.signOut();
  await app.login('demo.director2');
  await app.approveForCustomer(customer);
  await app.openInvoicesTab();

  await expect(invoiceRow).toContainText('Approved');
  await expect(invoiceRow).toContainText('2 of 2');
});
