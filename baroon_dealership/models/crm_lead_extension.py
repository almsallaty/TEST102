from odoo import _, models
from odoo.exceptions import ValidationError


class CrmLeadDealershipExtension(models.Model):
    _inherit = 'crm.lead'

    def action_create_test_drive(self):
        self.ensure_one()
        if not self.car_lot_id:
            raise ValidationError(_('Select a VIN before creating a test drive.'))
        partner = self._get_or_create_baroon_partner()
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Test Drive'),
            'res_model': 'car.test.drive',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_lot_id': self.car_lot_id.id,
                'default_partner_id': partner.id,
                'default_lead_id': self.id,
                'default_pickup_location_id': self.car_lot_id.current_location_id.id,
                'default_return_location_id': self.car_lot_id.current_location_id.id,
            },
        }
