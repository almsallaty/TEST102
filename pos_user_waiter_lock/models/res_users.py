from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    pos_block_quantity_decrease = fields.Boolean(string='Block quantity decrease')
    pos_block_line_remove = fields.Boolean(string='Block removing products from order/table')
    pos_block_cancel_order = fields.Boolean(string='Block cancel whole order')
    pos_block_payment = fields.Boolean(string='Block payment')
    pos_hide_keypad = fields.Boolean(string='Hide backspace key')
