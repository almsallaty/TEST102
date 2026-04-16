# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class VehicleCustomerDiscount(models.Model):
    _name = 'vehicle.customer.discount'
    _description = 'Vehicle Customer Discount'
    _order = 'partner_id, sequence, id desc'

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    reason = fields.Text()
    discount_type = fields.Selection([
        ('free_days', 'Free Days'),
        ('fixed_amount', 'Fixed Amount'),
        ('percentage', 'Percentage'),
    ], required=True, default='fixed_amount')
    free_days = fields.Float(default=0.0)
    fixed_amount = fields.Monetary(default=0.0)
    percentage = fields.Float(default=0.0)
    start_date = fields.Date()
    end_date = fields.Date()
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, readonly=True)
    discount_product_id = fields.Many2one(
        'product.product',
        string='Discount Product',
        required=True,
        default=lambda self: self.env.ref(
            'vehicle_rental_customer_discount_bridge.product_vehicle_rental_discount',
            raise_if_not_found=False,
        ),
        domain=[('sale_ok', '=', True)],
        help='Used as the negative line on customer invoices.',
    )

    display_value = fields.Char(compute='_compute_display_value')

    @api.depends('discount_type', 'free_days', 'fixed_amount', 'percentage', 'currency_id')
    def _compute_display_value(self):
        for rec in self:
            if rec.discount_type == 'free_days':
                rec.display_value = _('%s free day(s)') % rec.free_days
            elif rec.discount_type == 'percentage':
                rec.display_value = _('%s %%') % rec.percentage
            else:
                rec.display_value = '%s %s' % (rec.fixed_amount, rec.currency_id.name or '')

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_('End Date must be greater than or equal to Start Date.'))

    @api.constrains('discount_type', 'free_days', 'fixed_amount', 'percentage')
    def _check_amounts(self):
        for rec in self:
            if rec.discount_type == 'free_days' and rec.free_days <= 0:
                raise ValidationError(_('Free Days must be greater than zero.'))
            if rec.discount_type == 'fixed_amount' and rec.fixed_amount <= 0:
                raise ValidationError(_('Fixed Amount must be greater than zero.'))
            if rec.discount_type == 'percentage' and (rec.percentage <= 0 or rec.percentage > 100):
                raise ValidationError(_('Percentage must be greater than zero and at most 100.'))

    def is_valid_for_contract(self, contract):
        self.ensure_one()
        today = contract.start_date.date() if contract.start_date else fields.Date.context_today(contract)
        if self.partner_id != contract.customer_id:
            return False
        if self.company_id != contract.company_id:
            return False
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return self.active
