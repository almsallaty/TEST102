{
    "name": "Baroon Dealership",
    "version": "19.0.31.0.0",
    "summary": "Native Odoo VIN-based dealership management",
    "description": """
Baroon Dealership for Odoo 19.

This module turns stock lots / serial numbers into complete car records with:
- VIN-first inventory management
- PO VIN creation and shipment tracking
- native Odoo inventory, graph, pivot, and reporting flows
- car transfer wizard and location history
- car expense tracking and landed cost linkage
- sales reservation / sale / delivery synchronization
- website showroom and portal reservation pages
""",
    "author": "OpenAI",
    "license": "LGPL-3",
    "category": "Sales/Sales",
    "depends": [
        "stock",
        "product",
        "purchase_stock",
        "sale_stock",
        "stock_landed_costs",
        "account",
        "crm",
        "sale_crm",
        "mail",
        "website",
        "portal",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/color_views.xml",
        "views/product_template_views.xml",
        "views/crm_lead_views.xml",
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_landed_cost_views.xml",
        "views/account_move_views.xml",
        "views/car_expense_views.xml",
        "views/car_test_drive_views.xml",
        "views/stock_lot_views.xml",
        "wizards/car_transfer_wizard_views.xml",
        "views/res_config_settings_views.xml",
        "reports/car_reports.xml",
        "views/car_sale_menus.xml",
        "views/website_car_templates.xml",
        "views/portal_templates.xml",
        "views/website_menu.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "baroon_dealership/static/src/js/car_image_gallery_field.js",
            "baroon_dealership/static/src/xml/car_image_gallery_field.xml",
            "baroon_dealership/static/src/scss/car_image_gallery.scss",
            "baroon_dealership/static/src/scss/car_dashboard.scss",
        ],
        "web.assets_frontend": [
            "baroon_dealership/static/src/css/car_sale_website.css",
            "baroon_dealership/static/src/js/car_sale_website.js",
        ],
    },
    "installable": True,
    "application": True,
}