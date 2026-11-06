# Dashboard Ninja with AI (Module for Odoo 19)

[![Odoo Version](https://img.shields.io/badge/Odoo-19.0-714B67?style=flat&logo=odoo)](https://www.odoo.com)
[![License](https://img.shields.io/badge/License-OPL--1-blue.svg)](https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html)
[![Frontend](https://img.shields.io/badge/Frontend-OWL%202-purple.svg)](https://odoo.github.io/owl/)
[![AI Engine](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)](https://ai.google.dev/)

**Dashboard Ninja with AI** is a real-time, interactive business analytics dashboard designed and developed by **Hammad Akbar** for Odoo 19, 18, 17, and 16. It empowers business owners and decision-makers with instant visual intelligence and generative AI briefings.

> 🔥 **Early-Bird Launch Offer:** Available at **$149 USD** exclusively for the **first 10 buyers**! Standard price increases to **$210 USD** after the first 10 purchases.
> 🎁 **First 10 Buyers VIP Bonus:** Need any extra chart, custom KPI, or bespoke report feature added? We will build & integrate your custom requirement **100% FREE of charge** for the first 10 buyers!

---

## 🌟 Highlights & Capabilities

### 1. Interactive Visualizations
- **KPI Cards:** Live counts, sums, and averages for any Odoo model (`sale.order`, `account.move`, `crm.lead`, `res.partner`).
- **Dynamic Charts:**
  - Bar Charts (e.g., Monthly Sales Revenue)
  - Line Charts (e.g., Lead Growth Trends)
  - Pie & Doughnut Charts (e.g., Top Customers, Sales by Category)
- **High Performance:** Powered by native Odoo OWL 2 and Chart.js without external browser bloat.

### 2. Generative AI Business Copilot
- **Executive Briefing:** Analyzes all active dashboard metrics and provides an instant executive summary.
- **Natural Language Interaction:** Ask questions directly to your data in plain English or Urdu.
- **Predictive Recommendations:** Uncovers profit drivers, margin anomalies, and inventory bottlenecks.
- **Flexible AI Provider:** Native support for Google Gemini 2.5 / Flash with smart rule-based local fallback.

### 3. Direct Email & Chatter Integration
- **Direct Mail Composer:** Click the **Send Mail** button directly on the dashboard to dispatch beautifully styled executive summaries, KPI tables, and AI briefings to partners or executives via Odoo's native mail composer.
- **Embedded & Native Chatter:** 
  - Integrated with `mail.thread` and `mail.activity.mixin`.
  - **Slide-Out Chatter Drawer:** Log notes and collaborate directly from the dashboard view without page reloads.
  - Full Odoo Chatter widget embedded in board & item backend forms for scheduling activities, logging notes, and managing followers.

### 4. Cyber Dark & Multi-Theme Engine
- Sleek dark aesthetic tailored for executive command centers (Cyber Dark, Neon Matrix, Midnight Violet, Executive Light).
- Neon Cyan, Lime Green, and Purple visual accents.
- Responsive design compatible with desktops, laptops, and tablets.
- Clickable KPI cards with automatic drill-down navigation to underlying records.
- Custom date filtering with manual start and end date range selectors.

---

## 📂 Architecture Overview

```text
dashboard_ninja_ai/
├── __init__.py
├── __manifest__.py                 # Manifest, dependencies & web assets
├── models/
│   ├── __init__.py
│   ├── dashboard_ninja.py          # Dashboard boards & items data engine
│   └── dashboard_ai_service.py     # Gemini AI API caller & analytics service
├── controllers/
│   ├── __init__.py
│   └── main.py                     # JSON-RPC controller endpoints
├── views/
│   ├── dashboard_ninja_item_views.xml   # Backend configuration views
│   └── dashboard_ninja_menus.xml        # Menus & Client Action registration
├── security/
│   └── ir.model.access.csv         # Role-based access control (RBAC)
└── static/
    ├── description/
    │   └── icon.png                # App icon for Odoo App Switcher
    └── src/
        ├── js/dashboard_ninja.js   # OWL Component & Chart.js rendering
        ├── xml/dashboard_ninja.xml # OWL Component QWeb templates
        └── scss/dashboard_ninja.scss # Cyber Dark visual styling
```

---

## ⚙️ Configuration & AI API Key Setup

1. **Enable Developer Mode** in your Odoo database.
2. Navigate to **Settings -> Technical -> Parameters -> System Parameters**.
3. Create or edit the parameter:
   - **Key:** `dashboard_ninja_ai.gemini_api_key`
   - **Value:** `<Your Google Gemini API Key>` (Obtain free from [Google AI Studio](https://aistudio.google.com/))
4. Once saved, the AI Copilot will automatically communicate with Google Gemini in real-time.

---

## 🚀 How to Add Custom Dashboard Items

1. Open **Ninja Dashboard -> Configuration -> Dashboard Items**.
2. Click **New**.
3. Fill in:
   - **Name:** e.g., *"Top 5 Customers by Revenue"*
   - **Item Type:** Bar, Pie, Line, Doughnut, or KPI Card
   - **Model to Track:** Select any Odoo model (e.g., `sale.order`)
   - **Calculation Type:** Count, Sum, or Average
   - **Group By Field:** Select grouping field (e.g., `partner_id` or `date_order`)
   - **Filter Domain:** e.g., `[('state', '=', 'sale')]`
4. Click **Save**. Return to **Analytics & AI Copilot** and click **Refresh**!

---

## 📄 License
This module is licensed under the **Odoo Proprietary License v1.0 (OPL-1)**.
Commercial redistribution allowed on Odoo Apps Store.
