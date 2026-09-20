"""
Cart Controller for managing active Point of Sale shopping cart items,
line item adjustments, discounts, and held tickets.
"""
from typing import List, Dict, Any


class CartController:
    """Manages active shopping cart state and calculation pipeline."""

    def __init__(self):
        self._items: Dict[int, Dict[str, Any]] = {}
        self._discount: float = 0.0
        self._held_orders: List[Dict[str, Any]] = []

    def add_item(self, product_id: int, name: str, price: float, cost_price: float = 0.0, quantity: int = 1, unit: str = "pc"):
        if product_id in self._items:
            self._items[product_id]["quantity"] += quantity
        else:
            self._items[product_id] = {
                "product_id": product_id,
                "name": name,
                "price": float(price),
                "cost_price": float(cost_price),
                "quantity": int(quantity),
                "unit": unit
            }

    def adjust_quantity(self, product_id: int, delta: int):
        if product_id in self._items:
            self._items[product_id]["quantity"] += delta
            if self._items[product_id]["quantity"] <= 0:
                del self._items[product_id]

    def remove_item(self, product_id: int):
        self._items.pop(product_id, None)

    def get_items(self) -> List[Dict[str, Any]]:
        return list(self._items.values())

    def get_subtotal(self) -> float:
        return sum(item["price"] * item["quantity"] for item in self._items.values())

    def set_discount(self, val: float):
        self._discount = max(0.0, float(val))

    def get_discount(self) -> float:
        return self._discount

    def get_grand_total(self) -> float:
        subtotal = self.get_subtotal()
        return max(0.0, subtotal - self._discount)

    def clear(self):
        self._items.clear()
        self._discount = 0.0

    def hold_current_order(self):
        if self._items:
            self._held_orders.append({
                "items": list(self._items.values()),
                "discount": self._discount
            })

    def get_held_orders(self) -> List[Dict[str, Any]]:
        return self._held_orders
