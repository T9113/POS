"""
PySide6 Main Window Shell for OnesDev POS.
Hardware-accelerated frameless window with zero startup flicker/glitch,
fluid animations, deep slate sidebar navigation, live digital clock,
EOD register closing, and QStackedWidget screen management.
"""
from datetime import datetime
from PySide6.QtCore import Qt, QPoint, QTimer, QSize
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QColor, QFont, QCursor, QIcon

from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard, apply_windows_native_corners
from pos_app.utils.icon_helper import get_icon
from pos_app.controllers.auth_controller import AuthController
from pos_app.models.order_model import OrderModel
from pos_app.models.settings_model import SettingsModel

# View imports
from pos_app.views.qt_dashboard_view import QtDashboardView
from pos_app.views.qt_pos_view import QtPOSView
from pos_app.views.qt_products_view import QtProductsView
from pos_app.views.qt_inventory_view import QtInventoryView
from pos_app.views.qt_customers_view import QtCustomersView
from pos_app.views.qt_sales_view import QtSalesView
from pos_app.views.qt_reports_view import QtReportsView
from pos_app.views.qt_expenses_view import QtExpensesView
from pos_app.views.qt_settings_view import QtSettingsView


class QtMainWindow(QMainWindow):
    """Primary application frame with frameless controls and deep slate navigation."""

    def __init__(self, on_logout=None):
        super().__init__()
        self.on_logout = on_logout
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.drag_position = QPoint()
        self.sidebar_collapsed = False
        self.nav_buttons = {}

        # 1. Zero-glitch window flags & transparency setup
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1340, 840)
        self.setMinimumSize(1100, 700)
        apply_windows_native_corners(self)

        # 2. Build UI Shell
        self._build_ui()
        self._setup_clock()
        self.update_status_ticker()

        # Start on POS screen (or Dashboard depending on role)
        self.navigate_to("pos")

    def _build_ui(self):
        # Outer container widget for translucent margins and rounded corners
        self.outer_container = QWidget(self)
        self.setCentralWidget(self.outer_container)

        outer_layout = QVBoxLayout(self.outer_container)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        # Window root card with rounded corners and subtle shadow
        self.window_frame = QFrame(self.outer_container)
        self.window_frame.setObjectName("MainWindowContainer")
        self.window_frame.setStyleSheet(f"""
            #MainWindowContainer {{
                background-color: {COLORS["bg_main"]};
                border-radius: 14px;
                border: 1px solid {COLORS["border"]};
            }}
        """)
        window_shadow = QGraphicsDropShadowEffect(self.window_frame)
        window_shadow.setBlurRadius(24)
        window_shadow.setColor(QColor(0, 0, 0, 60))
        window_shadow.setOffset(0, 4)
        self.window_frame.setGraphicsEffect(window_shadow)

        frame_layout = QVBoxLayout(self.window_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # 1. Custom Top Title Bar (Draggable)
        self.title_bar = self._create_title_bar()
        frame_layout.addWidget(self.title_bar)

        # 2. Main Work Area (Sidebar + Stacked Screen Viewport)
        work_area = QWidget(self.window_frame)
        work_layout = QHBoxLayout(work_area)
        work_layout.setContentsMargins(0, 0, 0, 0)
        work_layout.setSpacing(0)

        # Deep Slate Sidebar
        self.sidebar = self._create_sidebar()
        work_layout.addWidget(self.sidebar)

        # Central Screen Stack
        self.screen_stack = QStackedWidget(work_area)
        self.screen_stack.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        self._init_screens()
        work_layout.addWidget(self.screen_stack, stretch=1)

        frame_layout.addWidget(work_area, stretch=1)

        # 3. Bottom Status Bar
        self.status_bar = self._create_status_bar()
        frame_layout.addWidget(self.status_bar)

        outer_layout.addWidget(self.window_frame)

    def _create_title_bar(self) -> QWidget:
        bar = QFrame(self.window_frame)
        bar.setObjectName("TitleBar")
        bar.setFixedHeight(50)
        bar.setStyleSheet(f"""
            #TitleBar {{
                background-color: {COLORS['bg_sidebar']};
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                border-bottom: 1px solid #334155;
            }}
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 12, 0)
        layout.setSpacing(12)

        # Brand / App Title
        brand_icon = QLabel(bar)
        brand_icon.setPixmap(get_icon("lightning", color="#F59E0B", size=20).pixmap(20, 20))
        brand_icon.setFixedSize(22, 22)
        layout.addWidget(brand_icon)

        biz_name = SettingsModel.get("business_name", "OnesDev POS")
        self.lbl_brand = QLabel(biz_name, bar)
        self.lbl_brand.setStyleSheet("font-size: 15px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.5px;")
        layout.addWidget(self.lbl_brand)

        # Collapse Sidebar Button
        btn_collapse = QPushButton("≡", bar)
        btn_collapse.setFixedSize(30, 30)
        btn_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_collapse.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #334155;
                color: #FFFFFF;
            }
        """)
        btn_collapse.clicked.connect(self._toggle_sidebar)
        layout.addWidget(btn_collapse)

        layout.addStretch()

        # Center Live Digital Clock
        self.lbl_clock = QLabel(bar)
        self.lbl_clock.setStyleSheet("font-size: 12px; font-weight: 600; color: #94A3B8;")
        layout.addWidget(self.lbl_clock)

        layout.addStretch()

        # Logged in user tag
        user = AuthController.get_current_user()
        u_name = user["full_name"] if user else "Cashier"
        u_role = user["role"] if user else "Cashier"
        role_bg = COLORS["primary"] if u_role == "Admin" else COLORS["success"]

        user_badge = QFrame(bar)
        user_badge.setStyleSheet("background-color: #334155; border-radius: 14px; padding: 2px 8px;")
        ub_l = QHBoxLayout(user_badge)
        ub_l.setContentsMargins(8, 2, 8, 2)
        ub_l.setSpacing(6)

        lbl_u_icon = QLabel(user_badge)
        lbl_u_icon.setPixmap(get_icon("user", color="#94A3B8", size=13).pixmap(13, 13))
        lbl_u_icon.setFixedSize(14, 14)
        ub_l.addWidget(lbl_u_icon)

        lbl_u = QLabel(u_name, user_badge)
        lbl_u.setStyleSheet("color: #F8FAFC; font-size: 12px; font-weight: 600;")
        ub_l.addWidget(lbl_u)

        lbl_r = QLabel(f" {u_role} ", user_badge)
        lbl_r.setStyleSheet(f"background-color: {role_bg}; color: #FFFFFF; font-size: 10px; font-weight: bold; border-radius: 8px; padding: 2px 4px;")
        ub_l.addWidget(lbl_r)
        layout.addWidget(user_badge)

        # Window Action Controls (Minimize, Maximize, Close)
        btn_min = QPushButton("─", bar)
        btn_min.setFixedSize(30, 30)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.setStyleSheet("""
            QPushButton { background: transparent; color: #94A3B8; font-size: 14px; font-weight: bold; border: none; border-radius: 6px; }
            QPushButton:hover { background: #334155; color: #FFFFFF; }
        """)
        btn_min.clicked.connect(self.showMinimized)
        layout.addWidget(btn_min)

        btn_max = QPushButton("□", bar)
        btn_max.setFixedSize(30, 30)
        btn_max.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_max.setStyleSheet("""
            QPushButton { background: transparent; color: #94A3B8; font-size: 14px; font-weight: bold; border: none; border-radius: 6px; }
            QPushButton:hover { background: #334155; color: #FFFFFF; }
        """)
        btn_max.clicked.connect(self._toggle_maximize)
        layout.addWidget(btn_max)

        btn_close = QPushButton("✕", bar)
        btn_close.setFixedSize(30, 30)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton { background: transparent; color: #94A3B8; font-size: 13px; font-weight: bold; border: none; border-radius: 6px; }
            QPushButton:hover { background: #DC2626; color: #FFFFFF; }
        """)
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        return bar

    def _create_sidebar(self) -> QWidget:
        self.sidebar_frame = QFrame(self.window_frame)
        self.sidebar_frame.setObjectName("Sidebar")
        self.sidebar_frame.setFixedWidth(210)
        self.sidebar_frame.setStyleSheet(f"""
            #Sidebar {{
                background-color: {COLORS['bg_sidebar']};
            }}
        """)

        layout = QVBoxLayout(self.sidebar_frame)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)

        # Nav items list: (key, icon_name, label)
        self.nav_items = [
            ("pos", "cart", "Point of Sale"),
            ("dashboard", "dashboard", "Dashboard"),
            ("products", "products", "Products"),
            ("inventory", "inventory", "Inventory"),
            ("customers", "customers", "Customers"),
            ("sales", "sales", "Sales & Orders"),
            ("reports", "reports", "Reports"),
            ("expenses", "expenses", "Expenses"),
            ("settings", "settings", "Settings"),
        ]

        for key, icon_key, label in self.nav_items:
            if not AuthController.can_access(key):
                continue

            btn = QPushButton(self.sidebar_frame)
            btn.setFixedHeight(42)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("nav_key", key)
            btn.setProperty("icon_key", icon_key)
            btn.setProperty("nav_label", label)
            btn.setText(f"  {label}")
            btn.setIcon(get_icon(icon_key, color=COLORS["sidebar_text"], size=18))
            btn.setIconSize(QSize(18, 18))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['sidebar_text']};
                    text-align: left;
                    padding-left: 14px;
                    font-size: 13px;
                    font-weight: 600;
                    border-radius: 8px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['sidebar_hover']};
                    color: #FFFFFF;
                }}
            """)
            btn.clicked.connect(lambda _, k=key: self.navigate_to(k))
            self.nav_buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Logout button
        self.btn_logout = QPushButton("  Sign Out", self.sidebar_frame)
        self.btn_logout.setIcon(get_icon("logout", color="#EF4444", size=18))
        self.btn_logout.setIconSize(QSize(18, 18))
        self.btn_logout.setFixedHeight(40)
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #EF4444;
                text-align: left;
                padding-left: 14px;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.15);
                color: #F87171;
            }
        """)
        self.btn_logout.clicked.connect(self._do_logout)
        layout.addWidget(self.btn_logout)

        return self.sidebar_frame

    def _init_screens(self):
        self.screen_instances = {}

        # 1. POS View
        self.pos_view = QtPOSView(self.screen_stack)
        self.pos_view.order_completed.connect(self._on_order_completed)
        self.screen_stack.addWidget(self.pos_view)
        self.screen_instances["pos"] = self.pos_view

        # 2. Dashboard View
        self.dashboard_view = QtDashboardView(self.screen_stack)
        self.dashboard_view.navigate_requested.connect(self.navigate_to)
        self.screen_stack.addWidget(self.dashboard_view)
        self.screen_instances["dashboard"] = self.dashboard_view

        # 3. Products View
        self.products_view = QtProductsView(self.screen_stack)
        self.screen_stack.addWidget(self.products_view)
        self.screen_instances["products"] = self.products_view

        # 4. Inventory View
        self.inventory_view = QtInventoryView(self.screen_stack)
        self.screen_stack.addWidget(self.inventory_view)
        self.screen_instances["inventory"] = self.inventory_view

        # 5. Customers View
        self.customers_view = QtCustomersView(self.screen_stack)
        self.screen_stack.addWidget(self.customers_view)
        self.screen_instances["customers"] = self.customers_view

        # 6. Sales View
        self.sales_view = QtSalesView(self.screen_stack)
        self.screen_stack.addWidget(self.sales_view)
        self.screen_instances["sales"] = self.sales_view

        # 7. Reports View
        self.reports_view = QtReportsView(self.screen_stack)
        self.screen_stack.addWidget(self.reports_view)
        self.screen_instances["reports"] = self.reports_view

        # 8. Expenses View
        self.expenses_view = QtExpensesView(self.screen_stack)
        self.screen_stack.addWidget(self.expenses_view)
        self.screen_instances["expenses"] = self.expenses_view

        # 9. Settings View
        self.settings_view = QtSettingsView(self.screen_stack)
        self.settings_view.settings_updated.connect(self._on_settings_updated)
        self.screen_stack.addWidget(self.settings_view)
        self.screen_instances["settings"] = self.settings_view

    def _create_status_bar(self) -> QWidget:
        bar = QFrame(self.window_frame)
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(32)
        bar.setStyleSheet(f"""
            #StatusBar {{
                background-color: {COLORS['bg_surface']};
                border-bottom-left-radius: 14px;
                border-bottom-right-radius: 14px;
                border-top: 1px solid {COLORS['border']};
            }}
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)

        self.lbl_sales_ticker = QLabel(bar)
        self.lbl_sales_ticker.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {COLORS['text_secondary']};")
        layout.addWidget(self.lbl_sales_ticker)

        layout.addStretch()

        lbl_offline = QLabel("● Offline Ready • Local Database", bar)
        lbl_offline.setStyleSheet(f"font-size: 11px; color: {COLORS['success']}; font-weight: 600;")
        layout.addWidget(lbl_offline)

        layout.addSpacing(16)

        lbl_ver = QLabel("OnesDev POS v2.0", bar)
        lbl_ver.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")
        layout.addWidget(lbl_ver)

        return bar

    def _setup_clock(self):
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        now = datetime.now()
        self.lbl_clock.setText(now.strftime("%A, %d %B %Y  •  %I:%M:%S %p"))

    def update_status_ticker(self):
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        metrics = OrderModel.get_today_metrics()
        self.lbl_sales_ticker.setText(
            f"Today's Sales: {self.currency} {metrics['total_sales']:,.2f}  ({metrics['total_orders']} orders)"
        )

    def navigate_to(self, key: str):
        if not AuthController.can_access(key):
            QMessageBox.warning(self, "Access Denied", "Your user role does not have permission to access this module.")
            return

        # Update sidebar button styles and icon colors
        for k, btn in self.nav_buttons.items():
            icon_key = btn.property("icon_key") or "cart"
            if k == key:
                btn.setIcon(get_icon(icon_key, color="#FFFFFF", size=18))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['sidebar_active_bg']};
                        color: {COLORS['sidebar_active_text']};
                        text-align: {"center" if self.sidebar_collapsed else "left"};
                        padding-left: {0 if self.sidebar_collapsed else 14}px;
                        font-size: 13px;
                        font-weight: 700;
                        border-radius: 8px;
                        border-left: {0 if self.sidebar_collapsed else 4}px solid {COLORS['sidebar_indicator']};
                    }}
                """)
            else:
                btn.setIcon(get_icon(icon_key, color=COLORS['sidebar_text'], size=18))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {COLORS['sidebar_text']};
                        text-align: {"center" if self.sidebar_collapsed else "left"};
                        padding-left: {0 if self.sidebar_collapsed else 14}px;
                        font-size: 13px;
                        font-weight: 600;
                        border-radius: 8px;
                        border: none;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['sidebar_hover']};
                        color: #FFFFFF;
                    }}
                """)

        if key in self.screen_instances:
            screen = self.screen_instances[key]
            self.screen_stack.setCurrentWidget(screen)
            if hasattr(screen, "refresh_data"):
                screen.refresh_data()
            elif hasattr(screen, "refresh_orders"):
                screen.refresh_orders()
            elif hasattr(screen, "refresh_customers"):
                screen.refresh_customers()
            elif hasattr(screen, "refresh_expenses"):
                screen.refresh_expenses()

        self.update_status_ticker()

    def _toggle_sidebar(self):
        self.sidebar_collapsed = not self.sidebar_collapsed
        new_width = 64 if self.sidebar_collapsed else 210
        self.sidebar_frame.setFixedWidth(new_width)

        for key, btn in self.nav_buttons.items():
            label = btn.property("nav_label") or ""
            if self.sidebar_collapsed:
                btn.setText("")
                btn.setToolTip(label)
                btn.setStyleSheet(btn.styleSheet() + "text-align: center; padding-left: 0px;")
            else:
                btn.setText(f"  {label}")
                btn.setToolTip("")
                btn.setStyleSheet(btn.styleSheet() + "text-align: left; padding-left: 14px;")

        if hasattr(self, "btn_logout"):
            if self.sidebar_collapsed:
                self.btn_logout.setText("")
                self.btn_logout.setToolTip("Sign Out")
                self.btn_logout.setStyleSheet(self.btn_logout.styleSheet() + "text-align: center; padding-left: 0px;")
            else:
                self.btn_logout.setText("  Sign Out")
                self.btn_logout.setToolTip("")
                self.btn_logout.setStyleSheet(self.btn_logout.styleSheet() + "text-align: left; padding-left: 14px;")

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _on_order_completed(self, order_dict):
        self.update_status_ticker()

    def _on_settings_updated(self):
        biz_name = SettingsModel.get("business_name", "OnesDev POS")
        self.lbl_brand.setText(biz_name)
        self.update_status_ticker()

    def _do_logout(self):
        AuthController.logout()
        if self.on_logout:
            self.on_logout()
        self.close()

    # --- Frameless Window Dragging Handlers ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicked inside title bar region
            if event.position().y() <= 50:
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = QPoint()
        event.accept()

    # Global Key shortcuts
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_F1:
            self.navigate_to("pos")
        elif key == Qt.Key.Key_F2:
            self.navigate_to("pos")
            if hasattr(self.pos_view, "txt_search"):
                self.pos_view.txt_search.setFocus()
        elif key == Qt.Key.Key_F5:
            self.navigate_to("pos")
            if hasattr(self.pos_view, "_on_checkout"):
                self.pos_view._on_checkout()
        else:
            super().keyPressEvent(event)
