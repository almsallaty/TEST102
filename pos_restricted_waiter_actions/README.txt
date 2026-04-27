POS Restricted Waiter Actions (Odoo 19)

What this module does:
- Stores POS restriction permissions on hr.employee only.
- Loads those employee fields into POS.
- Blocks or allows protected actions per current cashier/employee.
- Writes audit logs for allowed and denied attempts.

Protected actions:
- Decrease quantity of kitchen-sent lines
- Delete kitchen-sent lines
- Delete whole order
- Open payment screen / validate payment
- Backspace control visibility and use

Notes:
- This module is written from scratch to match the requested behavior and avoid duplicating third-party proprietary code.
- Depending on your exact Odoo 19 enterprise/community POS build and installed restaurant patches, one or two frontend method names may need a tiny adjustment after the first test (for example the exact delete-order hook).
