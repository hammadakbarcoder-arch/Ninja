# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class DashboardNinjaController(http.Controller):

    @http.route('/dashboard_ninja_ai/get_data', type='jsonrpc', auth='user')
    def get_dashboard_data(self, board_id=None):
        """Fetch dashboard board and item data."""
        board_obj = request.env['dashboard.ninja.board']
        if board_id:
            board = board_obj.browse(board_id)
        else:
            board = board_obj.search([], limit=1)
            if not board:
                # Create a sample starter board if none exists
                board = board_obj.create({
                    'name': 'Ninja Executive Command Center',
                })
                # Add default sample items if sale/crm/res.partner exist
                partner_model = request.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
                user_model = request.env['ir.model'].search([('model', '=', 'res.users')], limit=1)
                if partner_model:
                    request.env['dashboard.ninja.item'].create({
                        'name': 'Total Active Customers',
                        'board_id': board.id,
                        'item_type': 'kpi',
                        'model_id': partner_model.id,
                        'aggregate_func': 'count',
                        'theme_color': 'neon_blue',
                    })
                if user_model:
                    request.env['dashboard.ninja.item'].create({
                        'name': 'System Users',
                        'board_id': board.id,
                        'item_type': 'kpi',
                        'model_id': user_model.id,
                        'aggregate_func': 'count',
                        'theme_color': 'neon_green',
                    })

        return board.get_dashboard_data()

    @http.route('/dashboard_ninja_ai/ask_ai', type='jsonrpc', auth='user')
    def ask_ai(self, board_id, prompt=None):
        """Invoke AI Copilot for insights."""
        service = request.env['dashboard.ninja.ai.service']
        return service.ask_ai_insights(board_id, user_prompt=prompt)
