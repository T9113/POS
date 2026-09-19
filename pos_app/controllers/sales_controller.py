from pos_app.models.order_model import OrderModel
from pos_app.models.activity_model import ActivityModel
from pos_app.controllers.auth_controller import AuthController
from pos_app.utils.receipt_printer import ReceiptPrinter

class SalesController:
    @staticmethod
    def list_orders(query: str = "", date_from: str = None, date_to: str = None, payment_method: str = None, limit: int = 50, offset: int = 0):
        return OrderModel.list_orders(query, date_from, date_to, payment_method, limit, offset)

    @staticmethod
    def count_orders(query: str = "", date_from: str = None, date_to: str = None, payment_method: str = None):
        return OrderModel.count_orders(query, date_from, date_to, payment_method)

    @staticmethod
    def get_order(order_id: int):
        return OrderModel.get_order_by_id(order_id)

    @staticmethod
    def process_refund(order_id: int, returned_items: list, total_refund: float, reason: str) -> tuple[bool, str]:
        user = AuthController.get_current_user()
        user_id = user["id"] if user else 1

        order = OrderModel.get_order_by_id(order_id)
        if not order:
            return False, "Order not found"

        return_id = OrderModel.process_return(order_id, user_id, returned_items, total_refund, reason)
        ActivityModel.log(user_id, "RETURN", f"Processed refund for order {order['order_number']}, refund amount: {total_refund:,.2f} ({reason})")
        return True, "Return processed successfully. Stock has been restored."

    @staticmethod
    def reprint_order_receipt(order_id: int, printer_name: str = None) -> tuple[bool, str]:
        order = OrderModel.get_order_by_id(order_id)
        if not order:
            return False, "Order not found"
        return ReceiptPrinter.print_receipt(order, printer_name)
