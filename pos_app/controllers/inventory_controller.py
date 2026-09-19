from pos_app.models.inventory_model import InventoryModel
from pos_app.models.purchase_model import PurchaseModel
from pos_app.models.supplier_model import SupplierModel
from pos_app.models.product_model import ProductModel
from pos_app.models.activity_model import ActivityModel
from pos_app.controllers.auth_controller import AuthController

class InventoryController:
    @staticmethod
    def adjust_stock(product_id: int, quantity_change: float, reason: str, note: str = "") -> tuple[bool, str]:
        user = AuthController.get_current_user()
        user_id = user["id"] if user else 1

        product = ProductModel.get_by_id(product_id)
        if not product:
            return False, "Product not found"

        adjust_id = InventoryModel.adjust_stock(product_id, user_id, quantity_change, reason, note)
        ActivityModel.log(user_id, "STOCK_ADJUST", f"Stock adjusted for {product['name']}: {quantity_change:+g} units ({reason})")
        return True, "Stock adjusted successfully"

    @staticmethod
    def receive_purchase(supplier_id: int, items: list, note: str = "") -> tuple[bool, str, int]:
        if not items:
            return False, "No items in purchase order", 0

        user = AuthController.get_current_user()
        user_id = user["id"] if user else 1

        total_amount = sum(float(i["total"]) for i in items)
        purchase_id = PurchaseModel.create_purchase(supplier_id, user_id, total_amount, note, items)
        ActivityModel.log(user_id, "PURCHASE_RECEIVE", f"Received purchase #{purchase_id} with {len(items)} items, total: {total_amount:,.2f}")
        return True, f"Purchase #{purchase_id} received and stock updated", purchase_id

    @staticmethod
    def get_stock_valuation():
        return ProductModel.get_stock_valuation()

    @staticmethod
    def get_low_stock_items(limit: int = 50):
        return ProductModel.get_low_stock_products(limit)
