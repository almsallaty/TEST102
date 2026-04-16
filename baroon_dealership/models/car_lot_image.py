from odoo import api, fields, models


class CarLotImage(models.Model):
    _name = 'car.lot.image'
    _description = 'Car Gallery Image'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    lot_id = fields.Many2one('stock.lot', string='Car', required=True, ondelete='cascade', index=True)
    name = fields.Char(required=True, default='Image')
    avatar = fields.Image(required=True)
    image_filename = fields.Char()
    capture_method = fields.Selection([
        ('upload', 'Upload'),
        ('camera', 'Camera'),
    ], default='upload')
    capture_date = fields.Datetime(default=fields.Datetime.now)
    file_size = fields.Integer(string='File Size')
    image_type = fields.Selection([
        ('gallery', 'Gallery'),
        ('front', 'Front'),
        ('rear', 'Rear'),
        ('left', 'Left Side'),
        ('right', 'Right Side'),
        ('interior', 'Interior'),
        ('dashboard', 'Dashboard'),
        ('engine', 'Engine'),
        ('damage', 'Damage'),
        ('document', 'Document'),
        ('other', 'Other'),
    ], default='gallery')
    note = fields.Char()
    company_id = fields.Many2one(related='lot_id.company_id', store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault('capture_date', fields.Datetime.now())
            vals.setdefault('image_type', 'gallery')
            if not vals.get('name'):
                vals['name'] = vals.get('image_filename') or 'Image'
        return super().create(vals_list)
