# -*- coding: utf-8 -*-
{
    'name': 'Vehicle Rental Car Audit & Reports',
    'summary': 'Audit logs, KPIs, and printable PDF reports for rental vehicles',
    'version': '19.0.2.0.0',
    'category': 'Fleet',
    'author': 'OpenAI',
    'license': 'LGPL-3',
    'depends': [
        'vehicle_rental',
        'maintenance',
        'fleet',
        'mail',
        'hr_expense',
        'account',
        'vehicle_rental_fleet_asset_bridge',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/car_movement_log_views.xml',
        'views/contract_audit_log_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/vehicle_contract_views.xml',
        'report/car_report_templates.xml',
        'report/car_report_actions.xml',
    ],
    'installable': True,
    'application': False,
}
