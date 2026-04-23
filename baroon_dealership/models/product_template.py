from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_car_vehicle = fields.Boolean(
        string='Car Vehicle Product',
        help='Enable VIN-based dealership features for this product model.'
    )
    brand = fields.Char(tracking=True)
    model_name = fields.Char(string='Model', tracking=True)
    trim = fields.Char(tracking=True)
    body_style = fields.Selection([
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('coupe', 'Coupe'),
        ('pickup', 'Pickup'),
        ('hatchback', 'Hatchback'),
        ('wagon', 'Wagon'),
        ('van', 'Van'),
        ('other', 'Other'),
    ], tracking=True)
    seats = fields.Integer()
    doors = fields.Integer()
    drivetrain = fields.Selection([
        ('fwd', 'FWD'),
        ('rwd', 'RWD'),
        ('awd', 'AWD'),
        ('4wd', '4WD'),
        ('other', 'Other'),
    ])
    lot_count = fields.Integer(compute='_compute_car_counts')
    active_car_count = fields.Integer(compute='_compute_car_counts')
    sold_car_count = fields.Integer(compute='_compute_car_counts')

    def _compute_car_counts(self):
        Lot = self.env['stock.lot'].with_context(active_test=False)
        for template in self:
            lots = Lot.search([('product_id', 'in', template.product_variant_ids.ids)])
            template.lot_count = len(lots)
            template.active_car_count = len(lots.filtered(lambda l: l.active and l.car_status not in ('sold', 'delivered')))
            template.sold_car_count = len(lots.filtered(lambda l: (not l.active) or l.car_status in ('sold', 'delivered')))

    @api.constrains('is_car_vehicle', 'tracking')
    def _check_car_tracking(self):
        for template in self:
            if template.is_car_vehicle and template.tracking != 'serial':
                raise ValidationError(_('Car vehicle products must use tracking by unique serial number.'))

    @api.onchange('is_car_vehicle')
    def _onchange_is_car_vehicle(self):
        for template in self:
            if template.is_car_vehicle:
                template.tracking = 'serial'

    def action_view_car_lots(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cars / VINs'),
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('product_id', 'in', self.product_variant_ids.ids)],
            'context': {'search_default_filter_car_vehicle': 1},
            'target': 'current',
        }
