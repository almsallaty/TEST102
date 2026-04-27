from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_hr_employee(self):
        result = super()._loader_params_hr_employee()
        fields_list = result.setdefault('search_params', {}).setdefault('fields', [])
        extra_fields = [
            'pos_allow_sent_line_decrease',
            'pos_allow_sent_line_delete',
            'pos_allow_order_delete',
            'pos_allow_payment',
            'pos_show_backspace',
            'pos_manager_override',
        ]
        for field_name in extra_fields:
            if field_name not in fields_list:
                fields_list.append(field_name)
        return result
