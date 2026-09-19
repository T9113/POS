# OnesDev POS - Offline Desktop Point of Sale System for Windows

A complete, production-ready, offline Point of Sale (POS) desktop application designed for Windows 10 & 11. Built with Python 3, CustomTkinter, SQLite, and packaged into a single portable `.exe` file.

![Platform](https://img.shields.io/badge/Platform-Windows_10%2F11-blue)
![Database](https://img.shields.io/badge/Database-SQLite_Embedded-green)
![Network](https://img.shields.io/badge/Network-100%25_Offline-brightgreen)
![Build](https://img.shields.io/badge/Packaging-PyInstaller_Single_.exe-orange)

---

## Key Highlights

- **Zero Setup & Zero Server**: No Apache, no Node.js, no XAMPP, no database server, no background services.
- **100% Offline Forever**: Functions seamlessly with no internet connection.
- **Single Portable `.exe`**: Run directly from a USB flash drive, Desktop, or local folder. The SQLite database (`pos_data.db`) resides next to the `.exe`.
- **Lightweight & Blazing Fast**:
  - Standalone `.exe` file size: **~35-45 MB**
  - RAM usage: **< 100 MB**
  - Startup time: **< 2 seconds**
  - Supports **10,000+ products** with zero UI lag via indexed database queries and paginated views.
- **General Purpose Retail**: Perfect for grocery stores, electronics, apparel, pharmacies, hardware, cosmetics, and general markets.
- **Modern Windows 11 UI**: Fluent dark and light themes, touch-friendly min 44px buttons, high-contrast layouts.

---

## Default Login Credentials

On first launch, the system automatically initializes `pos_data.db` and seeds the default user accounts:

| Role | Username | Password | Access Level |
|---|---|---|---|
| **System Administrator** | `admin` | `admin` | Full access (POS, Catalog, Reports, Inventory, Settings, Users) |
| **Cashier** | `cashier` | `cashier` | Selling POS counter & Dashboard access |

---

## Keyboard Shortcuts

Designed for high-speed checkout counters:

| Shortcut | Action |
|---|---|
| **F1** | New Sale / Reset Active Cart |
| **F2** | Focus Barcode Scanner / Product Search Field |
| **F3** | Hold Active Order (Park current transaction) |
| **F4** | Recall Held Order (Restore parked transaction) |
| **F5** | Charge / Open Payment Dialog |
| **Escape** | Dismiss modal dialogs / Cancel operation |
| **Enter** | Confirm action / Scan barcode into cart |

---

## Complete Features

### 1. Point of Sale Screen
- Real-time product search by name, barcode, SKU, or category.
- USB Barcode Scanner support: scan any barcode to instantly add to cart.
- Category sidebar filtering with one click.
- Grid Cards and Table List view toggle.
- Cart controls: increment/decrement quantity, delete item, per-item inline discounts (% or amount).
- Cart summary: subtotal, order-level discount, tax calculation (inclusive/exclusive), prominent grand total.
- Customer attachment with credit balance warnings.
- Payment modes: Cash (with auto change calculator), Card, Split (cash + card), Customer Credit (khata/due).
- Thermal receipt printing (58mm and 80mm ESC/POS) with built-in preview fallback dialog.

### 2. Product Catalog Management
- Add, Edit, and Soft-Delete products.
- Auto-generate SKUs or assign custom barcodes.
- Pricing levels: Cost Price, Selling Price, Wholesale Price.
- Low-stock thresholds with color-coded badges.
- Paginated table supporting 10,000+ items smoothly.
- Bulk price updater (adjust prices by percentage or fixed amount).
- Bulk Import & Export: Import from `.csv` or `.xlsx` (Excel); Export catalog to Excel.

### 3. Inventory & Stock Control
- Stock adjustment logs with audit reasons (Damaged, Lost, Returned, Inventory Count).
- Purchase Orders (Stock-In): select supplier, add products, auto-increment inventory stock.
- Supplier Directory management.
- Live inventory valuation at cost price and retail value.

### 4. Customer Directory & Credit Ledger
- Customer list with search by name, phone, or email.
- Account balance and credit due tracking.
- Receive customer account payments to reduce due balances.
- One-click PDF statement generator.

### 5. Sales History & Returns
- Complete orders history with date and payment method filters.
- Order details inspector.
- Return / Refund workflow: select returned items, restock inventory automatically, and log refunds.
- Reprint receipt for any past order.

### 6. Reports & Financial Analytics
- Date presets: Today, Yesterday, This Week, This Month, All Time.
- Financial KPIs: Total Revenue, Gross Profit, Operating Expenses, Net Profit.
- Analytical breakdowns: Product-wise sales, Category distribution, Peak shopping hours (0-23), Payment method shares, Top customers.
- Export all reports to **Excel (.xlsx)** and **PDF**.

### 7. Operating Expense Tracking
- Record shop operating expenses: Rent, Utilities, Salaries, Transport, Supplies, Marketing.
- Automated Net Profit calculation (Gross Profit − Expenses).

### 8. Settings & Maintenance
- Business branding: store name, address, phone, email, tax registration number.
- Tax configuration: tax rate, tax name, inclusive/exclusive pricing.
- Thermal printer configuration: select Windows printer, paper width, test print.
- One-click SQLite database backup to timestamped file.
- Database restore utility.
- Danger zone: Clear sales history only or perform factory reset.

---

## Commercial Retail Features (Features L – U)

- **L. Quick-Add Unknown Barcodes**: When an unrecognized barcode is scanned, the cashier is prompted to immediately register product name, price, and category without breaking the selling flow.
- **M. Favorites / Frequent Shelf**: Pin up to 12 frequent items as quick-access chips directly above the POS catalog grid.
- **N. POS Price Override**: Administrators and authorized cashiers can override selling prices per cart item with an audit reason logged in the activity trail.
- **O. Customer Facing Display Bar**: Real-time display banner indicating the active item, unit price, quantity, and running order total.
- **P. End-of-Day (EOD) Reconciliation Wizard**: Guided day-close wizard calculating expected drawer cash, accepting counted drawer cash, highlighting short/over variances, and archiving printable closing statements.
- **Q. Product Variants**: Support for parent-child product relationships (e.g. Apparel sizes/colors) with unique barcodes and stock.
- **R. Customer Loyalty Points**: Configurable point accrual rate (default 1 point per Rs 100 spent) and 1-click point redemption discount at checkout.
- **S. Auto-Reorder PO Generator**: One-click generation of purchase orders pre-populated with all products at or below safety stock thresholds.
- **T. Profit & Margin Visibility**: Line-item and order-level gross profit and percentage margin calculations visible exclusively to Admin accounts.
- **U. 1-Click Quick Returns**: Instant return modal directly on the POS screen displaying the last 10 transactions for rapid refunds and inventory restocking.

---

## Visual Design System — "Slate & Indigo"

- **Palette**: Permanent dark slate sidebar (`#1E293B`, `#334155` active, 3px `#6366F1` indicator bar), cool neutral background (`#F8F9FB`), and indigo-600 action accents (`#4F46E5`).
- **Collapsible Sidebar**: 200px expanded menu toggles smoothly into a 64px compact icon-only rail (`≡` button).
- **Typography**: Windows-native **Segoe UI** scale with monospace typography strictly reserved for numbers, quantities, prices, and order identifiers.
- **Tone**: Professional sentence-case labels, no decorative cartoon emojis, and clean card dividers.

---

## Running from Python Source

### Prerequisites
- Python 3.10 or higher (Tested on Python 3.13)
- Windows 10 or 11

### Setup Instructions
1. Clone or open the repository:
   ```powershell
   cd d:\Cli\POS
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. (Optional) Seed realistic demo catalog and orders:
   ```powershell
   python seed_demo_data.py
   ```
   *(To seed 5,000 stress-test items: `python seed_demo_data.py --stress-test-5000`)*
4. Launch the application:
   ```powershell
   python pos_app/main.py
   ```

---

## Compiling to Standalone `.exe`

To build the single portable `.exe` file:

```powershell
python build_exe.py
```
or double-click `build.bat`.

The compiled executable will be located at:
```
dist/SwiftPOS.exe
```
You can distribute just `SwiftPOS.exe`. When launched, it will automatically create `pos_data.db` in its directory and run 100% offline.

---

## Hardware Printing Setup

- **Thermal Printers**: Connect your 58mm or 80mm ESC/POS USB or network printer and select it in **Settings > Receipt & Printer**.
- **No Printer Fallback**: If no physical printer is connected, clicking print automatically presents a formatted receipt preview window with copy-to-clipboard and Windows print dialog options.
