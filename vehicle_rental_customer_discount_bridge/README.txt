Vehicle Rental Customer Discount Bridge for Odoo 19

What it adds:
- Customer discount profiles on contacts
- Discount types: Free Days, Fixed Amount, Percentage
- Apply/Clear Discount buttons on rental contract
- Discount-aware installment generation
- Accounting visibility through negative discount invoice lines

Important notes:
- Free Days is designed for contracts with Rent Type = Days.
- If installments already exist and are not invoiced yet, applying/clearing a discount rebuilds those installments.
- Existing posted invoices are not changed automatically.

Suggested test flow:
1. Install module.
2. Open a customer and create a Rental Discount profile.
3. Create a vehicle contract for that customer.
4. Select the discount profile and click Apply Discount.
5. Create installments.
6. Open a payment option and create invoice.
7. Confirm that the invoice contains:
   - main rental line
   - negative Rental Discount line
