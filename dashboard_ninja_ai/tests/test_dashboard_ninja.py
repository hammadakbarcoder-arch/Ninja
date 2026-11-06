# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDashboardNinja(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        cls.user_model = cls.env['ir.model'].search([('model', '=', 'res.users')], limit=1)
        
        # Create a dedicated test board
        cls.board = cls.env['dashboard.ninja.board'].create({
            'name': 'Automated Test Executive Board',
            'is_public': True,
        })

        # Add a KPI item
        cls.kpi_item = cls.env['dashboard.ninja.item'].create({
            'name': 'Test Total Partners',
            'board_id': cls.board.id,
            'item_type': 'kpi',
            'model_id': cls.partner_model.id,
            'aggregate_func': 'count',
            'theme_color': 'neon_blue',
        })

        # Add a Chart item
        country_field = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.partner_model.id),
            ('name', '=', 'country_id')
        ], limit=1)
        
        cls.chart_item = cls.env['dashboard.ninja.item'].create({
            'name': 'Test Partners by Country',
            'board_id': cls.board.id,
            'item_type': 'bar',
            'model_id': cls.partner_model.id,
            'aggregate_func': 'count',
            'field_group_by': country_field.id if country_field else False,
            'theme_color': 'neon_green',
        })

    def test_01_board_structure(self):
        """Test board creation and items linking."""
        self.assertTrue(self.board.id)
        self.assertEqual(len(self.board.item_ids), 2)
        self.assertEqual(self.board.item_ids[0].name, 'Test Total Partners')

    def test_02_get_dashboard_data(self):
        """Test OWL frontend data delivery structure."""
        data = self.board.get_dashboard_data()
        self.assertEqual(data['board_id'], self.board.id)
        self.assertEqual(data['name'], 'Automated Test Executive Board')
        self.assertIn('items', data)
        self.assertEqual(len(data['items']), 2)

        # Check KPI item structure
        kpi_data = [it for it in data['items'] if it['id'] == self.kpi_item.id][0]
        self.assertEqual(kpi_data['type'], 'kpi')
        self.assertIsInstance(kpi_data['value'], (int, float))

        # Check Chart item structure
        chart_data = [it for it in data['items'] if it['id'] == self.chart_item.id][0]
        self.assertEqual(chart_data['type'], 'bar')
        self.assertIsInstance(chart_data['labels'], list)
        self.assertIsInstance(chart_data['values'], list)

    def test_03_date_filtering(self):
        """Test date filters across time ranges without throwing exceptions."""
        for df in ['all', 'today', 'this_week', 'this_month', 'this_year']:
            data = self.board.get_dashboard_data(date_filter=df)
            self.assertEqual(data['date_filter'], df)
            self.assertIn('items', data)

    def test_04_ai_dashboard_generation(self):
        """Test Gen-AI / Template Dashboard generator."""
        res = self.env['dashboard.ninja.board'].generate_ai_dashboard('Operations')
        self.assertTrue(res.get('board_id'))
        generated_board = self.env['dashboard.ninja.board'].browse(res['board_id'])
        self.assertTrue(len(generated_board.item_ids) >= 1)

    def test_05_ai_service_insights(self):
        """Test AI briefing generation and rule-based fallback."""
        res = self.env['dashboard.ninja.ai.service'].ask_ai_insights(self.board.id, user_prompt='What is our client trajectory?')
        self.assertEqual(res['status'], 'success')
        self.assertTrue(bool(res['reply']))
        self.assertIn('Ninja AI', res['reply'])

    def test_06_dashboard_chatter(self):
        """Test chatter messages and direct post on board."""
        post_res = self.board.post_chatter_message(self.board.id, "Testing automated chatter log note.")
        self.assertTrue(post_res['success'])
        
        messages = self.board.get_chatter_messages(self.board.id)
        self.assertTrue(len(messages) >= 1)
        self.assertIn("Testing automated chatter log note.", messages[0]['body'])

    def test_07_dashboard_direct_mail(self):
        """Test mail composer action creation for executive briefing."""
        mail_action = self.board.action_send_dashboard_mail(self.board.id)
        self.assertEqual(mail_action['res_model'], 'mail.compose.message')
        self.assertEqual(mail_action['target'], 'new')
        self.assertIn('Executive Dashboard Briefing', mail_action['context']['default_subject'])

    def test_08_security_access_and_record_rules(self):
        """Test access rights and record rules for public vs private boards."""
        demo_user = self.env['res.users'].create({
            'name': 'Demo Security Auditor',
            'login': 'demo_auditor',
            'email': 'auditor@test.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('dashboard_ninja_ai.group_dashboard_ninja_user').id])],
        })

        # Public board must be readable
        public_boards = self.env['dashboard.ninja.board'].with_user(demo_user).search([('id', '=', self.board.id)])
        self.assertTrue(public_boards, "Public board must be visible to standard users")

        # Private board of another user must be hidden
        private_board = self.env['dashboard.ninja.board'].create({
            'name': 'Confidential C-Level Board',
            'is_public': False,
            'user_id': self.env.ref('base.user_admin').id,
        })
        visible_private = self.env['dashboard.ninja.board'].with_user(demo_user).search([('id', '=', private_board.id)])
        self.assertFalse(visible_private, "Private board must NOT be visible to other standard users")

    def test_09_kpi_target_and_growth(self):
        """Test target progress bar and growth percentage calculation."""
        self.kpi_item.write({
            'target_value': 10.0,
            'growth_rate': 18.5,
            'show_progress': True,
        })
        item_data = self.kpi_item.get_item_data()
        self.assertEqual(item_data['growth_rate'], 18.5)
        self.assertTrue(item_data['show_progress'])
        self.assertIn('target_progress', item_data)
        self.assertIsInstance(item_data['target_progress'], float)

    def test_10_multi_board_tabs(self):
        """Test multi-dashboard switcher tabs listing."""
        board_2 = self.env['dashboard.ninja.board'].create({
            'name': 'Secondary Operations Board',
            'is_public': True,
        })
        data = self.board.get_dashboard_data()
        self.assertIn('all_boards', data)
        board_ids = [b['id'] for b in data['all_boards']]
        self.assertIn(self.board.id, board_ids)
        self.assertIn(board_2.id, board_ids)

    def test_11_no_duplicate_boards_and_deletion(self):
        """Test that generating the same template reuses board instead of creating duplicates, and test board deletion."""
        res_1 = self.env['dashboard.ninja.board'].generate_ai_dashboard('Sales')
        board_id_1 = res_1['board_id']
        
        # Generating again must reuse the same board, not create a duplicate
        res_2 = self.env['dashboard.ninja.board'].generate_ai_dashboard('Sales')
        board_id_2 = res_2['board_id']
        self.assertEqual(board_id_1, board_id_2, "Must reuse existing board rather than creating duplicate!")

        # Test deletion
        del_res = self.env['dashboard.ninja.board'].delete_board(board_id_1)
        self.assertTrue(del_res['success'])
        self.assertFalse(self.env['dashboard.ninja.board'].browse(board_id_1).exists())

    def test_12_all_vs_domain_specific_filtering(self):
        """Test that 'all' mode returns all 12 items while specific domain boards return only their domain items."""
        Board = self.env['dashboard.ninja.board']
        all_data = Board.get_dashboard_data('all')
        self.assertEqual(all_data['board_id'], 'all')
        self.assertEqual(len(all_data['items']), 12, "All Dashboards mode must return all 12 items (6 KPIs + 6 Charts)")

        for tpl in ['Sales', 'Finance', 'CRM', 'Operations']:
            res = Board.generate_ai_dashboard(tpl)
            dom_data = Board.get_dashboard_data(res['board_id'])
            self.assertEqual(len(dom_data['items']), 7, f"{tpl} Dashboard must return its 7 domain-specific items")

    def test_13_security_manager_vs_user_acl_and_rules(self):
        """Test security groups, ACLs, and record rules for standard user vs manager."""
        user_group = self.env.ref('dashboard_ninja_ai.group_dashboard_ninja_user')
        mgr_group = self.env.ref('dashboard_ninja_ai.group_dashboard_ninja_manager')
        base_user = self.env.ref('base.group_user')

        std_user = self.env['res.users'].create({
            'name': 'Standard Ninja User',
            'login': 'std_ninja_user_sec',
            'email': 'std_ninja@test.com',
            'group_ids': [(6, 0, [base_user.id, user_group.id])],
        })
        mgr_user = self.env['res.users'].create({
            'name': 'Manager Ninja User',
            'login': 'mgr_ninja_user_sec',
            'email': 'mgr_ninja@test.com',
            'group_ids': [(6, 0, [base_user.id, mgr_group.id])],
        })

        # Standard user can create their own private board and read it
        own_board = self.env['dashboard.ninja.board'].with_user(std_user).create({
            'name': 'My Personal Sales Board',
            'is_public': False,
        })
        self.assertEqual(own_board.user_id.id, std_user.id)

        # Manager can see even private boards of standard users
        mgr_visible = self.env['dashboard.ninja.board'].with_user(mgr_user).search([('id', '=', own_board.id)])
        self.assertTrue(mgr_visible, "Dashboard Manager must have full visibility across boards")

    def test_14_multilang_ai_report_and_data_upload(self):
        """Test Topic-Specific & Multi-Language AI Report Generator (English, Roman Urdu, Urdu, Arabic) and Data Upload."""
        import base64
        ai_svc = self.env['dashboard.ninja.ai.service']

        # 1. Explicit English selection even with mixed prompt
        rep_en_sales = ai_svc.generate_ai_report(self.board.id, user_prompt='Generate Sales and Revenue Report', lang='en')
        self.assertEqual(rep_en_sales['status'], 'success')
        self.assertEqual(rep_en_sales['lang'], 'en')
        self.assertEqual(rep_en_sales['topic_key'], 'sales')

        # 2. Financial report produces distinct topic, title, and rows from Sales report
        rep_en_fin = ai_svc.generate_ai_report(self.board.id, user_prompt='Generate Financial and Invoice Report', lang='en')
        self.assertEqual(rep_en_fin['topic_key'], 'finance')
        self.assertNotEqual(rep_en_sales['title'], rep_en_fin['title'])
        self.assertNotEqual(rep_en_sales['analytics_rows'][0]['name'], rep_en_fin['analytics_rows'][0]['name'])

        # 3. Roman Urdu report generation
        rep_ro_ur = ai_svc.generate_ai_report(self.board.id, user_prompt='Sales aur Revenue ki mukammal report banao', lang='ro_ur')
        self.assertEqual(rep_ro_ur['status'], 'success')
        self.assertEqual(rep_ro_ur['lang'], 'ro_ur')
        self.assertTrue(len(rep_ro_ur['analytics_rows']) >= 1)
        self.assertTrue(len(rep_ro_ur['smart_suggestions']) >= 1)

        # 4. Urdu script & Arabic report generation
        rep_ur = ai_svc.generate_ai_report(self.board.id, user_prompt='سیلز اور منافع کی رپورٹ بنائیں', lang='ur')
        self.assertEqual(rep_ur['status'], 'success')
        self.assertEqual(rep_ur['lang'], 'ur')

        rep_ar = ai_svc.generate_ai_report(self.board.id, user_prompt='Generate CRM Report', lang='ar')
        self.assertEqual(rep_ar['status'], 'success')
        self.assertEqual(rep_ar['lang'], 'ar')
        self.assertEqual(rep_ar['topic_key'], 'crm')

        # 5. CSV Data Upload & Analytics
        csv_content = b"Product,Revenue\nEnterprise License,540\nAI Copilot,380\nCloud Hosting,290\n"
        b64_data = base64.b64encode(csv_content).decode('utf-8')
        up_res = ai_svc.upload_and_analyze_data(self.board.id, 'sales_q4.csv', b64_data, lang='ro_ur')
        self.assertEqual(up_res['status'], 'success')
        self.assertEqual(up_res['row_count'], 3)
        self.assertEqual(up_res['total_sum'], 1210.0)
