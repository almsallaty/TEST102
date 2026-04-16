# -*- coding: utf-8 -*-
# Copyright 2024-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class ResConfigSetting(models.TransientModel):
    """Inherits res.config.settings"""
    _inherit = 'res.config.settings'

    terms_conditions_link = fields.Char(config_parameter='vehicle_rental.terms_conditions_link')
    privacy_policy_link = fields.Char(config_parameter='vehicle_rental.privacy_policy_link')
    pagination_item_per_page = fields.Integer(
        string="Records Per Page",
        config_parameter="vehicle_rental.pagination_item_per_page", default=5)

    salesperson_id = fields.Many2one(comodel_name='res.users', string='Default Salesperson',
                                     domain="[('share', '=', False)]",
                                     config_parameter='vehicle_rental.salesperson_id')

    sale_team_id = fields.Many2one(comodel_name='crm.team', string="Default Sales Team",
                                   config_parameter='vehicle_rental.sale_team_id')

    maintenance_reminder_days = fields.Integer(
        string="Maintenance Reminder Before (Days)", default=5,
        config_parameter="vehicle_rental.maintenance_reminder_days",
        help="Number of days before the upcoming maintenance date to send reminder email.")
