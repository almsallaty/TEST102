# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _


class RentalCheckListItem(models.Model):
    """Rental CheckList Item"""
    _name = 'rental.checklist.item'
    _description = __doc__
    _order = "sequence"
    _rec_name = 'name'

    sequence = fields.Integer(default=0)
    name = fields.Char(translate=True)
    display_type = fields.Selection(selection=[
        ('line_section', "Section"),
        ('line_note', "Note")],
        default=False)
    vehicle_rental_checklist_id = fields.Many2one(comodel_name='vehicle.rental.checklist', ondelete='cascade')


class VehicleRentalChecklist(models.Model):
    """Vehicle Rental Checklist"""
    _name = 'vehicle.rental.checklist'
    _description = __doc__
    _rec_name = 'name'

    name = fields.Char(translate=True)
    rental_checklist_item_ids = fields.One2many(comodel_name='rental.checklist.item',
                                                inverse_name='vehicle_rental_checklist_id',
                                                string="Checklist Items")

    @api.constrains('rental_checklist_item_ids')
    def _check_rental_checklist_item(self):
        """Check Rental Checklist Items"""
        for record in self:
            if not record.rental_checklist_item_ids:
                raise ValidationError(_("Checklist item is required."))


class RentalContractChecklist(models.Model):
    """Inspection Check list"""
    _name = 'rental.contract.checklist'
    _description = __doc__
    _order = "sequence"
    _rec_name = 'name'

    sequence = fields.Integer()
    name = fields.Char(translate=True)
    display_type = fields.Selection(selection=[
        ('line_section', "Section"),
        ('line_note', "Note")],
        default=False)
    is_checkin_item = fields.Boolean(string="CheckIn Item")
    is_checkout_item = fields.Boolean(string="CheckOut Item")
    vehicle_contract_id = fields.Many2one(comodel_name='vehicle.contract', ondelete='cascade')
