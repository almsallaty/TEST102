from odoo import fields, models


class CarExteriorColor(models.Model):
    _name = 'car.exterior.color'
    _description = 'Car Exterior Color'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    color = fields.Integer(string='Tag Color')

    _sql_constraints = [
        ('car_exterior_color_name_uniq', 'unique(name)', 'Exterior color must be unique.'),
    ]


class CarInteriorColor(models.Model):
    _name = 'car.interior.color'
    _description = 'Car Interior Color'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    color = fields.Integer(string='Tag Color')

    _sql_constraints = [
        ('car_interior_color_name_uniq', 'unique(name)', 'Interior color must be unique.'),
    ]
