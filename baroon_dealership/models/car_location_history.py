from odoo import fields, models


class CarLocationHistory(models.Model):
    _name = 'car.location.history'
    _description = 'Car Location History'
    _order = 'movement_date desc, id desc'

    lot_id = fields.Many2one('stock.lot', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='lot_id.company_id', store=True, readonly=True)
    picking_id = fields.Many2one('stock.picking', index=True)
    source_location_id = fields.Many2one('stock.location', string='From', index=True)
    destination_location_id = fields.Many2one('stock.location', string='To', index=True)
    movement_type = fields.Selection([
        ('receipt', 'Receipt'),
        ('internal', 'Internal Transfer'),
        ('delivery', 'Delivery'),
        ('manual', 'Manual Update'),
    ], default='manual', required=True, index=True)
    movement_date = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True)
    note = fields.Text()
