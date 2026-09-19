import os
import sys
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pos_app.database import init_database, get_db
from pos_app.models.category_model import CategoryModel
from pos_app.models.customer_model import CustomerModel
from pos_app.models.supplier_model import SupplierModel
from pos_app.models.product_model import ProductModel
from pos_app.models.order_model import OrderModel
from pos_app.models.expense_model import ExpenseModel

REALISTIC_CATALOG = [
    # Category: Beverages
    ("Mineral Water 500ml", "BEV-001", "890100100001", "Beverages", "bottle", 30.0, 50.0, 42.0, 20.0, 150.0),
    ("Mineral Water 1.5L", "BEV-002", "890100100002", "Beverages", "bottle", 60.0, 90.0, 80.0, 15.0, 85.0),
    ("Coca Cola Can 250ml", "BEV-003", "890100100003", "Beverages", "can", 70.0, 100.0, 88.0, 24.0, 120.0),
    ("Sprite Can 250ml", "BEV-004", "890100100004", "Beverages", "can", 70.0, 100.0, 88.0, 24.0, 95.0),
    ("Pepsi 1.5L Bottle", "BEV-005", "890100100005", "Beverages", "bottle", 130.0, 180.0, 160.0, 10.0, 45.0),
    ("Fresh Orange Juice 1L", "BEV-006", "890100100006", "Beverages", "bottle", 220.0, 320.0, 280.0, 8.0, 30.0),
    ("Energy Drink 250ml", "BEV-007", "890100100007", "Beverages", "can", 190.0, 280.0, 250.0, 12.0, 60.0),
    ("Green Tea Bag Pack 50s", "BEV-008", "890100100008", "Beverages", "pack", 340.0, 480.0, 420.0, 10.0, 40.0),

    # Category: Snacks & Confectionery
    ("Lays Masala Chips 65g", "SNK-001", "890200100001", "Snacks", "pack", 60.0, 90.0, 78.0, 20.0, 80.0),
    ("Lays Wavy BBQ 65g", "SNK-002", "890200100002", "Snacks", "pack", 60.0, 90.0, 78.0, 20.0, 70.0),
    ("Kurkure Chutney Chaska", "SNK-003", "890200100003", "Snacks", "pack", 35.0, 50.0, 42.0, 30.0, 110.0),
    ("Dairy Milk Silk 60g", "SNK-004", "890200100004", "Snacks", "piece", 150.0, 220.0, 195.0, 15.0, 45.0),
    ("KitKat 4 Finger 41g", "SNK-005", "890200100005", "Snacks", "piece", 120.0, 180.0, 155.0, 20.0, 55.0),
    ("Salted Peanuts 100g", "SNK-006", "890200100006", "Snacks", "pack", 80.0, 120.0, 105.0, 10.0, 35.0),
    ("Chocolate Chip Cookies", "SNK-007", "890200100007", "Snacks", "box", 110.0, 160.0, 140.0, 12.0, 60.0),

    # Category: Groceries & Staples
    ("Super Basmati Rice 1kg", "GRO-001", "890300100001", "Groceries", "kg", 240.0, 340.0, 300.0, 25.0, 180.0),
    ("Super Basmati Rice 5kg Bag", "GRO-002", "890300100002", "Groceries", "bag", 1150.0, 1600.0, 1450.0, 10.0, 50.0),
    ("Premium Cooking Oil 1L", "GRO-003", "890300100003", "Groceries", "bottle", 380.0, 510.0, 460.0, 20.0, 90.0),
    ("Fine Wheat Flour 10kg", "GRO-004", "890300100004", "Groceries", "bag", 950.0, 1300.0, 1180.0, 15.0, 75.0),
    ("White Refined Sugar 1kg", "GRO-005", "890300100005", "Groceries", "kg", 110.0, 150.0, 135.0, 30.0, 220.0),
    ("Iodized Table Salt 800g", "GRO-006", "890300100006", "Groceries", "pack", 40.0, 60.0, 50.0, 25.0, 140.0),
    ("Red Chili Powder 200g", "GRO-007", "890300100007", "Groceries", "pack", 160.0, 230.0, 200.0, 10.0, 45.0),
    ("Turmeric Powder 200g", "GRO-008", "890300100008", "Groceries", "pack", 140.0, 200.0, 175.0, 10.0, 40.0),

    # Category: Personal Care & Pharmacy
    ("Antibacterial Hand Soap 100g", "PER-001", "890400100001", "Personal Care", "piece", 75.0, 110.0, 95.0, 20.0, 85.0),
    ("Herbal Shampoo 360ml", "PER-002", "890400100002", "Personal Care", "bottle", 360.0, 520.0, 460.0, 10.0, 40.0),
    ("Fluoride Toothpaste 140g", "PER-003", "890400100003", "Personal Care", "piece", 140.0, 210.0, 185.0, 15.0, 65.0),
    ("Soft Bristle Toothbrush", "PER-004", "890400100004", "Personal Care", "piece", 60.0, 95.0, 80.0, 20.0, 90.0),
    ("Hand Sanitizer Gel 100ml", "PER-005", "890400100005", "Personal Care", "bottle", 85.0, 130.0, 110.0, 15.0, 55.0),
    ("Paracetamol Tablets 500mg (10s)", "PER-006", "890400100006", "Pharmacy", "strip", 20.0, 35.0, 28.0, 50.0, 250.0),
    ("First Aid Bandages Box (50s)", "PER-007", "890400100007", "Pharmacy", "box", 120.0, 190.0, 160.0, 10.0, 45.0),

    # Category: Electronics & Accessories
    ("USB-C Fast Charging Cable 1m", "ELE-001", "890500100001", "Electronics", "piece", 180.0, 350.0, 280.0, 15.0, 60.0),
    ("Wireless Optical Mouse", "ELE-002", "890500100002", "Electronics", "piece", 650.0, 1150.0, 950.0, 8.0, 25.0),
    ("In-Ear Stereo Earphones 3.5mm", "ELE-003", "890500100003", "Electronics", "piece", 220.0, 450.0, 360.0, 10.0, 40.0),
    ("USB 3.0 Flash Drive 32GB", "ELE-004", "890500100004", "Electronics", "piece", 720.0, 1250.0, 1050.0, 10.0, 35.0),
    ("Universal Travel Power Adapter", "ELE-005", "890500100005", "Electronics", "piece", 480.0, 850.0, 700.0, 6.0, 18.0),
    ("AA Alkaline Batteries (4-Pack)", "ELE-006", "890500100006", "Electronics", "pack", 160.0, 280.0, 230.0, 15.0, 50.0),

    # Category: Stationery
    ("Gel Ink Pen Blue 0.7mm", "STA-001", "890600100001", "Stationery", "piece", 25.0, 45.0, 35.0, 50.0, 300.0),
    ("A4 Copy Paper Ream 500s", "STA-002", "890600100002", "Stationery", "ream", 850.0, 1200.0, 1050.0, 10.0, 45.0),
    ("Spiral Notebook 200 Pages", "STA-003", "890600100003", "Stationery", "piece", 120.0, 190.0, 160.0, 15.0, 70.0),
    ("Stapler with Pin Box", "STA-004", "890600100004", "Stationery", "piece", 180.0, 300.0, 250.0, 8.0, 30.0),

    # Low Stock Items for alerting testing
    ("Specialty Green Coffee 250g", "BEV-009", "890100100009", "Beverages", "pack", 450.0, 680.0, 590.0, 10.0, 2.0),
    ("Premium Olive Oil 500ml", "GRO-009", "890300100009", "Groceries", "bottle", 850.0, 1350.0, 1150.0, 8.0, 3.0),
    ("Wireless Bluetooth Keyboard", "ELE-007", "890500100007", "Electronics", "piece", 1400.0, 2400.0, 2000.0, 5.0, 1.0)
]

def clean_old_data():
    """Removes all old testing products, orders, customers, and test artifacts."""
    print("Clearing old test records and resetting data tables...")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF;")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('users', 'settings', 'sqlite_sequence')")
        tables = [r[0] for r in cursor.fetchall()]
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            try:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
            except Exception:
                pass
        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON;")
    print("Old test records removed successfully.")

def seed_data(extra_stress_count: int = 0):
    print("Initializing database...")
    init_database()
    clean_old_data()

    from pos_app.models.settings_model import SettingsModel
    SettingsModel.set("business_name", "OnesDev POS Store")
    SettingsModel.set("receipt_header", "Welcome to OnesDev POS Store")
    SettingsModel.set("receipt_footer", "Thank you for shopping with us!\nReturn within 7 days with receipt.")
    SettingsModel.set("desktop_shortcut_created", "1")

    print("Seeding suppliers...")
    suppliers = [
        ("Metro Cash & Carry Wholesale", "042-111-786-786", "wholesale@metro.com", "Raiwind Road, Lahore"),
        ("Al-Madina FMCG Distributors", "0300-9876543", "orders@almadina.pk", "Main Commercial Market"),
        ("Global Tech & Accessories Import", "0321-4567890", "sales@globaltech.pk", "Electronics Plaza"),
        ("Universal Foods & Staples Ltd", "021-34567890", "info@universalfoods.com", "Industrial Estate")
    ]
    for s in suppliers:
        SupplierModel.create(s[0], s[1], s[2], s[3])

    print("Seeding customers...")
    customers = [
        ("Ali Khan", "0300-1112233", "ali.khan@gmail.com", "House 12, Street 4, Sector G-9", "", 0.0),
        ("Fatima Noor", "0322-3344556", "fatima.noor@yahoo.com", "Apartment 4B, Silver Heights", "", 0.0),
        ("Bilal Ahmed (Regular Khata)", "0333-7788990", "bilal.ahmed@live.com", "Shop 5, Main Bazar", "Pays at end of month", 4500.0),
        ("Usman Tariq", "0345-6677889", "usman.tariq@outlook.com", "Commercial Area", "", 0.0),
        ("Zainab Bibi", "0312-4455667", "zainab.b@gmail.com", "Block C, Phase 2", "", 1200.0)
    ]
    cust_ids = []
    for c in customers:
        cid = CustomerModel.create(c[0], c[1], c[2], c[3], c[4], c[5])
        cust_ids.append(cid)

    print("Seeding categories & products catalog...")
    cat_map = {}
    for item in REALISTIC_CATALOG:
        name, sku, barcode, cat_name, unit, cost, sell, wholesale, min_s, stock = item
        if cat_name not in cat_map:
            cat_map[cat_name] = CategoryModel.get_or_create(cat_name)
        cat_id = cat_map[cat_name]

        existing = ProductModel.get_by_barcode_or_sku(barcode) or ProductModel.get_by_barcode_or_sku(sku)
        if not existing:
            ProductModel.create({
                "name": name,
                "sku": sku,
                "barcode": barcode,
                "category_id": cat_id,
                "unit": unit,
                "cost_price": cost,
                "selling_price": sell,
                "wholesale_price": wholesale,
                "min_stock": min_s,
                "current_stock": stock,
                "description": f"Quality {name}",
                "is_active": 1
            })

    # Extra stress testing products if requested
    if extra_stress_count > 0:
        print(f"Generating {extra_stress_count} stress-test products...")
        prefixes = ["Super", "Classic", "Deluxe", "Organic", "Golden", "Pure", "Royal", "Speedy", "Mega", "Compact"]
        items_base = ["Biscuits", "Shampoo", "Soap", "Juice", "Notebook", "Battery", "Cleaner", "Bulb", "Towel", "Detergent"]
        cats_list = list(cat_map.values())

        with get_db() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            batch = []
            for i in range(1, extra_stress_count + 1):
                p_name = f"{random.choice(prefixes)} {random.choice(items_base)} {i}"
                sku = f"GEN-{i:05d}"
                bar = f"99{i:010d}"
                cid = random.choice(cats_list)
                cost = round(random.uniform(20.0, 500.0), 2)
                sell = round(cost * random.uniform(1.2, 1.6), 2)
                stock = random.randint(5, 250)
                batch.append((p_name, sku, bar, cid, "piece", cost, sell, sell*0.9, 5.0, stock, "", 1, now, now))

            cursor.executemany("""
                INSERT INTO products (name, sku, barcode, category_id, unit, cost_price, selling_price, wholesale_price, min_stock, current_stock, description, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
        print(f"Stress test catalog loaded ({extra_stress_count} products added).")

    print("Seeding sample historical sales...")
    prods = ProductModel.search_products(limit=25)
    today = datetime.now()

    # Generate 15 sample completed orders across today and yesterday
    for i in range(1, 16):
        order_num = f"ORD-{today.strftime('%Y%m%d')}-{i:04d}"
        days_ago = 1 if i <= 5 else 0
        order_time = (today - timedelta(days=days_ago, hours=random.randint(1, 8), minutes=random.randint(5, 55))).strftime("%Y-%m-%d %H:%M:%S")

        sel_prods = random.sample(prods, k=random.randint(2, 4))
        items = []
        subtotal = 0.0
        for p in sel_prods:
            qty = random.randint(1, 3)
            price = p["selling_price"]
            tot = round(qty * price, 2)
            subtotal += tot
            items.append({
                "product_id": p["id"],
                "product_name": p["name"],
                "quantity": qty,
                "unit_price": price,
                "discount": 0.0,
                "total": tot,
                "cost_price": p["cost_price"]
            })

        disc = 50.0 if subtotal > 1000 and i % 3 == 0 else 0.0
        grand_total = subtotal - disc
        method = "cash" if i % 3 != 0 else ("split" if i % 2 == 0 else "credit")
        cust_id = random.choice(cust_ids) if method == "credit" or i % 2 == 0 else None

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO orders (
                    order_number, customer_id, user_id, subtotal, discount_amount, discount_percent,
                    tax_amount, total, amount_paid, change_due, payment_method, payment_status, note, status, created_at
                ) VALUES (?, ?, 1, ?, ?, 0.0, 0.0, ?, ?, ?, ?, 'paid', '', 'completed', ?)
            """, (order_num, cust_id, subtotal, disc, grand_total, grand_total, 0.0, method, order_time))
            oid = cursor.lastrowid
            if oid:
                for itm in items:
                    cursor.execute("""
                        INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, discount, total, cost_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (oid, itm["product_id"], itm["product_name"], itm["quantity"], itm["unit_price"], itm["discount"], itm["total"], itm["cost_price"]))

    print("Seeding sample shop operating expenses...")
    today_str = today.strftime("%Y-%m-%d")
    ExpenseModel.create("Store Supplies", 1500.0, "Thermal receipt paper rolls & packaging bags", today_str, 1)
    ExpenseModel.create("Electricity & Utilities", 8500.0, "Monthly commercial electricity bill", today_str, 1)
    ExpenseModel.create("Transport & Fuel", 1200.0, "Stock delivery fuel expense", today_str, 1)

    # Sync seeded database to dist/pos_data.db for the standalone binary
    import shutil
    from pos_app.config import DB_PATH, APP_DIR
    dist_db = os.path.join(BASE_DIR, "dist", "pos_data.db")
    if os.path.exists(os.path.join(BASE_DIR, "dist")):
        shutil.copy2(DB_PATH, dist_db)
        print(f"Synced demo database to: {dist_db}")

    print("[SUCCESS] Clean retail demo data seeded successfully!")

if __name__ == "__main__":
    stress = 5000 if "--stress-test-5000" in sys.argv else 0
    seed_data(extra_stress_count=stress)

