Here's the improved, complete prompt:

---

# SwiftPOS — Offline Desktop POS System for Windows

## Complete Build Prompt & Specification

---

## WHAT TO BUILD

A **complete, production-ready, offline Point of Sale desktop application for Windows**. Single portable `.exe` file. No installer, no server, no XAMPP, no browser, no internet. Double-click → it opens. That's it.

**General purpose** — grocery, clothing, electronics, pharmacy, hardware, bookshop, cosmetics, mobile shop, general store, any retail marketplace. NOT restaurant-specific (no tables, no kitchen display, no dine-in/takeaway).

---

## HARD CONSTRAINTS

- **Single `.exe`** via PyInstaller `--onefile --windowed`
- **No internet required** — 100% offline, forever
- **No background server** — no localhost, no XAMPP, no terminal window
- **No external dependencies** — user installs nothing (no Python, Node, Java, .NET)
- **No daily startup ritual** — no "start server first." Just double-click
- **Portable** — runs from USB, Desktop, any folder
- **Database:** SQLite `.db` file auto-created next to `.exe` on first run
- **Stack:** Python 3.11+ / CustomTkinter / SQLite3 / PyInstaller
- **Size:** `.exe` under 50 MB, RAM under 150 MB, startup under 3 seconds
- **No web tech inside** — no Electron, no embedded browser, no HTML rendering

---

## VISUAL DESIGN SYSTEM — "Slate & Indigo"

This POS will be used 8–12 hours daily in bright shop lighting. The design must reduce eye fatigue, maintain high readability, and feel like commercial POS software (Square, Shopify POS, Lightspeed) — not a student project or AI-generated UI.

### Design Tokens

**Light Mode (default):**
```
Background (app shell):     #F8F9FB   ← cool neutral, NOT warm cream
Surface (cards, panels):    #FFFFFF
Surface raised (cart):      #FFFFFF   with left border shadow only
Sidebar background:         #1E293B   ← dark slate, always dark regardless of mode
Sidebar text:               #94A3B8
Sidebar active item bg:     #334155
Sidebar active text:        #FFFFFF
Sidebar active indicator:   #6366F1   ← 3px left bar on active item

Border / dividers:          #E2E8F0
Border subtle:              #F1F5F9

Text primary:               #0F172A
Text secondary:             #475569
Text muted / placeholders:  #94A3B8
Text on dark (sidebar):     #E2E8F0

Accent / primary action:    #4F46E5   ← indigo-600, used ONLY for the main charge button and active states
Accent hover:               #4338CA
Accent subtle bg:           #EEF2FF   ← for selected category pill, active filters

Success:                    #059669   ← stock OK, payment complete
Success background:         #ECFDF5
Warning:                    #D97706   ← low stock, held orders
Warning background:         #FFFBEB
Danger:                     #DC2626   ← delete, void, refund, negative numbers
Danger background:          #FEF2F2

Cart item hover:            #F8FAFC
Input field background:     #F8F9FB   with 1px #E2E8F0 border
Input focus border:         #6366F1
```

**Dark Mode:**
```
Background:                 #0F1117
Surface:                    #1A1D27
Surface raised:             #222633
Sidebar background:         #0B0E14   ← even darker than shell
Border:                     #2A2F3D
Text primary:               #E2E8F0
Text secondary:             #8892A6
Text muted:                 #5A6478
Input field background:     #1A1D27
Accent remains:             #6366F1   ← brighter indigo in dark mode
```

### Typography

- **Primary font:** Segoe UI (ships with Windows — zero extra bundling)
- **Monospace font:** Cascadia Mono or Consolas (ships with Windows)
- **Type scale:**
  - Grand total price: 28px, Segoe UI Semibold, monospace digits
  - Screen title: 18px, Semibold
  - Section headers: 14px, Semibold
  - Body / product names: 13px, Regular
  - Cart item text: 13px, Regular
  - Labels, stock status, metadata: 11px, Regular
  - Button text: 13px, Medium
  - Sidebar items: 12px, Medium
- **Line height:** 1.4 for body, 1.2 for headings
- **No ALL CAPS anywhere** — use sentence case for labels, buttons, headers
- **No accented single words in headings** — no "Your BEST Sales Dashboard"
- **Monospace only for:** prices, quantities, totals, order numbers, time

### Spacing & Layout

- **Grid unit:** 8px. All padding, margins, gaps are multiples of 8 (8, 12, 16, 24, 32)
- **Border radius:** 8px for cards and panels, 6px for buttons and inputs, 4px for badges and pills, 0px for sidebar
- **Minimum clickable area:** 40px height for all buttons and interactive elements
- **Main charge button:** 52px height, full width of cart panel, indigo-600 bg, white text, 15px Semibold
- **Card shadows:** Light mode only — `0 1px 3px rgba(15,23,42,0.04)` — barely visible. Dark mode: no shadows, use 1px borders instead

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│ TOPBAR: [≡ Menu] [🔍 Search / barcode field............] [14:35] [Admin ●] │
├──────┬──────────────────────────────────┬───────────────────────────┤
│      │                                  │                           │
│  S   │   Category pills row:            │   ORDER #0042             │
│  I   │   [All] [Grocery] [Electronics]  │                           │
│  D   │                                  │   ┌─────────────────────┐ │
│  E   │   ┌──────┐ ┌──────┐ ┌──────┐   │   │ Rice 5kg   ×2  1400 │ │
│  B   │   │ Card │ │ Card │ │ Card │   │   │ Oil 1L     ×1   650 │ │
│  A   │   │ Prod │ │ Prod │ │ Prod │   │   │ Sugar 1kg  ×3   450 │ │
│  R   │   │ Name │ │ Name │ │ Name │   │   └─────────────────────┘ │
│      │   │ Rs X │ │ Rs X │ │ Rs X │   │                           │
│  ●Pos│   └──────┘ └──────┘ └──────┘   │   Subtotal       Rs 2500 │
│  Prod│                                  │   Tax (0%)          Rs 0 │
│  Inv │   ┌──────┐ ┌──────┐ ┌──────┐   │   Discount         −Rs 0 │
│  Cust│   │      │ │      │ │      │   │   ──────────────────────  │
│  Sale│   │      │ │      │ │      │   │   TOTAL         Rs 2,500  │
│  Rept│   │      │ │      │ │      │   │                           │
│  Exp │   └──────┘ └──────┘ └──────┘   │   [Hold] [Discount]       │
│  ⚙Set│                                  │   [💵 Cash] [💳 Card]    │
│      │                                  │   [══ CHARGE Rs 2,500 ══]│
├──────┴──────────────────────────────────┴───────────────────────────┤
│ STATUS: Cashier: Admin  │  Today: Rs 45,230 (32 orders)  │  Sep 19 │
└─────────────────────────────────────────────────────────────────────┘
```

**Sidebar:** Always dark (#1E293B), even in light mode. 200px wide. Icon + label for each nav item. Active item gets a 3px left indigo bar + lighter background. Collapsed state (icon only, 64px) available via toggle.

**Product grid:** 4-5 columns depending on window width. Each card shows: product name (13px), price in monospace (14px Semibold), stock badge. No emoji — use a small colored circle or product initial as identifier. Hover: subtle border highlight, no transform/scale animation.

**Cart panel:** Fixed 360px width on right. White/surface background. Scrollable item list. Sticky summary footer with totals and payment buttons.

**No decoration-only elements.** No gradients, no glows, no ornamental borders, no numbered markers (01/02/03), no background patterns. Every visual element encodes information.

---

## COMPLETE FEATURE LIST

### A. First Run & Login
- First launch: auto-create database, seed default admin (`admin`/`admin`), show quick setup wizard (business name, currency, tax — skippable)
- Login screen: username + password, "Remember me" checkbox
- Role-based access: Admin (full), Cashier (POS + limited views only)
- Session state maintained until logout or app close
- Password: salted SHA-256 hash, never stored plain

### B. Dashboard
- Today's total sales, order count, gross profit, average order value
- Low stock alerts list (products below minimum threshold)
- Top 5 selling products today (by quantity)
- Recent 5 orders quick list
- Quick action buttons: New Sale, Add Product, View Reports
- Live clock, greeting with user name, current date
- Refresh on view switch (no stale data)

### C. POS Screen (Core Selling)
- **Search bar** at top — search by name, barcode, SKU (instant filter, 50ms max response with 10,000+ products)
- **USB barcode scanner support** — auto-focus input, scan adds product to cart instantly, audible beep
- **Category filter row** — horizontal scrollable pills/tabs below search
- **Product grid** — clickable cards, grid or compact list toggle
- **Cart panel** showing current order:
  - Item name, unit price, quantity (editable via +/− or direct input), line total
  - Per-item discount (flat amount or percentage)
  - Remove item button (subtle, appears on hover)
- **Cart summary:**
  - Subtotal, bill-level discount (amount or %), tax (from settings), grand total
  - Grand total in large monospace text, visually dominant
- **Customer selection** — optional dropdown, default "Walk-in Customer"
- **Payment flow:**
  - Cash: enter received amount → auto-calculate change due
  - Card: mark as card payment (no real processing)
  - Split: part cash + part card with individual amount entry
  - Credit/Due: assign to customer account, track balance
- **Hold/Recall** — park current cart, start fresh, recall any held order from list
- **Order note** — optional text note on order
- **Receipt:** auto-print to thermal printer or show preview dialog
- **Keyboard shortcuts:**
  - `F1` New sale / `F2` Focus search / `F3` Hold order
  - `F4` Recall order / `F5` Checkout / `Esc` Cancel / `Enter` Confirm
  - Number keys for quick quantity when item is selected

### D. Product Management
- **Fields:** Name, SKU (auto-generate or manual), barcode, category, unit (piece/kg/liter/meter/box/pack/dozen/pair), cost price, selling price, wholesale price (optional), min stock level, current stock, image (optional local file), description, active/inactive
- **Product list:** paginated table, search/filter, sort by any column, color-coded stock (red/yellow/green)
- **Quick inline stock edit** from list view
- **Add/Edit** via modal form
- **Soft delete** (mark inactive, preserve history)
- **Bulk import** from CSV or Excel with column mapping dialog
- **Export** to CSV/Excel
- **Category management** — add, edit, delete, reorder
- **Bulk price update** — select multiple, adjust by % or flat amount

### E. Inventory & Stock
- **Stock adjustment** — increase/decrease with reason (damaged, lost, returned, counted, opening stock)
- **Adjustment log** — full audit trail with date, user, reason, quantity change
- **Purchase orders (Stock-In):**
  - Select supplier → add products with quantities and cost prices
  - On receive: stock auto-increases, cost prices update
  - Purchase history with date, supplier, total
- **Supplier management:** name, phone, email, address, notes, purchase history
- **Low stock report** — filterable list of all items below minimum
- **Stock valuation** — total inventory value at cost

### F. Customer Management
- **Fields:** Name, phone, email, address, notes, balance/credit
- **Customer list** with search
- **Purchase history** per customer — all orders linked to them
- **Credit/balance tracking** — outstanding amounts, payment collection
- **Customer statement** — printable summary of all transactions with running balance

### G. Sales History & Returns
- **Order list** — order#, date, customer, total, payment method, status
- **Search** by order number, customer name; **filter** by date range, payment method
- **Order detail** — full item breakdown with prices, discounts, tax, payment info
- **Return/Refund:**
  - Select past order → select items to return → enter return reason
  - Stock auto-restores on return
  - Refund amount recorded, linked to original order
- **Reprint receipt** for any past order

### H. Reports (all with date range filter + CSV/Excel/PDF export)
- Sales summary (total, order count, avg order, by day/week/month)
- Profit report (revenue − cost, gross margin %)
- Product-wise sales (units sold, revenue per product)
- Category-wise breakdown
- Hourly sales pattern (find peak hours)
- Payment method split (cash vs card vs credit)
- Tax collected
- Top customers by spend
- Current stock levels and value
- Expense summary by category
- **Daily closing summary** — one-page printable day-end report
- **Charts:** use matplotlib embedded in CustomTkinter canvas, or simple bar/line rendered via tkinter Canvas directly (no external chart library needed)

### I. Expense Tracking
- **Add expense:** date, category (rent/electricity/salary/transport/supplies/other), amount, description
- **Expense list** with search + date filter
- **Manage expense categories**
- **Net profit** = gross sales profit − total expenses

### J. Settings
- **Business profile:** name, address, phone, email, logo image, tax/registration number
- **Tax:** enable/disable, name (VAT/GST/Sales Tax), percentage, inclusive or exclusive
- **Receipt:** header text, footer text, toggle fields (tax/discount/barcode/customer), paper width (58mm/80mm), auto-print on/off
- **Currency:** symbol (Rs/$/€/£), position (before/after), decimal places (0 or 2), thousand separator
- **Printer:** select from system printers, test print button
- **Users:** add/edit/deactivate, username/password/role/fullname
- **Backup:** one-click copy `.db` to folder/USB with datestamp, restore from file, auto-backup reminder
- **Data reset:** clear sales only (keep products) or full factory reset — admin password required
- **Language:** English / Urdu (RTL support for Urdu)
- **Theme:** Dark / Light / System toggle
- **Sound:** enable/disable beep on scan and chime on sale

### K. Additional Features
- **Activity log** — who did what when (login, sale, refund, product edit, setting change)
- **Keyboard shortcut cheat sheet** — help modal showing all hotkeys
- **Multi-monitor awareness** — remember window position and size
- **Graceful error handling** — never crash, show user-friendly messages
- **Auto-backup reminder** at configurable intervals

---

## ADDITIONAL SUGGESTIONS (INCLUDE THESE)

### L. Quick-Add Products from POS
- If barcode scanned doesn't exist, prompt: "Product not found. Add new?" → open quick-add form pre-filled with the barcode. Cashier can add name + price + category and immediately sell it. Full details can be completed later.

### M. Favorite / Frequent Products
- Pin up to 12 "favorite" products on POS screen as a quick-access row above the grid. Configurable per user.

### N. Price Override at POS
- Allow admin to override selling price on a cart item (with reason). Logged in activity log.

### O. Customer Display Message
- Optional second-line text area showing current item and running total — for customer-facing secondary monitor (future readiness, display via a simple always-on-top borderless window).

### P. End of Day (EOD) Wizard
- Guided day-close flow: show day summary → expected cash in drawer → enter actual cash counted → record difference (short/over) → generate daily report → option to auto-backup database.

### Q. Product Variants (Simple)
- Support simple variants: a product "T-Shirt" can have child entries like "T-Shirt — Red / L", "T-Shirt — Blue / M" with individual stock and barcode but grouped in reports.

### R. Loyalty Points (Basic)
- Earn 1 point per Rs 100 spent (configurable). Redeem points as discount. Show points balance on customer profile.

### S. Auto-Reorder Suggestions
- When generating low-stock report, show a "Generate Purchase Order" button that pre-fills a PO with all low-stock items at their last purchase quantities and supplier.

### T. Profit per Sale
- Show profit margin on each completed order in sales history (selling price − cost price per item). Only visible to Admin role.

### U. Quick Returns from POS Screen
- "Return" button on POS screen opens last 10 orders. Tap an order → tap items to return → confirm. Faster than navigating to Sales History.

---

## DATABASE SCHEMA (SQLite — 15+ Tables)

1. **users** — id, username, password_hash, salt, full_name, role (admin/cashier), is_active, created_at
2. **products** — id, name, sku, barcode, category_id, parent_product_id (for variants), unit, cost_price, selling_price, wholesale_price, min_stock, current_stock, image_path, description, is_favorite, is_active, created_at, updated_at
3. **categories** — id, name, color_hex, sort_order, is_active
4. **customers** — id, name, phone, email, address, notes, balance, loyalty_points, created_at
5. **suppliers** — id, name, phone, email, address, notes, created_at
6. **orders** — id, order_number, customer_id, user_id, subtotal, discount_amount, discount_percent, tax_amount, total, cost_total, profit, amount_paid, change_due, payment_method, payment_status, note, status, created_at
7. **order_items** — id, order_id, product_id, product_name, quantity, unit_price, cost_price, discount, total, price_override, override_reason
8. **purchases** — id, supplier_id, user_id, total_amount, note, status, created_at
9. **purchase_items** — id, purchase_id, product_id, quantity, cost_price, total
10. **stock_adjustments** — id, product_id, user_id, type (in/out/adjustment), quantity_change, reason, note, created_at
11. **expenses** — id, category, amount, description, expense_date, user_id, created_at
12. **expense_categories** — id, name, is_active
13. **settings** — id, key, value (business_name, currency_symbol, tax_rate, tax_name, tax_inclusive, receipt_header, receipt_footer, paper_width, auto_print, language, theme, loyalty_rate, etc.)
14. **held_orders** — id, cart_data_json, customer_id, user_id, note, created_at
15. **returns** — id, order_id, user_id, items_json, total_refund, reason, created_at
16. **activity_log** — id, user_id, action, entity_type, entity_id, detail, created_at
17. **eod_reports** — id, user_id, date, total_sales, total_orders, expected_cash, actual_cash, difference, notes, created_at

**Indexes:** barcode, sku, product name, order_number, customer phone, orders.created_at, activity_log.created_at

---

## RECEIPT FORMAT (ESC/POS Thermal Printer)

```
================================
      YOUR BUSINESS NAME
    123 Main Street, City
     Phone: 0300-1234567
================================
Date: 2026-09-19    Time: 14:35
Order: #00145     Cashier: Admin
Customer: Walk-in
--------------------------------
Item           Qty  Price  Total
--------------------------------
Rice 5kg         2   700  1,400
Cooking Oil 1L   1   650    650
Sugar 1kg        3   150    450
--------------------------------
Subtotal                Rs 2,500
Discount (10%)           −Rs 250
Tax (17%)                 Rs 383
                ================
TOTAL                  Rs 2,633
                ================
Paid (Cash)            Rs 3,000
Change                   Rs 367
--------------------------------
Loyalty earned: +26 pts
Balance: 142 pts
--------------------------------
    Thank you for shopping!
     Return within 7 days.
================================
       [BARCODE / QR HERE]
```

Support 58mm and 80mm widths. Fallback: system print dialog preview window if no thermal printer detected.

---

## PROJECT STRUCTURE

```
/pos_app/
  __init__.py
  main.py              ← entry point
  config.py            ← paths, frozen detection, constants
  database.py          ← schema, migrations, seed

  models/              ← SQLite data access (one file per entity)
  controllers/         ← business logic (cart, payments, stock, reports)
  views/               ← CustomTkinter screens
    theme.py           ← design tokens from above
    main_window.py     ← shell (topbar, sidebar, status bar, content frame)
    login_view.py
    dashboard_view.py
    pos_view.py        ← the core selling screen
    products_view.py
    inventory_view.py
    customers_view.py
    sales_view.py
    reports_view.py
    expenses_view.py
    settings_view.py
    dialogs/           ← checkout, hold/recall, product form, receipt preview, EOD wizard
  utils/
    receipt_printer.py
    exporter.py        ← PDF (reportlab) + Excel (openpyxl)
    importer.py        ← CSV/Excel import
    sound.py
    i18n.py
    security.py        ← password hashing

  assets/              ← app icon, default logo, sounds

seed_demo_data.py
build_exe.py
build.bat
requirements.txt
README.md
```

---

## BUILD & FIRST RUN

**Build:**
```bash
pyinstaller --onefile --windowed --icon=app_icon.ico --name=SwiftPOS main.py
```

**First run behavior:**
1. No `.db` found → create it, run all CREATE TABLE statements
2. Seed default admin user, default settings (currency=Rs, tax=0%)
3. Show quick setup wizard (business name, currency, tax) — skippable
4. Land on login screen → `admin` / `admin`
5. After login → Dashboard

---

## WHAT NOT TO DO

- No web framework (Flask/Django/FastAPI)
- No browser needed to open
- No Electron or web wrapper
- No Node.js/npm/Java/.NET
- No internet to function
- No background server or service
- No 1990s Windows look — must look modern and commercial-grade
- No warm cream backgrounds (#F4F1EA) — that's an AI design tell
- No terracotta/clay accent (#D97757) — another AI tell
- No acid-green-on-black — another AI tell
- No newspaper broadsheet layout
- No ALL CAPS labels
- No "01 / 02 / 03" numbered markers unless content is truly sequential
- No emojis as product identifiers in the actual app
- No tracked-out spaced eyebrow labels
- No "→" appended to buttons
- No fade-and-slide-up animations on every section

---

## DELIVERABLES

1. Complete Python source code — well-commented, modular
2. `requirements.txt`
3. `build.bat` one-click build script
4. Compiled `dist/SwiftPOS.exe`
5. `README.md` with build instructions, first-run guide, shortcut list

---

That's the complete prompt. It has the exact design tokens, every feature, database schema, layout wireframe, anti-patterns to avoid, and build instructions — all in one document you can hand to any developer or AI tool and get a consistent, professional result.