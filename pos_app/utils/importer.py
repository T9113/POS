import csv
import os
from pos_app.models.product_model import ProductModel
from pos_app.models.category_model import CategoryModel

class ProductImporter:
    @staticmethod
    def import_file(file_path: str) -> dict:
        """
        Imports products from a CSV or Excel (.xlsx) file.
        Returns dict with imported, updated, errors count.
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            return ProductImporter._import_csv(file_path)
        elif ext in [".xlsx", ".xls"]:
            return ProductImporter._import_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Please provide a .csv or .xlsx file.")

    @staticmethod
    def _normalize_header(header: str) -> str:
        h = header.strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "product_name": "name",
            "title": "name",
            "item_name": "name",
            "code": "sku",
            "product_code": "sku",
            "bar_code": "barcode",
            "upc": "barcode",
            "ean": "barcode",
            "cat": "category",
            "category_name": "category",
            "cost": "cost_price",
            "purchase_price": "cost_price",
            "buy_price": "cost_price",
            "price": "selling_price",
            "sale_price": "selling_price",
            "retail_price": "selling_price",
            "stock": "current_stock",
            "quantity": "current_stock",
            "qty": "current_stock",
            "min_level": "min_stock",
            "minimum_stock": "min_stock",
            "desc": "description"
        }
        return aliases.get(h, h)

    @staticmethod
    def _process_records(records: list[dict]) -> dict:
        imported = 0
        updated = 0
        errors = []

        category_cache = {}

        for idx, row in enumerate(records, start=2): # Line 2 accounting for header
            name = str(row.get("name") or "").strip()
            if not name:
                errors.append(f"Row {idx}: Missing product name, skipped.")
                continue

            category_name = str(row.get("category") or "General").strip()
            if category_name not in category_cache:
                category_id = CategoryModel.get_or_create(category_name)
                category_cache[category_name] = category_id
            else:
                category_id = category_cache[category_name]

            sku = str(row.get("sku") or "").strip() or None
            barcode = str(row.get("barcode") or "").strip() or None

            try:
                cost_price = float(row.get("cost_price") or 0.0)
                selling_price = float(row.get("selling_price") or 0.0)
                wholesale_price = float(row.get("wholesale_price") or 0.0)
                min_stock = float(row.get("min_stock") or 5.0)
                current_stock = float(row.get("current_stock") or 0.0)
            except ValueError as e:
                errors.append(f"Row {idx} ({name}): Number parsing error - {e}")
                continue

            unit = str(row.get("unit") or "piece").strip()
            description = str(row.get("description") or "").strip()

            product_data = {
                "name": name,
                "sku": sku,
                "barcode": barcode,
                "category_id": category_id,
                "unit": unit,
                "cost_price": cost_price,
                "selling_price": selling_price,
                "wholesale_price": wholesale_price,
                "min_stock": min_stock,
                "current_stock": current_stock,
                "description": description,
                "is_active": 1
            }

            # Check existing by barcode or sku
            existing = None
            if barcode:
                existing = ProductModel.get_by_barcode_or_sku(barcode)
            if not existing and sku:
                existing = ProductModel.get_by_barcode_or_sku(sku)

            if existing:
                ProductModel.update(existing["id"], product_data)
                updated += 1
            else:
                ProductModel.create(product_data)
                imported += 1

        return {
            "imported": imported,
            "updated": updated,
            "failed": len(errors),
            "errors": errors
        }

    @staticmethod
    def _import_csv(file_path: str) -> dict:
        records = []
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = [ProductImporter._normalize_header(h) for h in next(reader, [])]
            for row in reader:
                if not any(row):
                    continue
                record = {}
                for h, val in zip(headers, row):
                    record[h] = val
                records.append(record)
        return ProductImporter._process_records(records)

    @staticmethod
    def _import_excel(file_path: str) -> dict:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        records = []
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return {"imported": 0, "updated": 0, "failed": 0, "errors": ["File is empty."]}
        
        headers = [ProductImporter._normalize_header(str(h or "")) for h in rows[0]]
        for row in rows[1:]:
            if not any(row):
                continue
            record = {}
            for h, val in zip(headers, row):
                record[h] = val
            records.append(record)
        return ProductImporter._process_records(records)
