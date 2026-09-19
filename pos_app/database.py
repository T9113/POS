import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
from pos_app.config import DB_PATH
from pos_app.utils.security import hash_password

SCHEMA_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Admin', 'Cashier')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    color_hex TEXT DEFAULT '#4F46E5',
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sku TEXT UNIQUE,
    barcode TEXT,
    category_id INTEGER,
    parent_product_id INTEGER,
    unit TEXT DEFAULT 'piece',
    cost_price REAL NOT NULL DEFAULT 0.0,
    selling_price REAL NOT NULL DEFAULT 0.0,
    wholesale_price REAL DEFAULT 0.0,
    min_stock REAL DEFAULT 5.0,
    current_stock REAL DEFAULT 0.0,
    image_path TEXT,
    description TEXT,
    is_favorite INTEGER DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY(parent_product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    notes TEXT,
    balance REAL DEFAULT 0.0,
    loyalty_points REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    customer_id INTEGER,
    user_id INTEGER,
    subtotal REAL NOT NULL DEFAULT 0.0,
    discount_amount REAL NOT NULL DEFAULT 0.0,
    discount_percent REAL NOT NULL DEFAULT 0.0,
    tax_amount REAL NOT NULL DEFAULT 0.0,
    total REAL NOT NULL DEFAULT 0.0,
    cost_total REAL DEFAULT 0.0,
    profit REAL DEFAULT 0.0,
    amount_paid REAL NOT NULL DEFAULT 0.0,
    change_due REAL NOT NULL DEFAULT 0.0,
    payment_method TEXT NOT NULL,
    payment_status TEXT NOT NULL DEFAULT 'paid',
    note TEXT,
    status TEXT NOT NULL DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Order Items table
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER,
    product_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit_price REAL NOT NULL,
    cost_price REAL DEFAULT 0.0,
    discount REAL DEFAULT 0.0,
    total REAL NOT NULL,
    price_override INTEGER DEFAULT 0,
    override_reason TEXT,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
);

-- Purchases table (Stock-In)
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER,
    user_id INTEGER,
    total_amount REAL NOT NULL DEFAULT 0.0,
    note TEXT,
    status TEXT NOT NULL DEFAULT 'received',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Purchase Items table
CREATE TABLE IF NOT EXISTS purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    cost_price REAL NOT NULL,
    total REAL NOT NULL,
    FOREIGN KEY(purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(id)
);

-- Stock Adjustments table
CREATE TABLE IF NOT EXISTS stock_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    user_id INTEGER,
    type TEXT DEFAULT 'adjustment',
    quantity_change REAL NOT NULL,
    reason TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(product_id) REFERENCES products(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Expenses table
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    date TEXT NOT NULL,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Expense Categories table
CREATE TABLE IF NOT EXISTS expense_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    is_active INTEGER DEFAULT 1
);

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT
);

-- Held Orders table
CREATE TABLE IF NOT EXISTS held_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_data_json TEXT NOT NULL,
    customer_id INTEGER,
    user_id INTEGER,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Returns table
CREATE TABLE IF NOT EXISTS returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    user_id INTEGER,
    items_json TEXT NOT NULL,
    total_refund REAL NOT NULL DEFAULT 0.0,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Activity Log table
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    detail TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- End of Day (EOD) Reports table
CREATE TABLE IF NOT EXISTS eod_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT NOT NULL,
    total_sales REAL NOT NULL DEFAULT 0.0,
    total_orders INTEGER NOT NULL DEFAULT 0,
    expected_cash REAL NOT NULL DEFAULT 0.0,
    actual_cash REAL NOT NULL DEFAULT 0.0,
    difference REAL NOT NULL DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Fast search indexes
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_cat ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_num ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);
CREATE INDEX IF NOT EXISTS idx_activity_date ON activity_log(created_at);
"""

@contextmanager
def get_db(db_path: str = None):
    """Context manager for SQLite connections with row factory enabled."""
    target_path = db_path or DB_PATH
    conn = sqlite3.connect(target_path, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def _run_migrations(conn):
    """Safely apply column additions if migrating an existing database."""
    cursor = conn.cursor()
    migrations = [
        ("products", "parent_product_id", "INTEGER"),
        ("products", "is_favorite", "INTEGER DEFAULT 0"),
        ("categories", "color_hex", "TEXT DEFAULT '#4F46E5'"),
        ("customers", "loyalty_points", "REAL DEFAULT 0.0"),
        ("orders", "cost_total", "REAL DEFAULT 0.0"),
        ("orders", "profit", "REAL DEFAULT 0.0"),
        ("order_items", "price_override", "INTEGER DEFAULT 0"),
        ("order_items", "override_reason", "TEXT"),
        ("stock_adjustments", "type", "TEXT DEFAULT 'adjustment'"),
        ("activity_log", "entity_type", "TEXT"),
        ("activity_log", "entity_id", "INTEGER")
    ]
    for table, col, col_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass # Column already exists

def init_database(db_path: str = None):
    """Initialize database tables, indexes, migrations, and seed default data."""
    target_path = db_path or DB_PATH
    is_first_run = not os.path.exists(target_path)

    with get_db(target_path) as conn:
        conn.executescript(SCHEMA_SQL)
        _run_migrations(conn)
        
        cursor = conn.cursor()

        # Seed default users
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            admin_pwd = hash_password("admin")
            cashier_pwd = hash_password("cashier")
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                ("admin", admin_pwd, "System Administrator", "Admin")
            )
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                ("cashier", cashier_pwd, "Default Cashier", "Cashier")
            )

        # Seed default categories
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            default_categories = ["General", "Beverages", "Snacks", "Groceries", "Household", "Personal Care"]
            for idx, cat_name in enumerate(default_categories, start=1):
                cursor.execute(
                    "INSERT INTO categories (name, sort_order) VALUES (?, ?)",
                    (cat_name, idx)
                )

        # Seed default settings
        cursor.execute("SELECT COUNT(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            default_settings = {
                "business_name": "OnesDev POS Store",
                "business_address": "123 Main Commercial Boulevard",
                "business_phone": "0300-1234567",
                "business_email": "store@onesdev.local",
                "tax_number": "TR-10029384",
                "currency_symbol": "Rs",
                "currency_position": "before",
                "decimal_places": "2",
                "thousand_separator": ",",
                "enable_tax": "0",
                "tax_name": "VAT",
                "tax_percentage": "0",
                "tax_type": "exclusive",
                "receipt_header": "Welcome to OnesDev POS Store",
                "receipt_footer": "Thank you for shopping with us!\nReturn within 7 days with receipt.",
                "receipt_width": "80mm",
                "auto_print": "0",
                "printer_name": "Default",
                "sound_enabled": "1",
                "language": "en",
                "theme_mode": "light",
                "loyalty_rate": "100", # spend 100 to earn 1 pt
                "loyalty_point_val": "1.0", # 1 pt = 1 currency unit
                "setup_completed": "0"
            }
            cursor.executemany(
                "INSERT INTO settings (key, value) VALUES (?, ?)",
                list(default_settings.items())
            )

    return is_first_run
