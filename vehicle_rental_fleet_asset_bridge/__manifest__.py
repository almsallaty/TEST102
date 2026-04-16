# -*- coding: utf-8 -*-
{
    'name': 'Vehicle Rental Fleet Asset Bridge',
    'summary': 'Safe bridge addon for Fleet, Purchase, and Assets in vehicle rental',
    'version': '19.0.1.1.0',
    'category': 'Fleet',
    'author': 'OpenAI',
    'license': 'LGPL-3',
    'depends': [
        'vehicle_rental',
        'purchase',
        'account_asset',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_vehicle_views.xml',
        'views/account_asset_views.xml',
    ],
    'installable': True,
    'application': False,
}
