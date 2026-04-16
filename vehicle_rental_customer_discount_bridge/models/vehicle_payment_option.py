# -*- coding: utf-8 -*-
from odoo import fields, models

from odoo.addons.vehicle_rental.utils import _display_rental_notification


class VehiclePaymentOption(models.Model):
    _inherit = 'vehicle.payment.option'

    base_payment_amount = fields.Monetary(string='Gross Payment Amount', currency_field='currency_id')
    discount_amount_applied = fields.Monetary(string='Discount Amount', currency_field='currency_id')

    def _ensure_discount_values_for_invoicing(self):
        self.ensure_one()
        contract = self.vehicle_contract_id
        if not contract or not contract.discount_applied:
            return
        if self.invoice_id:
            return
        if not self.discount_amount_applied and contract.vehicle_payment_option_ids.filtered(lambda p: not p.invoice_id):
            contract._apply_discount_to_existing_uninvoiced_options()
            self.invalidate_recordset(['base_payment_amount', 'discount_amount_applied', 'payment_amount'])

    def action_create_payment_invoice(self):
        for rec in self:
            rec._ensure_discount_values_for_invoicing()
            tax_ids = rec.vehicle_contract_id.tax_ids.ids
            gross_amount = rec.base_payment_amount or rec.payment_amount
            discount_amount = rec.discount_amount_applied or max(gross_amount - rec.payment_amount, 0.0)
            if gross_amount == 0:
                return _display_rental_notification(
                    message="""Please add the proper payment amount""",
                    message_type='warning')

            invoice_lines = [(0, 0, {
                'product_id': rec.invoice_item_id.id,
                'name': rec.name,
                'quantity': 1,
                'price_unit': gross_amount,
                'tax_ids': [(6, 0, tax_ids)],
            })]

            if discount_amount and rec.vehicle_contract_id.discount_product_id:
                invoice_lines.append((0, 0, {
                    'product_id': rec.vehicle_contract_id.discount_product_id.id,
                    'name': rec.vehicle_contract_id.discount_reason or 'Customer Discount',
                    'quantity': 1,
                    'price_unit': -discount_amount,
                    'tax_ids': [(6, 0, tax_ids)],
                }))

            data = {
                'partner_id': rec.vehicle_contract_id.customer_id.id,
                'move_type': 'out_invoice',
                'invoice_date': rec.payment_date,
                'invoice_line_ids': invoice_lines,
                'vehicle_contract_id': rec.vehicle_contract_id.id,
                'vehicle_discount_amount': discount_amount,
                'vehicle_discount_profile_id': rec.vehicle_contract_id.discount_profile_id.id,
            }
            invoice_id = self.env['account.move'].sudo().create(data)
            rec.invoice_id = invoice_id
            return {
                'type': 'ir.actions.act_window',
                'name': self.env._('Invoice'),
                'res_model': 'account.move',
                'res_id': invoice_id.id,
                'view_mode': 'form',
                'target': 'current'
            }
