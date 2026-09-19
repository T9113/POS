from pos_app.models.order_model import OrderModel
from pos_app.models.product_model import ProductModel
from pos_app.models.customer_model import CustomerModel
from pos_app.models.settings_model import SettingsModel
from pos_app.models.activity_model import ActivityModel
from pos_app.controllers.auth_controller import AuthController

class POSController:
    def __init__(self):
        self.cart_items = {} # key: product_id -> dict
        self.selected_customer = None
        self.order_discount_amount = 0.0
        self.order_discount_percent = 0.0
        self.order_note = ""

    def clear_cart(self):
        self.cart_items.clear()
        self.selected_customer = None
        self.order_discount_amount = 0.0
        self.order_discount_percent = 0.0
        self.order_note = ""

    def set_customer(self, customer_dict: dict = None):
        self.selected_customer = customer_dict

    def add_product_by_code(self, code: str, qty: float = 1.0) -> tuple[bool, str]:
        """Looks up product by barcode or SKU and adds to cart."""
        product = ProductModel.get_by_barcode_or_sku(code)
        if not product:
            return False, f"No product found with code '{code}'"
        return self.add_product(product, qty)

    def add_product(self, product: dict, qty: float = 1.0) -> tuple[bool, str]:
        pid = product["id"]
        if pid in self.cart_items:
            self.cart_items[pid]["quantity"] += qty
        else:
            self.cart_items[pid] = {
                "product_id": pid,
                "product_name": product["name"],
                "unit_price": float(product["selling_price"]),
                "cost_price": float(product.get("cost_price", 0.0)),
                "quantity": float(qty),
                "discount": 0.0,
                "unit": product.get("unit", "piece"),
                "max_stock": float(product.get("current_stock", 999999))
            }
        self._recalc_item(pid)
        return True, f"Added {product['name']} to cart"

    def update_quantity(self, product_id: int, quantity: float):
        if product_id in self.cart_items:
            if quantity <= 0:
                self.remove_item(product_id)
            else:
                self.cart_items[product_id]["quantity"] = float(quantity)
                self._recalc_item(product_id)

    def change_quantity(self, product_id: int, delta: float):
        if product_id in self.cart_items:
            new_qty = self.cart_items[product_id]["quantity"] + delta
            self.update_quantity(product_id, new_qty)

    def remove_item(self, product_id: int):
        if product_id in self.cart_items:
            del self.cart_items[product_id]

    def set_item_discount(self, product_id: int, discount_value: float, is_percentage: bool = False):
        if product_id in self.cart_items:
            item = self.cart_items[product_id]
            price = item["unit_price"]
            if is_percentage:
                item["discount"] = round((price * discount_value) / 100.0, 2)
            else:
                item["discount"] = min(price, float(discount_value))
            self._recalc_item(product_id)

    def _recalc_item(self, product_id: int):
        item = self.cart_items[product_id]
        net_price = max(0.0, item["unit_price"] - item["discount"])
        item["total"] = round(net_price * item["quantity"], 2)

    def set_order_discount(self, value: float, is_percentage: bool = False):
        if is_percentage:
            self.order_discount_percent = float(value)
            self.order_discount_amount = 0.0
        else:
            self.order_discount_amount = float(value)
            self.order_discount_percent = 0.0

    def get_summary(self) -> dict:
        settings = SettingsModel.get_all()
        enable_tax = settings.get("enable_tax", "0") == "1"
        tax_pct = float(settings.get("tax_percentage", "0")) if enable_tax else 0.0
        tax_type = settings.get("tax_type", "exclusive")

        subtotal = sum(item["total"] for item in self.cart_items.values())
        
        # Calculate bill discount
        bill_discount = 0.0
        if self.order_discount_percent > 0:
            bill_discount = round((subtotal * self.order_discount_percent) / 100.0, 2)
        elif self.order_discount_amount > 0:
            bill_discount = min(subtotal, self.order_discount_amount)

        net_subtotal = max(0.0, subtotal - bill_discount)

        # Tax calculation
        tax_amount = 0.0
        if enable_tax and tax_pct > 0:
            if tax_type == "inclusive":
                # Price includes tax: Tax = Subtotal - (Subtotal / (1 + rate))
                tax_amount = round(net_subtotal - (net_subtotal / (1.0 + (tax_pct / 100.0))), 2)
                grand_total = round(net_subtotal, 2)
            else:
                # Exclusive: Tax is added on top
                tax_amount = round((net_subtotal * tax_pct) / 100.0, 2)
                grand_total = round(net_subtotal + tax_amount, 2)
        else:
            grand_total = round(net_subtotal, 2)

        return {
            "subtotal": round(subtotal, 2),
            "discount_amount": bill_discount,
            "discount_percent": self.order_discount_percent,
            "tax_amount": tax_amount,
            "grand_total": grand_total,
            "total_items": len(self.cart_items),
            "total_units": sum(item["quantity"] for item in self.cart_items.values())
        }

    def hold_current_order(self, note: str = "") -> tuple[bool, str]:
        if not self.cart_items:
            return False, "Cannot hold an empty cart"
        
        user = AuthController.get_current_user()
        user_id = user["id"] if user else None
        cust_id = self.selected_customer["id"] if self.selected_customer else None

        cart_data = {
            "items": list(self.cart_items.values()),
            "discount_amount": self.order_discount_amount,
            "discount_percent": self.order_discount_percent,
            "note": note or self.order_note
        }

        held_id = OrderModel.hold_order(cart_data, cust_id, user_id, note)
        self.clear_cart()
        return True, f"Order #{held_id} placed on hold"

    def recall_held_order(self, held_id: int) -> tuple[bool, str]:
        held_orders = OrderModel.list_held_orders()
        target = next((h for h in held_orders if h["id"] == held_id), None)
        if not target:
            return False, "Held order not found"

        self.clear_cart()
        cart_data = target["cart_data"]
        for itm in cart_data.get("items", []):
            self.cart_items[itm["product_id"]] = itm

        self.order_discount_amount = float(cart_data.get("discount_amount", 0.0))
        self.order_discount_percent = float(cart_data.get("discount_percent", 0.0))
        self.order_note = cart_data.get("note", "")

        if target.get("customer_id"):
            self.selected_customer = CustomerModel.get_by_id(target["customer_id"])

        # Delete from held table
        OrderModel.delete_held_order(held_id)
        return True, f"Held order #{held_id} restored to cart"

    def checkout(self, payment_method: str, amount_paid: float, note: str = "") -> tuple[bool, str, dict]:
        """
        Executes order checkout, records in database, decrements inventory stock.
        Returns (success: bool, message: str, order_details: dict)
        """
        if not self.cart_items:
            return False, "Cart is empty. Add products before checkout.", {}

        summary = self.get_summary()
        grand_total = summary["grand_total"]
        user = AuthController.get_current_user()
        user_id = user["id"] if user else 1

        # Calculate change due
        if payment_method in ["cash", "card", "split"]:
            change_due = max(0.0, amount_paid - grand_total)
        else: # credit/due
            change_due = 0.0

        payment_status = "paid" if amount_paid >= grand_total else "partial"
        if payment_method == "credit":
            payment_status = "credit"

        cust_id = self.selected_customer["id"] if self.selected_customer else None

        order_data = {
            "customer_id": cust_id,
            "user_id": user_id,
            "subtotal": summary["subtotal"],
            "discount_amount": summary["discount_amount"],
            "discount_percent": summary["discount_percent"],
            "tax_amount": summary["tax_amount"],
            "total": grand_total,
            "amount_paid": amount_paid,
            "change_due": change_due,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "note": note or self.order_note,
            "status": "completed"
        }

        items = list(self.cart_items.values())
        order_id, order_number = OrderModel.create_order(order_data, items)

        # Log activity
        ActivityModel.log(user_id, "NEW_SALE", f"Completed order {order_number} for {grand_total:,.2f}")

        # Retrieve complete recorded order for receipt printing
        full_order = OrderModel.get_order_by_id(order_id)
        self.clear_cart()

        return True, f"Sale completed: {order_number}", full_order
