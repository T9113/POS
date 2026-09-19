# Complete Prompt: Offline Desktop POS System for Windows

---

## WHAT TO BUILD

Build me a **complete, production-ready, offline Point of Sale (POS) desktop application for Windows**. It must be a **single portable `.exe` file** — no installer, no server, no XAMPP, no Node.js, no database server, no browser needed. The user double-clicks the `.exe` and it opens. That's it.

---

## CORE REQUIREMENTS (NON-NEGOTIABLE)

### 1. Zero Setup, Zero Server
- **Single `.exe` file** that runs on any Windows 10/11 machine
- **No internet required** — works 100% offline, forever
- **No background server** — no localhost, no XAMPP, no Apache, no terminal
- **No dependencies** — user does NOT install Python, Node, Java, .NET, or anything else
- **No daily startup ritual** — no "start server first, then open app." Just double-click
- **Portable** — can run from USB drive, Desktop, any folder

### 2. Technology Stack
- **Language:** Python 3
- **GUI Framework:** `customtkinter` (modern, native Windows look) or `PySide6` / `PyQt6`
- **Database:** SQLite (single `.db` file, stored next to the `.exe`)
- **Packaging:** PyInstaller `--onefile` to create single `.exe`
- **No web tech inside** — no Electron, no embedded browser, no HTML rendering

### 3. Lightweight Performance
- `.exe` size: under 50 MB ideally, max 100 MB
- RAM usage: under 150 MB while running
- Startup time: under 3 seconds on average hardware
- Smooth scrolling and UI with 10,000+ products in database
- No lag when typing in search or switching screens

---

## GENERAL PURPOSE — NOT RESTAURANT SPECIFIC

This POS is for **any type of retail business**:
- Grocery store, clothing shop, electronics store, pharmacy, hardware store, bookshop, cosmetics shop, general store, mobile accessories shop, stationery shop, any marketplace

**Do NOT include** restaurant-specific features like:
- Table management, kitchen display, dine-in/takeaway toggle, waiter assignment, menu courses

**DO include** general retail features like:
- Barcode support, stock tracking, product categories, customer management, supplier info, purchase tracking, profit/loss

---

## COMPLETE FEATURE LIST

### A. Dashboard (Home Screen)
- Today's total sales amount
- Today's total orders count
- Today's total profit
- Low stock alerts (products below minimum quantity)
- Top 5 selling products today
- Quick action buttons: New Sale, Add Product, View Reports
- Current date and time display
- Greeting with logged-in user name

### B. Point of Sale Screen (Main Selling Screen)
- **Product search bar** — search by name, barcode, SKU, or category (instant results as you type)
- **Product grid/list view** — show products as clickable cards or list rows, toggle between views
- **Category filter sidebar** — click a category to filter products
- **Barcode scanner input** — focus cursor in barcode field, scan with USB barcode scanner, auto-add to cart
- **Cart/bill panel on right side** — shows current order items
- **Cart item controls:**
  - Product name, unit price, quantity (editable), line total
  - +/− buttons to change quantity
  - Delete button to remove item
  - Inline discount per item (amount or percentage)
- **Cart summary:**
  - Subtotal
  - Overall discount (amount or percentage, applied to whole bill)
  - Tax (configurable tax rate from settings, default 0%)
  - Grand total (large, bold, prominent)
- **Customer selection** — optional, pick existing customer or "Walk-in"
- **Payment section:**
  - Cash payment — enter amount received, show change due
  - Card payment — just mark as card (no real card processing needed)
  - Split payment — part cash, part card
  - Credit/due — customer pays later, track the balance
- **Hold order** — park current order, start new one, recall held orders later
- **Order note** — optional text note attached to the order
- **Print receipt** — send to thermal printer (ESC/POS compatible, 58mm or 80mm)
- **Keyboard shortcuts:**
  - `F1` = New sale
  - `F2` = Focus search/barcode field
  - `F3` = Hold order
  - `F4` = Recall held order
  - `F5` = Payment / checkout
  - `Escape` = Cancel / go back
  - `Enter` = Confirm action
  - Number keys = quick quantity entry when product selected

### C. Product Management
- **Add product** with fields:
  - Product name (required)
  - SKU / product code (auto-generate or manual)
  - Barcode number (manual entry or scan)
  - Category (select from list or create new)
  - Unit (piece, kg, liter, meter, box, pack, dozen, pair, etc.)
  - Cost price (purchase price)
  - Selling price
  - Wholesale price (optional)
  - Minimum stock level (for low-stock alerts)
  - Current stock quantity
  - Product image (optional, stored locally)
  - Description / notes
  - Active/inactive status
- **Edit product** — same form, pre-filled
- **Delete product** — soft delete (mark inactive, keep history)
- **Import products from CSV/Excel** — bulk upload with column mapping
- **Export products to CSV/Excel**
- **Product list** with:
  - Search and filter
  - Sort by name, price, stock, category
  - Pagination or virtual scrolling for large lists
  - Quick inline stock edit
  - Color-coded stock status (red = below minimum, yellow = low, green = ok)
- **Category management** — add, edit, delete, reorder categories
- **Bulk price update** — select multiple products, change price by percentage or amount

### D. Inventory / Stock Management
- **Stock adjustment** — manually increase or decrease stock with reason (damaged, lost, returned, counted)
- **Stock transfer log** — record of all adjustments with date, user, reason
- **Purchase / Stock-In:**
  - Create purchase order: select supplier, add products, quantities, cost prices
  - When purchase is received, stock auto-increases
  - Track purchase history
- **Supplier management:**
  - Add supplier: name, phone, email, address, notes
  - View supplier purchase history
  - Edit / delete supplier
- **Low stock report** — all products below their minimum level
- **Stock value report** — total value of all inventory at cost price

### E. Customer Management
- **Add customer:** name, phone, email, address, notes
- **Edit / delete customer**
- **Customer list** with search
- **Customer purchase history** — all orders by this customer
- **Customer balance/credit** — if customer has due amount, show it
- **Customer statement** — printable summary of all transactions

### F. Sales History / Orders
- **Order list** — all completed sales with:
  - Order number, date/time, customer name, total amount, payment method, status
  - Search by order number, customer name, date
  - Filter by date range, payment method
- **Order detail view** — full breakdown of items, prices, discounts, tax, payment
- **Return / refund:**
  - Select an order, select items to return
  - Stock auto-increases on return
  - Refund amount tracked
  - Return reason recorded
- **Reprint receipt** — print receipt for any past order

### G. Reports & Analytics
All reports should have **date range filter** (today, yesterday, this week, this month, custom range) and **export to CSV/Excel/PDF**.

- **Sales report** — total sales, order count, average order value, grouped by day/week/month
- **Profit report** — total revenue minus total cost, gross profit margin
- **Product-wise sales** — which products sold how many units, revenue per product
- **Category-wise sales** — sales breakdown by category
- **Hourly sales** — sales volume by hour of day (find peak hours)
- **Payment method report** — how much came from cash vs card vs credit
- **Tax report** — total tax collected in period
- **Customer report** — top customers by purchase amount
- **Stock report** — current stock levels, stock value
- **Expense report** — if expense tracking is included
- **Daily summary** — one-page printable summary of the day

### H. Expense Tracking (Simple)
- **Add expense:** date, category (rent, electricity, salary, transport, supplies, other), amount, description
- **Expense list** with search and date filter
- **Expense categories** — manage list of expense types
- **Expense report** — total expenses by category and date range
- **Net profit** = Sales profit − Expenses

### I. Settings & Configuration
- **Business profile:**
  - Business name, address, phone, email
  - Logo (for receipt header)
  - Tax number / registration number
- **Tax settings:**
  - Enable/disable tax
  - Tax name (VAT, GST, Sales Tax, etc.)
  - Tax percentage
  - Tax inclusive or exclusive pricing
- **Receipt settings:**
  - Header text (business info)
  - Footer text (return policy, thank you message)
  - Show/hide fields: tax, discount, barcode, customer info
  - Receipt width: 58mm or 80mm
  - Auto-print on sale complete (on/off)
- **Currency settings:**
  - Currency symbol (Rs, $, €, £, etc.)
  - Currency position (before or after amount)
  - Decimal places (0 or 2)
  - Thousand separator
- **Printer settings:**
  - Select printer from system printers list
  - Test print button
- **User management:**
  - Admin and Cashier roles
  - Admin: full access to everything
  - Cashier: only POS screen, cannot edit products/settings/reports
  - Add user: username, password, role, full name
  - Edit / deactivate user
  - Login screen with username + password
- **Backup & restore:**
  - One-click backup: copies the `.db` file to a chosen folder or USB drive with date stamp
  - Restore from backup: select a `.db` file to restore
  - Auto-backup reminder (every day / every week)
- **Data reset:**
  - Clear all sales data (keep products)
  - Factory reset (delete everything, fresh start)
  - Require admin password to confirm

### J. Additional Features
- **Multi-language support** — at minimum English and Urdu (RTL support)
- **Dark mode / Light mode** toggle
- **Sound effects** — subtle beep on barcode scan, cash register sound on sale complete (optional, can disable)
- **Shortcut cheat sheet** — help screen showing all keyboard shortcuts
- **Auto-update check** — on startup, if internet is available, check a URL for new version (optional, non-blocking)
- **Activity log** — record who did what and when (login, sale, refund, product edit, settings change)

---

## USER INTERFACE DESIGN GUIDELINES

### Layout (POS Screen)
```
┌──────────────────────────────────────────────────────────────────┐
│  [Logo/Name]    [Search Bar]           [Clock]  [User] [Menu]   │
├────────┬──────────────────────────────┬──────────────────────────┤
│        │                              │   CART / CURRENT ORDER   │
│  C     │   PRODUCT GRID               │                          │
│  A     │   (cards or list view)       │   Item 1    ×2    Rs 500 │
│  T     │                              │   Item 2    ×1    Rs 300 │
│  E     │   [product] [product]        │   ─────────────────────  │
│  G     │   [product] [product]        │   Subtotal      Rs 800  │
│  O     │   [product] [product]        │   Discount       −Rs 0  │
│  R     │   [product] [product]        │   Tax              Rs 0  │
│  I     │                              │   TOTAL         Rs 800   │
│  E     │                              │                          │
│  S     │                              │   [Hold] [Discount]      │
│        │                              │   [Cash] [Card] [Credit] │
│        │                              │   [=== CHARGE Rs 800 ==] │
└────────┴──────────────────────────────┴──────────────────────────┘
```

### Design Rules
- **Clean, minimal, professional** — no flashy colors, no unnecessary decoration
- **High contrast** — easy to read in bright shop lighting
- **Large touch-friendly buttons** — minimum 44px height for all clickable elements (also works with touchscreen monitors)
- **Consistent spacing** — 8px grid system
- **Font:** System font or a clean sans-serif (Segoe UI on Windows)
- **Primary color:** A calm blue (like #2563EB) — trustworthy, professional
- **Danger actions in red** — delete, void, refund buttons
- **Success in green** — payment complete, stock ok
- **Warning in amber/yellow** — low stock, held orders
- **Smooth transitions** — subtle 150ms transitions on hover/click, nothing flashy
- **Status bar at bottom** — show: logged in user, total sales today, current date
- **Navigation:** sidebar or top tabs for switching between POS, Products, Inventory, Customers, Reports, Settings
- **Modal dialogs** for confirmations and quick forms — don't navigate away from current screen unnecessarily

---

## DATABASE SCHEMA (SQLite)

Design the database with these tables at minimum:

1. **users** — id, username, password_hash, full_name, role, is_active, created_at
2. **products** — id, name, sku, barcode, category_id, unit, cost_price, selling_price, wholesale_price, min_stock, current_stock, image_path, description, is_active, created_at, updated_at
3. **categories** — id, name, sort_order, is_active
4. **customers** — id, name, phone, email, address, notes, balance, created_at
5. **suppliers** — id, name, phone, email, address, notes, created_at
6. **orders** — id, order_number, customer_id, user_id, subtotal, discount_amount, discount_percent, tax_amount, total, amount_paid, change_due, payment_method, payment_status, note, status, created_at
7. **order_items** — id, order_id, product_id, product_name, quantity, unit_price, discount, total, cost_price
8. **purchases** — id, supplier_id, user_id, total_amount, note, status, created_at
9. **purchase_items** — id, purchase_id, product_id, quantity, cost_price, total
10. **stock_adjustments** — id, product_id, user_id, quantity_change, reason, note, created_at
11. **expenses** — id, category, amount, description, date, user_id, created_at
12. **settings** — id, key, value
13. **held_orders** — id, cart_data_json, customer_id, user_id, note, created_at
14. **returns** — id, order_id, user_id, items_json, total_refund, reason, created_at
15. **activity_log** — id, user_id, action, detail, created_at

---

## RECEIPT FORMAT (Thermal Printer)

```
================================
      YOUR BUSINESS NAME
    123 Main Street, City
     Phone: 0300-1234567
================================
Date: 2026-09-19  Time: 14:35
Order#: 00145    Cashier: Admin
Customer: Walk-in
--------------------------------
Item           Qty  Price  Total
--------------------------------
Product One      2   500   1,000
Product Two      1   300     300
Product Three    3   150     450
--------------------------------
Subtotal:               Rs 1,750
Discount (10%):          −Rs 175
Tax (17%):               Rs 268
                ================
TOTAL:                 Rs 1,843
                ================
Paid (Cash):           Rs 2,000
Change:                  Rs 157
--------------------------------
    Thank you for shopping!
     Return within 7 days
================================
```

Use **ESC/POS** commands for thermal printer. Support both **58mm and 80mm** paper widths. If no printer is connected, show the receipt in a print-preview window using system print dialog as fallback.

---

## BUILD & PACKAGING INSTRUCTIONS

### Step 1: Development
- Write all code in Python 3.11+
- Use `customtkinter` for UI (or `PySide6` — pick one, be consistent)
- Use `sqlite3` (built into Python) for database
- Use `python-escpos` or `win32print` for thermal printing
- Use `openpyxl` for Excel export
- Use `reportlab` or `fpdf2` for PDF generation
- Structure code in clean modules:
  ```
  /pos_app/
    main.py
    database.py
    models/
    views/
    controllers/
    utils/
    assets/  (icons, default logo)
  ```

### Step 2: Package as .exe
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=app_icon.ico --name="SwiftPOS" main.py
```
- `--onefile` = single .exe
- `--windowed` = no console window
- `--icon` = custom app icon
- Output: `dist/SwiftPOS.exe` — this is the only file the user needs

### Step 3: First Run Behavior
- On first launch, if no `.db` file exists next to the `.exe`, create it automatically
- Run all table creation SQL
- Insert default settings (currency=Rs, tax=0%, etc.)
- Create default admin user: username `admin`, password `admin`
- Show a setup wizard: business name, currency, tax — can be skipped
- Go to main POS screen

---

## WHAT TO DELIVER

1. **Complete Python source code** — well-commented, organized in modules
2. **Requirements.txt** — all pip dependencies
3. **Build script** — a `.bat` or `.py` file that runs PyInstaller with correct flags
4. **The compiled `.exe` file** — ready to double-click and use
5. **A short `README.md`** — how to build from source, first-run instructions, keyboard shortcuts

---

## IMPORTANT REMINDERS

- **DO NOT** use any web framework (Flask, Django, FastAPI)
- **DO NOT** require a browser to open
- **DO NOT** use Electron or any web-based wrapper
- **DO NOT** require Node.js, npm, Java, .NET runtime
- **DO NOT** need internet to function (offline-first, always)
- **DO NOT** require running any server or service in background
- **DO NOT** make the UI look like a 1990s Windows app — it should look modern and clean
- **DO** use SQLite — it's a single file, no server, perfect for this
- **DO** handle errors gracefully — never crash, show user-friendly error messages
- **DO** make it fast — lazy loading, pagination, indexed database queries
- **DO** make the database auto-create on first run
- **DO** test with 5,000+ products to ensure no lag

---
