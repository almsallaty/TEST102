{
    'name': 'Baroon Dealership',
    'version': '19.0.30.0.14',
    'summary': 'Premium VIN-first dealership platform with executive cockpit, luxury vehicle UI, role-based security, CRM, accounting, website and stock flows',
    'description': '''
Baroon Dealership for Odoo 19 by Tag Team Company.

This package includes:
- VIN-first vehicle operations
- Executive dashboard and premium UI assets
- CRM, website, sales, purchase, inventory, landed cost and accounting integration
- Role-based visibility for sales, inventory, accounting and executives
- Printable management and operations reports

This build is prepared as a commercial Tag Team Company module package without company logo branding.
''',
    'author': 'Tag Team Company',
    'license': 'OPL-1',
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
        'security/dealership_groups.xml',
        'security/record_rules.xml',
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
        'views/executive_dashboard_client_views.xml',
        'views/stock_lot_luxury_views.xml',
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
            'baroon_dealership/static/src/scss/dealership_design_system.scss',
            'https://cdn.jsdelivr.net/npm/apexcharts',
            'baroon_dealership/static/src/js/dashboard/dashboard.js',
            'baroon_dealership/static/src/xml/dashboard.xml',
        ],
        'web.assets_frontend': [
            'baroon_dealership/static/src/css/car_sale_website.css',
            'baroon_dealership/static/src/js/car_sale_website.js',
        ],
    },
    'installable': True,
    'application': True,
}
