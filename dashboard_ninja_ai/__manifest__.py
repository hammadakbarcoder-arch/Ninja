# -*- coding: utf-8 -*-
{
    'name': 'Dashboard Ninja with AGI',
    'version': '16.0.1.0.0',
    'category': 'Productivity/Dashboards',
    'summary': 'All-in-One AI Dashboard, Multi-Language AI Report Generator, Excel/PDF Upload & 6+ Chart Types (First 10 Buyers: $149 + FREE Custom Feature | Regular: $210)',
    'description': """
Dashboard Ninja with AI — By Hammad Akbar
=========================================
🔥 SPECIAL LAUNCH OFFER: $149 USD for the First 10 Buyers! (Standard Price: $210 USD after first 10 purchases)
🎁 EXCLUSIVE FIRST 10 BUYERS BONUS: Any Extra Feature or Custom Dashboard Requirement Added 100% FREE!

Transform your Odoo business data into a next-generation autonomous AI command center:
- AI Report Generator (Multi-Language: English, Roman Urdu, Arabic) with Auto-Summary, Analytics Table & Smart Suggestions.
- Data Upload Studio: Upload Excel (.xlsx/.xls), CSV, PDF, or JSON files for instant AI analysis & 1-click chart plotting.
- 1-Click PDF Export & Excel/CSV Export + Voice Command AI & Read-Aloud Speech Synthesis.
- 6 Signature Pastel KPI Cards (with Vs Target progress bars) & 6+ Interactive Chart Types (Bar, Doughnut, Line, Radar, 3D Funnel, Pie).
- Domain-Specific Dashboards (All-in-One, Sales, Finance, CRM, Operations) + 1-Click AI Dashboard Generator.
- 4 Built-in Themes (Pastel Studio, Cyber Dark, Neon Matrix, Midnight Violet), TV/Focus Mode, Chatter Drawer & Direct Mail.
- Seamless compatibility with Odoo 19.0, 18.0, 17.0 & 16.0 (Community & Enterprise editions).
    """,
    'author': 'Hammad Akbar',
    'maintainer': 'Hammad Akbar',
    'website': 'https://apps.odoo.com/apps/modules/browse?author=Hammad%20Akbar',
    'license': 'OPL-1',
    'price': 149.00,
    'currency': 'USD',
    'depends': ['base', 'web', 'mail', 'account'],
    'data': [
        'security/dashboard_ninja_security.xml',
        'security/ir.model.access.csv',
        'views/dashboard_ninja_item_views.xml',
        'views/dashboard_ninja_menus.xml',
    ],
    'demo': [
        'demo/dashboard_ninja_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dashboard_ninja_ai/static/src/scss/dashboard_ninja.scss',
            'dashboard_ninja_ai/static/src/js/dashboard_ninja.js',
            'dashboard_ninja_ai/static/src/xml/dashboard_ninja.xml',
        ],
    },
    'images': ['static/description/banner.gif', 'static/description/banner_v17.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
