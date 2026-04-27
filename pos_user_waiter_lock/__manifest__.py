{
    'name': 'POS User Waiter Lock',
    'version': '19.0.1.0.6',
    'category': 'Point of Sale',
    'summary': 'Per-user POS restrictions for quantity decrease, line remove, cancel order, payment, and keypad.',
    'author': 'OpenAI',
    'depends': ['point_of_sale'],
    'data': [
        'views/res_users_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_user_waiter_lock/static/src/js/restricted_waiter_actions.js',
            'pos_user_waiter_lock/static/src/css/restricted_waiter_actions.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
