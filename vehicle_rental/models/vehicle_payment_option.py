# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields
from ..utils import _display_rental_notification


class VehiclePaymentOption(models.Model):
    """Vehicle Payment Option"""
    _name = 'vehicle.payment.option'
    _description = __doc__
    _rec_name = 'name'

    name = fields.Char(string="Name", required=True, translate=True)
    payment_date = fields.Date(string="Payment Date", required=True)
    payment_amount = fields.Monetary(string="Payment Amount")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related="company_id.currency_id")
    invoice_item_id = fields.Many2one('product.product', string="Invoice Item")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    payment_state = fields.Selection(related="invoice_id.payment_state",
                                     string="Payment State")
    vehicle_contract_id = fields.Many2one('vehicle.contract', ondelete='cascade')

    def action_create_payment_invoice(self):
        """Action create payment invoice"""
        tax = []
        invoice_lines = []
        for rec in self.vehicle_contract_id.tax_ids:
            tax.append(rec.id)
        for rec in self:
            if rec.payment_amount == 0:
                message = _display_rental_notification(
                    message="""Please add the proper payment amount""",
                    message_type='warning')
                return message
            payment_details = {
                'product_id': self.invoice_item_id.id,
                'name': self.name,
                'quantity': 1,
                'price_unit': self.payment_amount,
                'tax_ids': tax,
            }
            invoice_lines = [(0, 0, payment_details)]
        data = {
            'partner_id': self.vehicle_contract_id.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.payment_date,
            'invoice_line_ids': invoice_lines,
            'vehicle_contract_id': self.vehicle_contract_id.id
        }
        invoice_id = self.env['account.move'].sudo().create(data)
        self.invoice_id = invoice_id
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
