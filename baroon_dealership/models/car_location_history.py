from odoo import fields, models


class CarLocationHistory(models.Model):
    _name = 'car.location.history'
    _description = 'Car Location History'
    _order = 'move_date desc, id desc'

    lot_id = fields.Many2one('stock.lot', string='Car', required=True, ondelete='cascade', index=True)
    move_date = fields.Datetime(default=fields.Datetime.now, required=True)
    source_location_id = fields.Many2one('stock.location', string='From')
    destination_location_id = fields.Many2one('stock.location', string='To')
    picking_id = fields.Many2one('stock.picking', string='Transfer Document')
    company_id = fields.Many2one(related='lot_id.company_id', store=True, readonly=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Moved By')
    note = fields.Char()
    reference = fields.Char()
