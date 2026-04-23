from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CarExpense(models.Model):
    _name = 'car.expense'
    _description = 'Car Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expense_date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    lot_id = fields.Many2one('stock.lot', required=True, ondelete='cascade', index=True, tracking=True)
    product_id = fields.Many2one(related='lot_id.product_id', store=True, readonly=True)
    company_id = fields.Many2one(related='lot_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='lot_id.currency_id', readonly=True)
    expense_type = fields.Selection([
        ('shipping', 'Shipping'),
        ('customs', 'Customs'),
        ('insurance', 'Insurance'),
        ('registration', 'Registration'),
        ('reconditioning', 'Reconditioning'),
        ('parts', 'Parts'),
        ('detailing', 'Detailing'),
        ('marketing', 'Marketing'),
        ('fees', 'Fees'),
        ('other', 'Other'),
    ], default='other', required=True, tracking=True)
    expense_date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    amount = fields.Monetary(required=True, tracking=True)
    vendor_id = fields.Many2one('res.partner', tracking=True)
    account_move_id = fields.Many2one('account.move', string='Vendor Bill', tracking=True, copy=False)
    bill_payment_state = fields.Selection(related='account_move_id.payment_state', string='Bill Payment Status', readonly=True)
    landed_cost_id = fields.Many2one('stock.landed.cost', tracking=True)
    purchase_order_id = fields.Many2one(related='lot_id.purchase_order_id', store=True, readonly=True)
    note = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
    ], default='approved', tracking=True)

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount < 0:
                raise ValidationError(_('Expense amount cannot be negative.'))

    def _get_or_create_expense_product(self):
        product = self.env['product.product'].search([('default_code', '=', 'BAROON_CAR_EXPENSE')], limit=1)
        if product:
            return product
        vals = {
            'name': 'Car Extra Cost',
            'default_code': 'BAROON_CAR_EXPENSE',
            'purchase_ok': True,
            'sale_ok': False,
            'list_price': 0.0,
            'standard_price': 0.0,
        }
        if 'type' in self.env['product.template']._fields:
            vals['type'] = 'service'
        elif 'detailed_type' in self.env['product.template']._fields:
            vals['detailed_type'] = 'service'
        tmpl = self.env['product.template'].create(vals)
        return tmpl.product_variant_id

    def action_create_vendor_bill(self):
        self.ensure_one()
        if self.account_move_id:
            return self.action_open_vendor_bill()
        if not self.vendor_id:
            raise ValidationError(_('Select a vendor before creating a vendor bill.'))
        product = self._get_or_create_expense_product()
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.vendor_id.id,
            'invoice_date': self.expense_date or fields.Date.context_today(self),
            'invoice_origin': self.lot_id.name,
            'ref': self.name,
            'car_lot_id': self.lot_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': '%s - %s' % (self.lot_id.name or '', self.name or ''),
                'quantity': 1.0,
                'price_unit': self.amount,
            })],
        })
        self.account_move_id = bill.id
        self.lot_id._compute_dealership_counts()
        self.lot_id._baroon_log_change('expense', description=_('Vendor bill created for expense: %s') % self.name)
        return self.action_open_vendor_bill()

    def action_open_vendor_bill(self):
        self.ensure_one()
        if not self.account_move_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bill'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.account_move_id.id,
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.lot_id._baroon_log_change(
                'expense',
                description=_('Expense added: %s (%s)') % (rec.name, rec.amount),
            )
        return records

    def write(self, vals):
        result = super().write(vals)
        self.mapped('lot_id')._compute_extra_costs()
        self.mapped('lot_id')._compute_profitability()
        self.mapped('lot_id')._compute_dealership_counts()
        return result
