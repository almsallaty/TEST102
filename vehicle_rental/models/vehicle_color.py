# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class VehicleColor(models.Model):
    _name = 'vehicle.color'
    _description = 'Vehicle Color'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('vehicle_color_name_unique', 'unique(name)', 'Color name must be unique.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._normalize_vals(vals) for vals in vals_list]
        return super().create(vals_list)

    def write(self, vals):
        vals = self._normalize_vals(vals)
        return super().write(vals)

    def _normalize_vals(self, vals):
        vals = dict(vals)
        if vals.get('name'):
            vals['name'] = vals['name'].strip().upper()
        return vals

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not record.name or not record.name.strip():
                raise ValidationError(_('Color name is required.'))
