# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vehicle_discount_profile_ids = fields.One2many(
        'vehicle.customer.discount', 'partner_id', string='Vehicle Discount Profiles'
    )
    vehicle_discount_profile_count = fields.Integer(compute='_compute_vehicle_discount_profile_count')

    def _compute_vehicle_discount_profile_count(self):
        for rec in self:
            rec.vehicle_discount_profile_count = len(rec.vehicle_discount_profile_ids)
