from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    pos_allow_sent_line_decrease = fields.Boolean(
        string='Allow Decrease of Sent Kitchen Lines',
        help='If disabled, this waiter cannot reduce the quantity of an order line after it has been sent to the kitchen.',
        default=False,
    )
    pos_allow_sent_line_delete = fields.Boolean(
        string='Allow Delete of Sent Kitchen Lines',
        help='If disabled, this waiter cannot delete an order line after it has been sent to the kitchen.',
        default=False,
    )
    pos_allow_order_delete = fields.Boolean(
        string='Allow Delete Entire POS Order',
        help='If disabled, this waiter cannot delete the whole order from the POS.',
        default=False,
    )
    pos_allow_payment = fields.Boolean(
        string='Allow Payment',
        help='If disabled, this waiter cannot open the payment screen or validate payment from the POS.',
        default=True,
    )
    pos_show_backspace = fields.Boolean(
        string='Show Backspace / Keyboard Controls',
        help='If disabled, the waiter cannot use the backspace related numpad controls in the POS.',
        default=True,
    )
    pos_manager_override = fields.Boolean(
        string='Manager Override Rights',
        help='Reserved flag for future manager override flows.',
        default=False,
    )
