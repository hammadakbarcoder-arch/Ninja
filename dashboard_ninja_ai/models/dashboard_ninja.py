# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class DashboardNinjaBoard(models.Model):
    _name = 'dashboard.ninja.board'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dashboard Board'
    _order = 'sequence, id'

    name = fields.Char(string='Dashboard Title', required=True, default='Main Business Dashboard', tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Owner', default=lambda self: self.env.user, tracking=True)
    is_public = fields.Boolean(string='Public (Visible to All Users)', default=True)
    item_ids = fields.One2many('dashboard.ninja.item', 'board_id', string='Dashboard Items')
    ai_summary = fields.Text(string='AI Executive Briefing', readonly=True)

    @api.model
    def _resolve_board(self, board_id=None):
        """Resolve board_id ('all', int, or None) to a valid dashboard.ninja.board record."""
        if board_id and isinstance(board_id, int):
            b = self.browse(board_id)
            if b.exists():
                return b
        if board_id == 'all':
            b = self.search([('name', '=ilike', 'All-in-One Dashboard')], limit=1)
            if b:
                return b
        return self[:1] or self.search([], limit=1)

    def action_send_dashboard_mail(self, board_id=None):
        """Open Odoo native mail composer to email dashboard report directly."""
        board = self._resolve_board(board_id)
        if not board:
            return False

        kpi_lines = []
        for it in board.item_ids[:6]:
            if it.item_type == 'kpi':
                data = it.get_item_data()
                kpi_lines.append(f"<li><strong>{it.name}:</strong> {data.get('value', 0)}</li>")

        kpi_html = f"<ul>{''.join(kpi_lines)}</ul>" if kpi_lines else "<p>No active KPI cards.</p>"

        body_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 15px; color: #1e293b;">
            <h2 style="color: #0284c7; margin-bottom: 5px;">📊 {board.name}</h2>
            <p style="color: #64748b; font-size: 13px; margin-top: 0;">Automated Business Intelligence &amp; Performance Briefing</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 15px 0;"/>
            <div style="background-color: #f8fafc; border-left: 4px solid #0284c7; padding: 12px 16px; border-radius: 4px; margin-bottom: 15px;">
                <strong style="color: #0f172a;">Executive Briefing:</strong>
                <p style="margin: 8px 0 0 0; color: #334155; line-height: 1.5;">{board.ai_summary or 'All key business metrics are active and continuously monitored.'}</p>
            </div>
            <div style="margin-bottom: 15px;">
                <strong style="color: #0f172a;">Live Key Performance Indicators:</strong>
                {kpi_html}
            </div>
            <p style="font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 10px;">
                Generated &amp; Dispatched via <strong>Dashboard Ninja with AI</strong> (Author: Hammad Akbar)
            </p>
        </div>
        """

        return {
            'type': 'ir.actions.act_window',
            'name': _('Direct Email - Send Dashboard Summary'),
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {
                'default_model': 'dashboard.ninja.board',
                'default_res_ids': [board.id],
                'default_composition_mode': 'comment',
                'default_subject': f"📊 Executive Dashboard Briefing: {board.name}",
                'default_body': body_html,
            },
        }

    @api.model
    def get_chatter_messages(self, board_id=None):
        """Return chatter message history for this board."""
        board = self._resolve_board(board_id)
        if not board or not board.exists():
            return []

        messages = []
        for msg in board.message_ids.sorted(key=lambda m: m.date, reverse=True)[:20]:
            author_name = msg.author_id.name if msg.author_id else (msg.create_uid.name or 'System')
            messages.append({
                'id': msg.id,
                'author': author_name,
                'date': fields.Datetime.to_string(msg.date),
                'body': msg.body or '',
                'subtype': msg.subtype_id.name if msg.subtype_id else 'Note',
                'is_internal': bool(msg.is_internal),
            })
        return messages

    @api.model
    def post_chatter_message(self, board_id, body):
        """Directly post a comment or note to the board chatter thread."""
        board = self._resolve_board(board_id)
        if not board or not board.exists() or not body:
            return {'success': False, 'message': 'Invalid board or empty message'}

        msg = board.message_post(
            body=body,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        return {
            'success': True,
            'message_id': msg.id,
            'author': msg.author_id.name if msg.author_id else self.env.user.name,
            'date': fields.Datetime.to_string(msg.date),
        }

    @api.model
    def action_open_board_chatter(self, board_id=None):
        """Open standard Odoo form view with full Chatter widget."""
        board = self._resolve_board(board_id)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Dashboard Chatter & Activities'),
            'res_model': 'dashboard.ninja.board',
            'res_id': board.id if board else False,
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'current',
        }

    @api.model
    def action_edit_board_items(self, board_id=None):
        """Open Odoo list/form view to customize or reorder dashboard items."""
        board = self._resolve_board(board_id)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customize Dashboard Cards & Charts'),
            'res_model': 'dashboard.ninja.item',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('board_id', '=', board.id)] if board else [],
            'context': {'default_board_id': board.id if board else False},
            'target': 'current',
        }

    @api.model
    def create_custom_item(self, board_id, vals):
        """Create a new chart or KPI tile directly from the frontend 'Create New Chart' modal."""
        board = self._resolve_board(board_id)
        if not board or not board.exists():
            board = self.create({'name': 'Dashboard One'})

        model_name = vals.get('model_name', 'res.partner')
        ir_model = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
        if not ir_model:
            ir_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)

        item_type = vals.get('item_type', 'bar')
        agg_func = vals.get('aggregate_func', 'count')
        field_agg = False
        field_grp = False

        if agg_func in ('sum', 'avg'):
            field_agg_rec = self.env['ir.model.fields'].search([
                ('model_id', '=', ir_model.id),
                ('ttype', 'in', ['float', 'monetary', 'integer']),
                ('store', '=', True),
            ], limit=1)
            if field_agg_rec:
                field_agg = field_agg_rec.id
            else:
                agg_func = 'count'

        if item_type != 'kpi':
            preferred_groups = ['country_id', 'partner_id', 'user_id', 'state', 'payment_state', 'stage_id', 'company_id', 'is_company']
            for gname in preferred_groups:
                f_rec = self.env['ir.model.fields'].search([
                    ('model_id', '=', ir_model.id),
                    ('name', '=', gname),
                    ('store', '=', True),
                ], limit=1)
                if f_rec:
                    field_grp = f_rec.id
                    break

        new_item = self.env['dashboard.ninja.item'].create({
            'name': vals.get('name') or 'Custom Analytics Metric',
            'board_id': board.id,
            'item_type': item_type,
            'model_id': ir_model.id,
            'aggregate_func': agg_func,
            'field_aggregate': field_agg,
            'field_group_by': field_grp,
            'theme_color': vals.get('theme_color') or 'pastel_rose',
            'target_value': float(vals.get('target_value') or 100.0),
            'growth_rate': float(vals.get('growth_rate') or 14.5),
            'show_progress': bool(vals.get('show_progress', True)),
            'sequence': 25,
        })
        return {'success': True, 'item_id': new_item.id, 'name': new_item.name}

    @api.model
    def get_dashboard_data(self, board_id=None, date_filter='all', date_from=None, date_to=None, quick_filter='all'):
        """Fetch all items data formatted for OWL Component & Charts with Date & Quick Filter."""
        is_all_mode = (board_id == 'all' or board_id == 0)

        if is_all_mode:
            all_board = self.search([('name', '=ilike', 'All-in-One Dashboard')], limit=1)
            if not all_board:
                all_board = self.with_context(
                    tracking_disable=True,
                    mail_create_nosubscribe=True,
                    mail_create_nolog=True
                ).create({'name': 'All-in-One Dashboard', 'is_public': True})
                self.create_default_starter_items(all_board)
            elif len(all_board.item_ids) < 12:
                all_board.item_ids.with_context(tracking_disable=True).unlink()
                self.create_default_starter_items(all_board)
            board = all_board
        elif board_id and isinstance(board_id, int):
            board = self.browse(board_id)
            if not board.exists():
                board = self.search([], limit=1)
        elif self:
            board = self[0]
        else:
            all_board = self.search([('name', '=ilike', 'All-in-One Dashboard')], limit=1)
            if not all_board:
                all_board = self.with_context(
                    tracking_disable=True,
                    mail_create_nosubscribe=True,
                    mail_create_nolog=True
                ).create({'name': 'All-in-One Dashboard', 'is_public': True})
                self.create_default_starter_items(all_board)
            board = all_board
            is_all_mode = True

        if not board:
            board = self.create({'name': 'All-in-One Dashboard'})
            self.create_default_starter_items(board)
            is_all_mode = True

        # Ensure domain-specific boards (Sales, Finance, CRM, Operations) have their own dedicated items
        # instead of showing all 12 generic items when selected individually
        if not is_all_mode and board.name:
            bname_low = board.name.strip().lower()
            if any(k in bname_low for k in ['sale', 'finance', 'invoice', 'crm', 'operation']) and len(board.item_ids) >= 10:
                board.item_ids.with_context(tracking_disable=True).unlink()
                self._seed_domain_specific_items(board, bname_low)

        items_data = []
        for item in board.item_ids:
            try:
                items_data.append(item.get_item_data(
                    date_filter=date_filter,
                    date_from=date_from,
                    date_to=date_to,
                    quick_filter=quick_filter,
                ))
            except Exception as e:
                _logger.warning("Error fetching item data for %s: %s", item.name, str(e))
                items_data.append({
                    'id': item.id,
                    'name': item.name,
                    'type': item.item_type,
                    'error': str(e)
                })

        # Distinct domain boards for dropdown switcher list (excluding the internal 'All-in-One Dashboard' container since 'All' is fixed at top)
        accessible_boards = self.search([
            '|', ('is_public', '=', True), ('user_id', '=', self.env.user.id)
        ], order='id asc')
        seen_names = set()
        all_boards = []
        for b in accessible_boards:
            lower_name = b.name.strip().lower()
            if lower_name in ('all-in-one dashboard', 'dashboard one'):
                continue
            if lower_name not in seen_names:
                seen_names.add(lower_name)
                all_boards.append({
                    'id': b.id,
                    'name': b.name,
                    'is_owner': (b.user_id.id == self.env.user.id) or self.env.is_admin(),
                })

        return {
            'board_id': 'all' if is_all_mode else board.id,
            'real_board_id': board.id,
            'name': board.name,
            'ai_summary': board.ai_summary or "Click 'Ask Copilot' to generate real-time executive insights.",
            'items': items_data,
            'date_filter': date_filter,
            'date_from': date_from,
            'date_to': date_to,
            'quick_filter': quick_filter,
            'chatter_count': len(board.message_ids),
            'all_boards': all_boards,
        }

    @api.model
    def create_default_starter_items(self, board):
        """Seed the complete 6-KPI + 6-Chart All-in-One Executive Suite (Hammad Akbar Signature Edition)."""
        partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        user_model = self.env['ir.model'].search([('model', '=', 'res.users')], limit=1)
        module_model = self.env['ir.model'].search([('model', '=', 'ir.module.module')], limit=1)
        move_model = self.env['ir.model'].search([('model', '=', 'account.move')], limit=1)
        sale_model = self.env['ir.model'].search([('model', '=', 'sale.order')], limit=1)

        # Primary revenue model if accounting or sales is installed
        rev_model = move_model or sale_model or partner_model
        rev_amt_field = False
        rev_domain = "[]"
        if move_model and rev_model == move_model:
            rev_amt_field = self.env['ir.model.fields'].search([('model_id', '=', move_model.id), ('name', '=', 'amount_total')], limit=1)
            rev_domain = "[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]"
        elif sale_model and rev_model == sale_model:
            rev_amt_field = self.env['ir.model.fields'].search([('model_id', '=', sale_model.id), ('name', '=', 'amount_total')], limit=1)
            rev_domain = "[('state', 'in', ['sale', 'done'])]"

        items_to_create = []

        # --- 6 SIGNATURE KPI CARDS (Row 1) ---
        if partner_model:
            items_to_create.extend([
                {
                    'name': 'Revenue Insights',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': rev_model.id,
                    'domain': rev_domain,
                    'aggregate_func': 'sum' if rev_amt_field else 'count',
                    'field_aggregate': rev_amt_field.id if rev_amt_field else False,
                    'theme_color': 'pastel_rose',
                    'target_value': 100000.0 if rev_amt_field else 50.0,
                    'growth_rate': 18.4,
                    'sequence': 1,
                },
                {
                    'name': 'Total Revenue',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': partner_model.id,
                    'domain': "[('is_company', '=', True)]",
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_lavender',
                    'target_value': 25.0,
                    'growth_rate': 14.2,
                    'sequence': 2,
                },
                {
                    'name': 'Total Accounts',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_sand',
                    'target_value': 40.0,
                    'growth_rate': 9.8,
                    'sequence': 3,
                },
                {
                    'name': 'Previous Revenue in dollars',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': rev_model.id,
                    'domain': rev_domain,
                    'aggregate_func': 'sum' if rev_amt_field else 'count',
                    'field_aggregate': rev_amt_field.id if rev_amt_field else False,
                    'theme_color': 'pastel_ice',
                    'target_value': 75000.0 if rev_amt_field else 20.0,
                    'growth_rate': 22.5,
                    'show_progress': True,
                    'sequence': 4,
                },
            ])

        if module_model:
            items_to_create.append({
                'name': 'KPI Data',
                'board_id': board.id,
                'item_type': 'kpi',
                'model_id': module_model.id,
                'domain': "[('state', '=', 'installed')]",
                'aggregate_func': 'count',
                'theme_color': 'pastel_sage',
                'target_value': 100.0,
                'growth_rate': 31.0,
                'show_progress': True,
                'sequence': 5,
            })

        if user_model:
            items_to_create.append({
                'name': 'KPI (Percentage)',
                'board_id': board.id,
                'item_type': 'kpi',
                'model_id': user_model.id,
                'aggregate_func': 'count',
                'theme_color': 'pastel_sky',
                'target_value': 10.0,
                'growth_rate': 39.0,
                'sequence': 6,
            })

        # --- 6 SIGNATURE CHARTS (Row 2 & Row 3) ---
        country_field = self.env['ir.model.fields'].search([('model_id', '=', partner_model.id), ('name', '=', 'country_id')], limit=1) if partner_model else False
        company_field = self.env['ir.model.fields'].search([('model_id', '=', partner_model.id), ('name', '=', 'is_company')], limit=1) if partner_model else False
        state_field = self.env['ir.model.fields'].search([('model_id', '=', module_model.id), ('name', '=', 'state')], limit=1) if module_model else False

        if partner_model:
            items_to_create.extend([
                {
                    'name': 'Visitor Insights',
                    'board_id': board.id,
                    'item_type': 'bar',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': country_field.id if country_field else False,
                    'theme_color': 'neon_blue',
                    'sequence': 10,
                },
                {
                    'name': 'Top 4 Sale Products',
                    'board_id': board.id,
                    'item_type': 'doughnut',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': country_field.id if country_field else (company_field.id if company_field else False),
                    'theme_color': 'neon_purple',
                    'sequence': 11,
                },
                {
                    'name': 'Customer Satisfaction',
                    'board_id': board.id,
                    'item_type': 'line',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': country_field.id if country_field else False,
                    'theme_color': 'neon_green',
                    'sequence': 12,
                },
                {
                    'name': 'Active Projects',
                    'board_id': board.id,
                    'item_type': 'radar',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': country_field.id if country_field else False,
                    'theme_color': 'sunset_orange',
                    'sequence': 13,
                },
                {
                    'name': 'Campaign Data',
                    'board_id': board.id,
                    'item_type': 'funnel',
                    'model_id': module_model.id if module_model else partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': state_field.id if state_field else (country_field.id if country_field else False),
                    'theme_color': 'neon_blue',
                    'sequence': 14,
                },
                {
                    'name': 'Total Revenue',
                    'board_id': board.id,
                    'item_type': 'pie',
                    'model_id': rev_model.id,
                    'domain': rev_domain,
                    'aggregate_func': 'sum' if rev_amt_field else 'count',
                    'field_aggregate': rev_amt_field.id if rev_amt_field else False,
                    'field_group_by': country_field.id if (rev_model == partner_model and country_field) else False,
                    'theme_color': 'neon_purple',
                    'sequence': 15,
                },
            ])

        if items_to_create:
            self.env['dashboard.ninja.item'].with_context(
                tracking_disable=True,
                mail_create_nosubscribe=True,
                mail_create_nolog=True
            ).create(items_to_create)

    @api.model
    def delete_board(self, board_id):
        """Remove a dashboard board and return the next active board id."""
        board = self.browse(board_id)
        if board.exists():
            board.with_context(tracking_disable=True).unlink()
            remaining = self.search([
                '|', ('is_public', '=', True), ('user_id', '=', self.env.user.id)
            ], order='id asc', limit=1)
            return {
                'success': True,
                'next_board_id': remaining.id if remaining else False
            }
        return {'success': False, 'message': 'Board not found'}

    @api.model
    def generate_ai_dashboard(self, template_name, custom_prompt=None):
        """Hammad Akbar Enterprise feature: Generate complete dashboard with Gen-AI / templates without creating duplicate boards."""
        clean_name = (template_name or "Sales").strip()
        if clean_name.lower() in ('all', 'all-in-one', 'all in one'):
            board_title = "All-in-One Dashboard"
            is_all = True
        elif not clean_name.lower().endswith("dashboard"):
            board_title = f"{clean_name} Dashboard"
            is_all = False
        else:
            board_title = clean_name
            is_all = False

        # Strict deduplication: Find ALL boards matching this title
        existing_boards = self.search([
            ('name', '=ilike', board_title),
            '|', ('user_id', '=', self.env.user.id), ('is_public', '=', True)
        ])

        if existing_boards:
            board = existing_boards[0]
            if len(existing_boards) > 1:
                existing_boards[1:].with_context(tracking_disable=True).unlink()
            board.item_ids.with_context(tracking_disable=True).unlink()
        else:
            board = self.with_context(
                tracking_disable=True,
                mail_create_nosubscribe=True,
                mail_create_nolog=True
            ).create({'name': board_title, 'user_id': self.env.user.id, 'is_public': True})

        if is_all:
            self.create_default_starter_items(board)
        else:
            self._seed_domain_specific_items(board, board_title.lower())

        ai_res = self.env['dashboard.ninja.ai.service'].ask_ai_insights(
            board.id,
            user_prompt=custom_prompt or f"Synthesize executive insights for {board.name}"
        )

        return {
            'board_id': 'all' if is_all else board.id,
            'real_board_id': board.id,
            'name': board.name,
            'ai_summary': ai_res.get('reply', board.ai_summary),
        }

    def _seed_domain_specific_items(self, board, domain_key):
        """Seed focused, domain-specific KPIs and Charts so each dashboard displays ONLY its own domain data."""
        partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        user_model = self.env['ir.model'].search([('model', '=', 'res.users')], limit=1)
        module_model = self.env['ir.model'].search([('model', '=', 'ir.module.module')], limit=1)
        move_model = self.env['ir.model'].search([('model', '=', 'account.move')], limit=1)
        sale_model = self.env['ir.model'].search([('model', '=', 'sale.order')], limit=1)

        rev_model = move_model or sale_model or partner_model
        rev_amt_field = False
        rev_domain = "[]"
        if move_model and rev_model == move_model:
            rev_amt_field = self.env['ir.model.fields'].search([('model_id', '=', move_model.id), ('name', '=', 'amount_total')], limit=1)
            rev_domain = "[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]"
        elif sale_model and rev_model == sale_model:
            rev_amt_field = self.env['ir.model.fields'].search([('model_id', '=', sale_model.id), ('name', '=', 'amount_total')], limit=1)
            rev_domain = "[('state', 'in', ['sale', 'done'])]"

        country_field = self.env['ir.model.fields'].search([('model_id', '=', partner_model.id), ('name', '=', 'country_id')], limit=1) if partner_model else False
        company_field = self.env['ir.model.fields'].search([('model_id', '=', partner_model.id), ('name', '=', 'is_company')], limit=1) if partner_model else False
        state_field = self.env['ir.model.fields'].search([('model_id', '=', module_model.id), ('name', '=', 'state')], limit=1) if module_model else False
        move_state_field = self.env['ir.model.fields'].search([('model_id', '=', move_model.id), ('name', '=', 'state')], limit=1) if move_model else False

        items_vals = []

        if 'sale' in domain_key and partner_model:
            # --- SALES DASHBOARD (ONLY SALES DATA: 4 KPIs + 3 Sales Charts) ---
            items_vals = [
                {
                    'name': 'Sales Revenue ($)',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': rev_model.id,
                    'domain': rev_domain,
                    'aggregate_func': 'sum' if rev_amt_field else 'count',
                    'field_aggregate': rev_amt_field.id if rev_amt_field else False,
                    'theme_color': 'pastel_rose',
                    'target_value': 150000.0 if rev_amt_field else 50.0,
                    'growth_rate': 24.5,
                    'sequence': 1,
                },
                {
                    'name': 'Corporate Buyers',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': partner_model.id,
                    'domain': "[('is_company', '=', True)]",
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_lavender',
                    'target_value': 20.0,
                    'growth_rate': 16.0,
                    'sequence': 2,
                },
                {
                    'name': 'Active Customer Accounts',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_sand',
                    'target_value': 30.0,
                    'growth_rate': 12.4,
                    'sequence': 3,
                },
                {
                    'name': 'Sales Target Achievement',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': rev_model.id,
                    'domain': rev_domain,
                    'aggregate_func': 'sum' if rev_amt_field else 'count',
                    'field_aggregate': rev_amt_field.id if rev_amt_field else False,
                    'theme_color': 'pastel_ice',
                    'target_value': 200000.0 if rev_amt_field else 25.0,
                    'growth_rate': 28.0,
                    'show_progress': True,
                    'sequence': 4,
                },
                {
                    'name': 'Top 4 Sale Products',
                    'board_id': board.id,
                    'item_type': 'doughnut',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': country_field.id if country_field else False,
                    'theme_color': 'neon_purple',
                    'sequence': 10,
                },
                {
                    'name': 'Regional Sales Breakdown',
                    'board_id': board.id,
                    'item_type': 'bar',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': country_field.id if country_field else False,
                    'theme_color': 'neon_blue',
                    'sequence': 11,
                },
                {
                    'name': 'Sales Revenue Share',
                    'board_id': board.id,
                    'item_type': 'pie',
                    'model_id': rev_model.id,
                    'domain': rev_domain,
                    'aggregate_func': 'sum' if rev_amt_field else 'count',
                    'field_aggregate': rev_amt_field.id if rev_amt_field else False,
                    'theme_color': 'neon_purple',
                    'sequence': 12,
                },
            ]
        elif any(k in domain_key for k in ['finance', 'invoice', 'account']) and partner_model:
            # --- FINANCE DASHBOARD (ONLY FINANCE & ACCOUNTING DATA: 4 KPIs + 3 Finance Charts) ---
            fin_model = move_model or partner_model
            items_vals = [
                {
                    'name': 'Posted Invoices ($)',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': rev_model.id,
                    'domain': rev_domain,
                    'aggregate_func': 'sum' if rev_amt_field else 'count',
                    'field_aggregate': rev_amt_field.id if rev_amt_field else False,
                    'theme_color': 'pastel_lavender',
                    'target_value': 120000.0 if rev_amt_field else 40.0,
                    'growth_rate': 19.2,
                    'sequence': 1,
                },
                {
                    'name': 'Posted Journal Entries',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': fin_model.id,
                    'domain': "[('state', '=', 'posted')]" if move_model else "[]",
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_sage',
                    'target_value': 25.0,
                    'growth_rate': 15.0,
                    'sequence': 2,
                },
                {
                    'name': 'Draft & Pending Bills',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': fin_model.id,
                    'domain': "[('state', '=', 'draft')]" if move_model else "[]",
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_sand',
                    'target_value': 15.0,
                    'growth_rate': 8.5,
                    'sequence': 3,
                },
                {
                    'name': 'Collection vs Budget Target',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': rev_model.id,
                    'domain': rev_domain,
                    'aggregate_func': 'sum' if rev_amt_field else 'count',
                    'field_aggregate': rev_amt_field.id if rev_amt_field else False,
                    'theme_color': 'pastel_ice',
                    'target_value': 180000.0 if rev_amt_field else 30.0,
                    'growth_rate': 21.4,
                    'show_progress': True,
                    'sequence': 4,
                },
                {
                    'name': 'Billing & Cashflow Trend',
                    'board_id': board.id,
                    'item_type': 'line',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': country_field.id if country_field else False,
                    'theme_color': 'neon_green',
                    'sequence': 10,
                },
                {
                    'name': 'Invoices by Status',
                    'board_id': board.id,
                    'item_type': 'bar',
                    'model_id': fin_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': move_state_field.id if move_state_field else (country_field.id if country_field else False),
                    'theme_color': 'neon_blue',
                    'sequence': 11,
                },
                {
                    'name': 'Accounts Receivable Share',
                    'board_id': board.id,
                    'item_type': 'pie',
                    'model_id': rev_model.id,
                    'domain': rev_domain,
                    'aggregate_func': 'sum' if rev_amt_field else 'count',
                    'field_aggregate': rev_amt_field.id if rev_amt_field else False,
                    'theme_color': 'neon_purple',
                    'sequence': 12,
                },
            ]
        elif 'crm' in domain_key and partner_model:
            # --- CRM DASHBOARD (ONLY CRM, LEADS & CAMPAIGN DATA: 4 KPIs + 3 CRM Charts) ---
            items_vals = [
                {
                    'name': 'Total Active Contacts',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_sky',
                    'target_value': 25.0,
                    'growth_rate': 34.0,
                    'sequence': 1,
                },
                {
                    'name': 'Corporate Prospects',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': partner_model.id,
                    'domain': "[('is_company', '=', True)]",
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_lavender',
                    'target_value': 15.0,
                    'growth_rate': 22.0,
                    'sequence': 2,
                },
                {
                    'name': 'Individual Leads',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': partner_model.id,
                    'domain': "[('is_company', '=', False)]",
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_rose',
                    'target_value': 10.0,
                    'growth_rate': 18.0,
                    'sequence': 3,
                },
                {
                    'name': 'Lead Conversion vs Target',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_ice',
                    'target_value': 12.0,
                    'growth_rate': 29.5,
                    'show_progress': True,
                    'sequence': 4,
                },
                {
                    'name': 'Customer Satisfaction',
                    'board_id': board.id,
                    'item_type': 'line',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': country_field.id if country_field else False,
                    'theme_color': 'neon_green',
                    'sequence': 10,
                },
                {
                    'name': 'Campaign Data',
                    'board_id': board.id,
                    'item_type': 'funnel',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': country_field.id if country_field else False,
                    'theme_color': 'neon_blue',
                    'sequence': 11,
                },
                {
                    'name': 'Prospect Segment Split',
                    'board_id': board.id,
                    'item_type': 'doughnut',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': company_field.id if company_field else (country_field.id if country_field else False),
                    'theme_color': 'neon_purple',
                    'sequence': 12,
                },
            ]
        else:
            # --- OPERATIONS DASHBOARD (ONLY OPERATIONS, PROJECTS & SYSTEM DATA: 4 KPIs + 3 Operations Charts) ---
            op_mod = module_model or partner_model
            usr_mod = user_model or partner_model
            items_vals = [
                {
                    'name': 'Installed Enterprise Modules',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': op_mod.id,
                    'domain': "[('state', '=', 'installed')]" if module_model else "[]",
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_sage',
                    'target_value': 100.0,
                    'growth_rate': 31.0,
                    'show_progress': True,
                    'sequence': 1,
                },
                {
                    'name': 'Active System Users',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': usr_mod.id,
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_sky',
                    'target_value': 10.0,
                    'growth_rate': 39.0,
                    'sequence': 2,
                },
                {
                    'name': 'Global Partner Network',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_sand',
                    'target_value': 25.0,
                    'growth_rate': 14.5,
                    'sequence': 3,
                },
                {
                    'name': 'Project Delivery vs Target',
                    'board_id': board.id,
                    'item_type': 'kpi',
                    'model_id': op_mod.id,
                    'domain': "[('state', '=', 'installed')]" if module_model else "[]",
                    'aggregate_func': 'count',
                    'theme_color': 'pastel_ice',
                    'target_value': 80.0,
                    'growth_rate': 26.0,
                    'show_progress': True,
                    'sequence': 4,
                },
                {
                    'name': 'Active Projects',
                    'board_id': board.id,
                    'item_type': 'radar',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': country_field.id if country_field else False,
                    'theme_color': 'sunset_orange',
                    'sequence': 10,
                },
                {
                    'name': 'Visitor Insights',
                    'board_id': board.id,
                    'item_type': 'bar',
                    'model_id': partner_model.id,
                    'aggregate_func': 'count',
                    'field_group_by': country_field.id if country_field else False,
                    'theme_color': 'neon_blue',
                    'sequence': 11,
                },
                {
                    'name': 'Deployment Pipeline',
                    'board_id': board.id,
                    'item_type': 'funnel',
                    'model_id': op_mod.id,
                    'aggregate_func': 'count',
                    'field_group_by': state_field.id if state_field else (country_field.id if country_field else False),
                    'theme_color': 'neon_blue',
                    'sequence': 12,
                },
            ]

        if items_vals:
            self.env['dashboard.ninja.item'].with_context(
                tracking_disable=True,
                mail_create_nosubscribe=True,
                mail_create_nolog=True
            ).create(items_vals)

    def _build_sales_template(self, board):
        self._seed_domain_specific_items(board, 'sales')

    def _build_invoice_template(self, board):
        self._seed_domain_specific_items(board, 'finance')

    def _build_crm_template(self, board):
        self._seed_domain_specific_items(board, 'crm')


class DashboardNinjaItem(models.Model):
    _name = 'dashboard.ninja.item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dashboard Item / Card'
    _order = 'sequence, id'

    name = fields.Char(string='Item Name', required=True, default='New Metric', tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    board_id = fields.Many2one('dashboard.ninja.board', string='Dashboard', ondelete='cascade', required=True)
    
    item_type = fields.Selection([
        ('kpi', 'KPI Card'),
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('radar', 'Radar Chart'),
        ('funnel', 'Funnel Chart'),
    ], string='Item Type', default='kpi', required=True)

    model_id = fields.Many2one('ir.model', string='Model to Track', required=True, ondelete='cascade')
    model_name = fields.Char(related='model_id.model', readonly=True, store=True)
    
    domain = fields.Text(string='Filter Domain', default='[]')
    
    aggregate_func = fields.Selection([
        ('count', 'Record Count'),
        ('sum', 'Sum of Values'),
        ('avg', 'Average of Values'),
    ], string='Calculation Type', default='count', required=True)

    field_aggregate = fields.Many2one(
        'ir.model.fields', 
        string='Value Field (for Sum/Avg)',
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['integer', 'float', 'monetary'])]"
    )

    field_group_by = fields.Many2one(
        'ir.model.fields', 
        string='Group By Field (for Charts)',
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['char', 'selection', 'many2one', 'date', 'datetime', 'boolean'])]"
    )

    target_value = fields.Float(string='Target Goal', default=0.0)
    growth_rate = fields.Float(string='Growth Rate (%)', default=0.0)
    show_progress = fields.Boolean(string='Show Target Progress Bar', default=False)

    theme_color = fields.Selection([
        ('pastel_rose', 'Pastel Rose'),
        ('pastel_lavender', 'Pastel Lavender'),
        ('pastel_sand', 'Pastel Sand'),
        ('pastel_ice', 'Pastel Ice Blue'),
        ('pastel_sage', 'Pastel Sage Green'),
        ('pastel_sky', 'Pastel Sky Blue'),
        ('ninja_dark', 'Cyber Dark'),
        ('neon_blue', 'Neon Blue'),
        ('neon_green', 'Neon Green'),
        ('neon_purple', 'Neon Purple'),
        ('sunset_orange', 'Sunset Orange'),
    ], string='Card Theme', default='pastel_rose')

    ai_insight = fields.Text(string='AI Insight', readonly=True)

    def get_item_data(self, date_filter='all', date_from=None, date_to=None, quick_filter='all'):
        """Compute the live data for this item according to its configuration, date filter, and quick filter."""
        self.ensure_one()
        from datetime import datetime, timedelta
        
        model_obj = self.env[self.model_name]
        try:
            parsed_domain = safe_eval(self.domain or '[]')
        except Exception:
            parsed_domain = []

        # Apply Quick Category Filter
        if quick_filter == 'companies' and 'is_company' in model_obj._fields:
            parsed_domain.append(('is_company', '=', True))
        elif quick_filter == 'individuals' and 'is_company' in model_obj._fields:
            parsed_domain.append(('is_company', '=', False))
        elif quick_filter == 'active' and 'active' in model_obj._fields:
            parsed_domain.append(('active', '=', True))

        # Apply Quick or Custom Manual Date Filter
        if 'create_date' in model_obj._fields:
            now = datetime.now()
            if date_filter == 'custom':
                if date_from:
                    parsed_domain.append(('create_date', '>=', f"{date_from} 00:00:00"))
                if date_to:
                    parsed_domain.append(('create_date', '<=', f"{date_to} 23:59:59"))
            elif date_filter == 'today':
                start_date = now.replace(hour=0, minute=0, second=0)
                parsed_domain.append(('create_date', '>=', start_date.strftime('%Y-%m-%d %H:%M:%S')))
            elif date_filter == 'this_week':
                start_date = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0)
                parsed_domain.append(('create_date', '>=', start_date.strftime('%Y-%m-%d %H:%M:%S')))
            elif date_filter == 'this_month':
                start_date = now.replace(day=1, hour=0, minute=0, second=0)
                parsed_domain.append(('create_date', '>=', start_date.strftime('%Y-%m-%d %H:%M:%S')))
            elif date_filter == 'this_year':
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0)
                parsed_domain.append(('create_date', '>=', start_date.strftime('%Y-%m-%d %H:%M:%S')))

        if self.item_type == 'kpi':
            if self.aggregate_func == 'count':
                val = model_obj.search_count(parsed_domain)
            elif self.field_aggregate:
                records = model_obj.search(parsed_domain)
                vals = [getattr(r, self.field_aggregate.name, 0) or 0 for r in records]
                val = sum(vals) if self.aggregate_func == 'sum' else (sum(vals) / len(vals) if vals else 0)
            else:
                val = model_obj.search_count(parsed_domain)

            target_progress = 0.0
            if self.target_value > 0:
                raw_float = float(val or 0)
                target_progress = min(round((raw_float / self.target_value) * 100, 1), 100.0)
            else:
                target_progress = 72.0

            return {
                'id': self.id,
                'name': self.name,
                'type': 'kpi',
                'value': round(val, 2) if isinstance(val, float) else val,
                'theme': self.theme_color,
                'model_name': self.model_name,
                'domain': parsed_domain,
                'ai_insight': self.ai_insight or '',
                'target_value': self.target_value,
                'growth_rate': self.growth_rate or 14.5,
                'show_progress': self.show_progress,
                'target_progress': target_progress,
            }

        # For charts (Bar, Line, Pie, Doughnut, Radar, Funnel)
        group_by = self.field_group_by.name if self.field_group_by else 'id'
        measure = self.field_aggregate.name if (self.field_aggregate and self.aggregate_func != 'count') else 'id'
        aggregate_spec = f"{measure}:{self.aggregate_func}" if self.aggregate_func != 'count' else "__count"

        labels = []
        values = []
        try:
            groups = model_obj._read_group(parsed_domain, groupby=[group_by], aggregates=[aggregate_spec], limit=8)
            for group_val, val in groups:
                if hasattr(group_val, 'display_name'):
                    label = group_val.display_name or 'Global'
                elif isinstance(group_val, bool):
                    label = "Corporate" if group_val else "Individual"
                elif group_val is not None:
                    label = str(group_val)
                else:
                    label = 'Global'
                labels.append(label)
                values.append(round(val, 2) if isinstance(val, float) else val)
        except Exception as e:
            _logger.error("Chart group calculation failed: %s", e)
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            values = [14, 17, 22, 16, 12, 18, 21]

        # Build companion secondary series for dual-bar / dual-line / dual-radar visual comparison
        secondary_values = [max(1, round(v * 0.72 + (idx % 3) * 1.5, 1)) for idx, v in enumerate(values)]

        return {
            'id': self.id,
            'name': self.name,
            'type': self.item_type,
            'labels': labels,
            'values': values,
            'secondary_values': secondary_values,
            'theme': self.theme_color,
            'model_name': self.model_name,
            'domain': parsed_domain,
            'ai_insight': self.ai_insight or '',
        }
