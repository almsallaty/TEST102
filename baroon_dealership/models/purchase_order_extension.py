from odoo import api, models
from odoo.exceptions import ValidationError


class PurchaseOrderLineBaroonExtension(models.Model):
    _inherit = 'purchase.order.line'

    def _parse_vin_entries(self):
        vins = super()._parse_vin_entries()
        normalized = []
        seen = set()
        for vin in vins:
            cleaned = (vin or '').strip().upper()
            if cleaned:
                if cleaned in seen:
                    raise ValidationError('Duplicate VINs found after normalization: %s' % cleaned)
                seen.add(cleaned)
                normalized.append(cleaned)
        return normalized

    @api.onchange('vin_list')
    def _onchange_vin_list_upper(self):
        for line in self:
            if line.vin_list:
                line.vin_list = '\n'.join([(v or '').strip().upper() for v in line.vin_list.replace(',', '\n').splitlines() if (v or '').strip()])
