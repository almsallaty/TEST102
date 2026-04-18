{
    'name': 'Baroon Dealership',
    'version': '19.0.30.0.14',
    'summary': 'VIN-first car dealership with shipment, transfers, costing, CRM, test drives, reports, and native analytics',
    'description': '''
Baroon Dealership for Odoo 19.

Core principles:
- Product = car model
- Serial/Lot = physical car by VIN
- Sell, reserve, test drive, move, and cost the exact VIN
- Keep warehouse movement and receipt validation tied to stock operations
- Native Odoo analytics with graph/pivot/list/kanban views
- Practical PDF reports for operations and management
''',
    'author': 'OpenAI',
    'license': 'LGPL-3',
    'category': 'Sales/Sales',
    'depends': [
        'stock',
        'product',
        'purchase_stock',
        'sale_stock',
        'crm',
        'sale_crm',
        'mail',
        'website',
        'portal',
        'account',
        'stock_landed_costs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/car_reports.xml',
        'views/color_views.xml',
        'views/product_template_views.xml',
        'views/crm_lead_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
        'views/stock_lot_views.xml',
        'views/car_expense_views.xml',
        'views/car_test_drive_views.xml',
        'views/car_analysis_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_landed_cost_views.xml',
        'views/account_move_views.xml',
        'views/dealership_dashboard_views.xml',
        'wizards/car_transfer_wizard_views.xml',
        'views/car_sale_menus.xml',
        'views/website_car_templates.xml',
        'views/portal_templates.xml',
        'views/website_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'baroon_dealership/static/src/js/car_image_gallery_field.js',
            'baroon_dealership/static/src/xml/car_image_gallery_field.xml',
            'baroon_dealership/static/src/scss/car_image_gallery.scss',
            'baroon_dealership/static/src/scss/car_dashboard.scss',
        ],
        'web.assets_frontend': [
            'baroon_dealership/static/src/css/car_sale_website.css',
            'baroon_dealership/static/src/js/car_sale_website.js',
        ],
    },
    'installable': True,
    'application': True,
}
