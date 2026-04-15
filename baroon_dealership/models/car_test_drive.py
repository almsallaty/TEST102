from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CarTestDrive(models.Model):
    _name = "car.test.drive"
    _description = "Car Test Drive"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scheduled_datetime desc, id desc"

    name = fields.Char(default=lambda self: _("New Test Drive"), required=True, tracking=True)
    lot_id = fields.Many2one("stock.lot", string="Car", required=True, ondelete="cascade", tracking=True)
    lead_id = fields.Many2one("crm.lead", string="Opportunity", tracking=True)
    partner_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    salesperson_id = fields.Many2one("res.users", string="Salesperson", default=lambda self: self.env.user, tracking=True)
    scheduled_datetime = fields.Datetime(required=True, default=fields.Datetime.now, tracking=True)
    duration = fields.Float(string="Duration (Hours)", default=1.0)
    state = fields.Selection([
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ], default="draft", tracking=True)
    phone = fields.Char()
    email = fields.Char()
    note = fields.Text()
    company_id = fields.Many2one(related="lot_id.company_id", store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.name == _("New Test Drive"):
                rec.name = _('Test Drive %s') % rec.id
        return records

    @api.constrains("lot_id")
    def _check_lot(self):
        for rec in self:
            if rec.lot_id and not rec.lot_id.is_car_vehicle:
                raise ValidationError(_("Test drives can only be scheduled for car VIN records."))

    def action_confirm(self):
        self.write({"state": "confirmed"})
        return True

    def action_done(self):
        self.write({"state": "done"})
        return True

    def action_cancel(self):
        self.write({"state": "cancelled"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True
