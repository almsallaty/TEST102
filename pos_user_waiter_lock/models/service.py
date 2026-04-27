from odoo import api, models


class PosUserWaiterLockService(models.AbstractModel):
    _name = 'pos.user.waiter.lock.service'
    _description = 'POS User Waiter Lock Service'

    @api.model
    def get_current_permissions(self):
        user = self.env.user.sudo()
        return {
            'block_quantity_decrease': bool(user.pos_block_quantity_decrease),
            'block_line_remove': bool(user.pos_block_line_remove),
            'block_cancel_order': bool(user.pos_block_cancel_order),
            'block_payment': bool(user.pos_block_payment),
            'hide_keypad': bool(user.pos_hide_keypad),
        }
