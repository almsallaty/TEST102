from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    car_lot_id = fields.Many2one(
        'stock.lot',
        string='Selected VIN',
        domain="[('is_car_vehicle', '=', True)]",
        tracking=True,
    )
    car_product_id = fields.Many2one(related='car_lot_id.product_id', string='Car Product', readonly=True)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count')
    test_drive_count = fields.Integer(compute='_compute_test_drive_count')

    def _get_baroon_sale_orders(self):
        self.ensure_one()
        return self.env['sale.order'].search([('opportunity_id', '=', self.id)])

    def _get_baroon_sale_orders_for_recordset(self):
        orders = self.env['sale.order'].search([('opportunity_id', 'in', self.ids)])
        mapping = {lead_id: self.env['sale.order'] for lead_id in self.ids}
        for order in orders:
            mapping[order.opportunity_id.id] |= order
        return mapping

    def _compute_sale_order_count(self):
        mapping = self._get_baroon_sale_orders_for_recordset() if self.ids else {}
        for lead in self:
            lead.sale_order_count = len(mapping.get(lead.id, self.env['sale.order']))

    def _compute_test_drive_count(self):
        data = self.env['car.test.drive'].read_group([('lead_id', 'in', self.ids)], ['lead_id'], ['lead_id']) if self.ids else []
        mapped = {item['lead_id'][0]: item['lead_id_count'] for item in data if item.get('lead_id')}
        for lead in self:
            lead.test_drive_count = mapped.get(lead.id, 0)

    @api.onchange('car_lot_id')
    def _onchange_car_lot_id_baroon(self):
        for lead in self:
            if lead.car_lot_id and not lead.name:
                lead.name = _('Opportunity for %s') % (lead.car_lot_id.display_name_website or lead.car_lot_id.display_name)

    @api.constrains('car_lot_id')
    def _check_selected_car(self):
        for lead in self:
            if lead.car_lot_id and (not lead.car_lot_id.is_car_vehicle or lead.car_lot_id.car_status in ('sold', 'delivered')):
                raise ValidationError(_('Only active car VIN records can be linked to an opportunity.'))

    def _prepare_baroon_partner_vals(self):
        self.ensure_one()
        name = self.partner_name or self.contact_name or self.name or _('Dealership Customer')
        return {
            'name': name,
            'email': self.email_from,
            'phone': self.phone or self.mobile,
            'mobile': self.mobile,
            'street': self.street,
            'street2': self.street2,
            'city': self.city,
            'zip': self.zip,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'company_id': self.company_id.id,
        }

    def _get_or_create_baroon_partner(self):
        self.ensure_one()
        if self.partner_id:
            return self.partner_id
        partner_vals = self._prepare_baroon_partner_vals()
        partner = False
        if self.email_from:
            partner = self.env['res.partner'].search([('email', '=', self.email_from)], limit=1)
        if not partner and (self.phone or self.mobile):
            phone = self.phone or self.mobile
            partner = self.env['res.partner'].search(['|', ('phone', '=', phone), ('mobile', '=', phone)], limit=1)
        if partner:
            partner.write({k: v for k, v in partner_vals.items() if v})
        else:
            partner = self.env['res.partner'].create(partner_vals)
        self.partner_id = partner.id
        return partner

    def action_create_sale_order(self):
        self.ensure_one()
        if not self.car_lot_id:
            raise ValidationError(_('Select a VIN on the opportunity before creating a quotation.'))
        if self.car_lot_id.car_status in ('sold', 'delivered') or not self.car_lot_id.active:
            raise ValidationError(_('The selected VIN is already sold or archived.'))

        existing = self._get_baroon_sale_orders().filtered(
            lambda o: o.state != 'cancel' and o.order_line.filtered(lambda l: l.car_lot_id == self.car_lot_id)
        )
        if existing:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Quotation'),
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': existing[0].id,
            }

        partner = self._get_or_create_baroon_partner()
        lot = self.car_lot_id.with_context(active_test=False)
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'opportunity_id': self.id,
            'origin': self.name,
            'user_id': self.user_id.id or self.env.user.id,
            'note': self.description or False,
        })
        car_title = ' '.join(filter(None, [lot.car_brand, lot.car_model, lot.car_trim])).strip() or lot.product_id.display_name
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': lot.product_id.id,
            'name': _('%s • VIN %s') % (car_title, lot.name or '-'),
            'product_uom_qty': 1.0,
            'price_unit': lot.sale_price or lot.product_id.lst_price,
            'car_lot_id': lot.id,
        })
        self.message_post(body=_('Quotation %s created with VIN %s.') % (order.name, lot.name or lot.display_name))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Quotation'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': order.id,
        }

    def action_view_test_drives(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Test Drives'),
            'res_model': 'car.test.drive',
            'view_mode': 'list,form,calendar',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id, 'default_lot_id': self.car_lot_id.id if self.car_lot_id else False, 'default_partner_id': self.partner_id.id if self.partner_id else False},
        }

    def action_create_test_drive(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Schedule Test Drive'),
            'res_model': 'car.test.drive',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_lot_id': self.car_lot_id.id if self.car_lot_id else False,
                'default_lead_id': self.id,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
                'default_phone': self.phone or self.mobile,
                'default_email': self.email_from,
                'default_note': self.description or False,
            },
        }

    def action_view_sale_orders(self):
        self.ensure_one()
        orders = self._get_baroon_sale_orders()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Orders'),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', orders.ids)],
        }
