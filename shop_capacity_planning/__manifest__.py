{
    'name': 'Shop Capacity Planning',
    'version': '19.0.1.0.0',
    'summary': 'Capacity planning for CNC, Edgebanding, Assembly, and Finish Prep workstations',
    'category': 'Manufacturing',
    'author': 'djenkins1027',
    'depends': ['base', 'mail'],
    'data': [
        'security/capacity_security.xml',
        'security/ir.model.access.csv',
        'data/capacity_workstation_data.xml',
        'views/capacity_workstation_views.xml',
        'views/capacity_work_order_views.xml',
        'views/capacity_plan_views.xml',
        'views/capacity_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'shop_capacity_planning/static/src/css/capacity.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
