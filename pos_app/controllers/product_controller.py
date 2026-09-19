from pos_app.models.product_model import ProductModel
from pos_app.models.category_model import CategoryModel
from pos_app.models.activity_model import ActivityModel
from pos_app.controllers.auth_controller import AuthController
from pos_app.utils.importer import ProductImporter
from pos_app.utils.exporter import Exporter

class ProductController:
    @staticmethod
    def get_product(product_id: int):
        return ProductModel.get_by_id(product_id)

    @staticmethod
    def search(query: str = "", category_id: int = None, limit: int = 50, offset: int = 0, sort_by: str = "name", sort_order: str = "ASC"):
        return ProductModel.search_products(query, category_id, active_only=True, limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order)

    @staticmethod
    def count(query: str = "", category_id: int = None):
        return ProductModel.count_products(query, category_id, active_only=True)

    @staticmethod
    def save_product(product_data: dict, product_id: int = None) -> tuple[bool, str, int]:
        name = product_data.get("name", "").strip()
        if not name:
            return False, "Product name is required", 0

        user = AuthController.get_current_user()
        user_id = user["id"] if user else None

        if product_id:
            ok = ProductModel.update(product_id, product_data)
            if ok:
                ActivityModel.log(user_id, "PRODUCT_EDIT", f"Updated product #{product_id}: {name}")
                return True, "Product updated successfully", product_id
            return False, "Failed to update product", 0
        else:
            new_id = ProductModel.create(product_data)
            ActivityModel.log(user_id, "PRODUCT_ADD", f"Created product #{new_id}: {name}")
            return True, "Product created successfully", new_id

    @staticmethod
    def delete_product(product_id: int) -> tuple[bool, str]:
        product = ProductModel.get_by_id(product_id)
        if not product:
            return False, "Product not found"
        ok = ProductModel.soft_delete(product_id)
        if ok:
            user = AuthController.get_current_user()
            user_id = user["id"] if user else None
            ActivityModel.log(user_id, "PRODUCT_DELETE", f"Soft deleted product #{product_id}: {product['name']}")
            return True, "Product deleted successfully"
        return False, "Failed to delete product"

    @staticmethod
    def bulk_update_prices(product_ids: list, adjust_type: str, value: float) -> tuple[bool, str]:
        if not product_ids:
            return False, "No products selected"
        count = ProductModel.bulk_update_prices(product_ids, adjust_type, value)
        user = AuthController.get_current_user()
        user_id = user["id"] if user else None
        ActivityModel.log(user_id, "PRICE_UPDATE", f"Bulk updated prices for {count} products ({adjust_type} {value})")
        return True, f"Successfully updated prices for {count} products"

    @staticmethod
    def import_from_file(file_path: str) -> dict:
        return ProductImporter.import_file(file_path)

    @staticmethod
    def export_products_excel(filename: str = "products_catalog.xlsx") -> str:
        products = ProductModel.get_all_for_export()
        headers = ["ID", "Product Name", "SKU", "Barcode", "Category", "Unit", "Cost Price", "Selling Price", "Wholesale Price", "Min Stock", "Current Stock", "Description", "Active"]
        rows = [
            [
                p["id"], p["name"], p["sku"] or "", p["barcode"] or "", p["category"] or "",
                p["unit"], p["cost_price"], p["selling_price"], p["wholesale_price"],
                p["min_stock"], p["current_stock"], p["description"] or "", "Yes" if p["is_active"] else "No"
            ]
            for p in products
        ]
        return Exporter.export_excel(filename, "Product Catalog", headers, rows)
