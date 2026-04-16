# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    vehicle_discount_amount = fields.Monetary(string='Rental Discount Amount', currency_field='currency_id', readonly=True)
    vehicle_discount_profile_id = fields.Many2one('vehicle.customer.discount', string='Rental Discount Profile', readonly=True)
