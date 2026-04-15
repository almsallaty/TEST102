from odoo import api, fields, models


class CarExpense(models.Model):
    _name = 'car.expense'
    _description = 'Car Expense'
    _order = 'expense_date desc, id desc'

    lot_id = fields.Many2one('stock.lot', string='Car', required=True, ondelete='cascade', index=True)
    name = fields.Char(required=True)
    expense_type = fields.Selection([
        ('shipping', 'Shipping'),
        ('customs', 'Customs'),
        ('reconditioning', 'Reconditioning'),
        ('registration', 'Registration'),
        ('insurance', 'Insurance'),
        ('service', 'Service'),
        ('other', 'Other'),
    ], default='other', required=True, index=True)
    expense_date = fields.Date(default=fields.Date.context_today, required=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    reference = fields.Char()
    amount = fields.Monetary(required=True, currency_field='currency_id')
    currency_id = fields.Many2one(related='lot_id.currency_id', store=True, readonly=True)
    purchase_order_id = fields.Many2one('purchase.order', related='lot_id.purchase_order_id', store=True, readonly=True)
    company_id = fields.Many2one(related='lot_id.company_id', store=True, readonly=True)
    account_move_id = fields.Many2one('account.move', string='Vendor Bill')
    landed_cost_id = fields.Many2one('stock.landed.cost', string='Landed Cost')
    note = fields.Text()

    @api.onchange('expense_type')
    def _onchange_expense_type_name(self):
        labels = dict(self._fields['expense_type'].selection)
        for rec in self:
            if rec.expense_type and not rec.name:
                rec.name = labels.get(rec.expense_type)
