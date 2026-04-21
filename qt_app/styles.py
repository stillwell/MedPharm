# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# Email: Andrew.Stillwell@enlightec.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
MedPharm ERP - Qt Desktop Stylesheet
Dark aurora theme: cyan/magenta/violet gradients on deep navy.
"""

STYLESHEET = """
/* ══════════════════════════════════════════════════════════════
   Global · Deep-space canvas with subtle radial tone
   ══════════════════════════════════════════════════════════════ */
QMainWindow, QWidget {
    background-color: #070b14;
    color: #e9eef7;
    font-family: "Segoe UI", "Inter", "Roboto", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background: qradialgradient(cx:0.1, cy:0, radius:1.2,
                                stop:0 #0f1830, stop:0.6 #0a0f1c, stop:1 #05080f);
}

/* ══════════════════════════════════════════════════════════════
   Menu / Status Bars
   ══════════════════════════════════════════════════════════════ */
QMenuBar {
    background-color: rgba(8, 12, 22, 0.88);
    color: #b6c0d8;
    border-bottom: 1px solid rgba(130,170,240,0.18);
    padding: 4px 6px;
}
QMenuBar::item {
    padding: 6px 12px;
    border-radius: 8px;
    background: transparent;
}
QMenuBar::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 rgba(0,229,208,0.22),
                                stop:1 rgba(177,75,255,0.22));
    color: #ffffff;
}

QMenu {
    background-color: #121a2b;
    color: #e9eef7;
    border: 1px solid rgba(130,170,240,0.22);
    border-radius: 12px;
    padding: 6px;
}
QMenu::item {
    padding: 8px 14px;
    border-radius: 8px;
}
QMenu::item:selected {
    background: rgba(0,229,208,0.18);
    color: #00e5d0;
}
QMenu::separator {
    height: 1px;
    background-color: rgba(130,170,240,0.16);
    margin: 6px 10px;
}

QStatusBar {
    background-color: rgba(8, 12, 22, 0.88);
    color: #8695b0;
    border-top: 1px solid rgba(130,170,240,0.14);
    font-size: 12px;
    padding: 4px 10px;
}
QStatusBar::item { border: none; }

/* ══════════════════════════════════════════════════════════════
   Sidebar · Frosted rail with glowing active pill
   ══════════════════════════════════════════════════════════════ */
QWidget#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(10,14,26,0.95),
                                stop:1 rgba(8,12,22,0.92));
    border-right: 1px solid rgba(130,170,240,0.16);
    min-width: 220px;
}
QPushButton#nav_button {
    background-color: transparent;
    color: #8695b0;
    border: none;
    border-radius: 12px;
    padding: 12px 18px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
    margin: 3px 12px;
}
QPushButton#nav_button:hover {
    background: rgba(0,229,208,0.08);
    color: #e9eef7;
}
QPushButton#nav_button:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 rgba(0,229,208,0.22),
                                stop:1 rgba(24,183,255,0.10));
    color: #00e5d0;
    border-left: 3px solid #00e5d0;
    font-weight: 600;
}

/* ══════════════════════════════════════════════════════════════
   Buttons · Gradient primary, ghost outline defaults
   ══════════════════════════════════════════════════════════════ */
QPushButton {
    background-color: rgba(24, 33, 54, 0.75);
    color: #e9eef7;
    border: 1px solid rgba(130,170,240,0.24);
    border-radius: 10px;
    padding: 9px 18px;
    font-weight: 500;
    min-height: 20px;
}
QPushButton:hover {
    background-color: rgba(36, 48, 78, 0.85);
    border-color: rgba(0,229,208,0.55);
    color: #ffffff;
}
QPushButton:pressed {
    background-color: rgba(18, 26, 43, 0.95);
}
QPushButton:disabled {
    background-color: rgba(18, 26, 43, 0.5);
    color: #5a6782;
    border-color: rgba(130,170,240,0.08);
}

QPushButton#primary_button {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #00e5d0,
                                stop:0.55 #18b7ff,
                                stop:1 #b14bff);
    color: #06111c;
    border: none;
    font-weight: 700;
    padding: 10px 22px;
    border-radius: 12px;
}
QPushButton#primary_button:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #29ffe6,
                                stop:0.55 #4bc9ff,
                                stop:1 #c872ff);
}
QPushButton#primary_button:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #00a899,
                                stop:1 #7d29c4);
}

QPushButton#danger_button {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #ff4757, stop:1 #ff3d8b);
    color: #ffffff;
    border: none;
    font-weight: 700;
    border-radius: 12px;
}
QPushButton#danger_button:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #ff6a78, stop:1 #ff6aa8);
}

QPushButton#success_button {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #00d97e, stop:1 #00e5d0);
    color: #052018;
    border: none;
    font-weight: 700;
    border-radius: 12px;
}
QPushButton#success_button:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #22f598, stop:1 #29ffe6);
}

QPushButton#warning_button {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #ffb800, stop:1 #ff9f43);
    color: #1b1100;
    border: none;
    font-weight: 700;
    border-radius: 12px;
}

/* ══════════════════════════════════════════════════════════════
   Inputs · Glass surface with glow focus
   ══════════════════════════════════════════════════════════════ */
QLineEdit, QTextEdit, QPlainTextEdit,
QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QDateTimeEdit {
    background-color: rgba(12, 18, 30, 0.85);
    color: #e9eef7;
    border: 1px solid rgba(130,170,240,0.22);
    border-radius: 10px;
    padding: 9px 12px;
    selection-background-color: #00e5d0;
    selection-color: #06111c;
    font-size: 13px;
    min-height: 20px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QDateTimeEdit:focus {
    border-color: #00e5d0;
    background-color: rgba(12, 18, 30, 0.98);
}
QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {
    background-color: rgba(18, 26, 43, 0.5);
    color: #5a6782;
}

QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #00e5d0;
    margin-right: 10px;
}
QComboBox QAbstractItemView {
    background-color: #121a2b;
    color: #e9eef7;
    border: 1px solid rgba(130,170,240,0.22);
    border-radius: 10px;
    selection-background-color: rgba(0,229,208,0.22);
    selection-color: #00e5d0;
    padding: 4px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button, QDateEdit::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button, QDateEdit::down-button {
    background-color: rgba(36, 48, 78, 0.7);
    border-radius: 4px;
    width: 20px;
    margin: 2px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: rgba(0,229,208,0.3);
}

/* ══════════════════════════════════════════════════════════════
   Tables
   ══════════════════════════════════════════════════════════════ */
QTableWidget, QTableView {
    background-color: rgba(12, 18, 30, 0.7);
    color: #e9eef7;
    gridline-color: rgba(130,170,240,0.12);
    border: 1px solid rgba(130,170,240,0.18);
    border-radius: 12px;
    selection-background-color: rgba(0,229,208,0.22);
    selection-color: #ffffff;
    alternate-background-color: rgba(18, 26, 43, 0.45);
    font-size: 12px;
}
QTableWidget::item, QTableView::item {
    padding: 8px 10px;
    border-bottom: 1px solid rgba(130,170,240,0.08);
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: rgba(0,229,208,0.18);
    color: #ffffff;
}
QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(18,26,43,0.95),
                                stop:1 rgba(12,18,30,0.95));
    color: #00e5d0;
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid rgba(0,229,208,0.45);
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
QHeaderView::section:hover { background: rgba(36, 48, 78, 0.8); }

/* ══════════════════════════════════════════════════════════════
   Tabs
   ══════════════════════════════════════════════════════════════ */
QTabWidget::pane {
    background-color: rgba(12,18,30,0.45);
    border: 1px solid rgba(130,170,240,0.18);
    border-radius: 12px;
    border-top-left-radius: 0;
    margin-top: -1px;
}
QTabBar::tab {
    background-color: transparent;
    color: #8695b0;
    border: 1px solid rgba(130,170,240,0.15);
    border-bottom: none;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 10px 22px;
    margin-right: 3px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(0,229,208,0.18),
                                stop:1 rgba(12,18,30,0.55));
    color: #00e5d0;
    border-bottom: 2px solid #00e5d0;
}
QTabBar::tab:hover:!selected {
    background: rgba(0,229,208,0.06);
    color: #e9eef7;
}

/* ══════════════════════════════════════════════════════════════
   Group Box
   ══════════════════════════════════════════════════════════════ */
QGroupBox {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(24,33,54,0.7),
                                stop:1 rgba(14,20,34,0.7));
    border: 1px solid rgba(130,170,240,0.18);
    border-radius: 14px;
    margin-top: 18px;
    padding: 18px;
    padding-top: 32px;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 6px 14px;
    color: #00e5d0;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}

/* ══════════════════════════════════════════════════════════════
   Scrollbars · Gradient thumb
   ══════════════════════════════════════════════════════════════ */
QScrollArea { border: none; background-color: transparent; }
QScrollBar:vertical {
    background-color: transparent;
    width: 12px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #2a3a5a, stop:1 #1b2740);
    border-radius: 5px;
    min-height: 40px;
}
QScrollBar::handle:vertical:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #00e5d0, stop:1 #18b7ff);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

QScrollBar:horizontal {
    background-color: transparent;
    height: 12px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #2a3a5a, stop:1 #1b2740);
    border-radius: 5px;
    min-width: 40px;
}
QScrollBar::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #00e5d0, stop:1 #18b7ff);
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ══════════════════════════════════════════════════════════════
   Check / Radio
   ══════════════════════════════════════════════════════════════ */
QCheckBox, QRadioButton {
    spacing: 10px;
    color: #e9eef7;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(130,170,240,0.35);
    background-color: rgba(12,18,30,0.8);
}
QCheckBox::indicator { border-radius: 5px; }
QRadioButton::indicator { border-radius: 9px; }
QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #00e5d0;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #00e5d0, stop:1 #18b7ff);
    border-color: #00e5d0;
}

/* ══════════════════════════════════════════════════════════════
   Progress Bar · Gradient chunk
   ══════════════════════════════════════════════════════════════ */
QProgressBar {
    background-color: rgba(12,18,30,0.85);
    border: 1px solid rgba(130,170,240,0.18);
    border-radius: 10px;
    text-align: center;
    color: #e9eef7;
    height: 22px;
    font-weight: 600;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #00e5d0, stop:0.6 #18b7ff, stop:1 #b14bff);
    border-radius: 8px;
}

/* ══════════════════════════════════════════════════════════════
   Tool Tips
   ══════════════════════════════════════════════════════════════ */
QToolTip {
    background-color: #121a2b;
    color: #e9eef7;
    border: 1px solid rgba(0,229,208,0.5);
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 12px;
}

QSplitter::handle { background-color: rgba(130,170,240,0.18); width: 2px; height: 2px; }
QSplitter::handle:hover { background-color: #00e5d0; }

QDialog, QMessageBox {
    background-color: #0a0f1c;
    color: #e9eef7;
}
QMessageBox QPushButton { min-width: 92px; }

/* ══════════════════════════════════════════════════════════════
   Calendar
   ══════════════════════════════════════════════════════════════ */
QCalendarWidget {
    background-color: #121a2b;
    color: #e9eef7;
}
QCalendarWidget QToolButton {
    background-color: rgba(36, 48, 78, 0.5);
    color: #e9eef7;
    border: none;
    border-radius: 8px;
    padding: 6px 12px;
}
QCalendarWidget QToolButton:hover {
    background-color: rgba(0,229,208,0.18);
    color: #00e5d0;
}
QCalendarWidget QMenu { background-color: #121a2b; color: #e9eef7; }
QCalendarWidget QAbstractItemView {
    background-color: #0a0f1c;
    color: #e9eef7;
    selection-background-color: rgba(0,229,208,0.3);
    selection-color: #ffffff;
}

/* ══════════════════════════════════════════════════════════════
   Labels · Typography roles
   ══════════════════════════════════════════════════════════════ */
QLabel { color: #e9eef7; }
QLabel#heading {
    font-size: 26px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.5px;
}
QLabel#subheading {
    font-size: 15px;
    font-weight: 500;
    color: #8695b0;
    letter-spacing: 0.4px;
}
QLabel#card_value {
    font-size: 32px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -1px;
}
QLabel#card_label {
    font-size: 11px;
    color: #8695b0;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
QLabel#card_title {
    font-size: 14px;
    font-weight: 700;
    color: #00e5d0;
    text-transform: uppercase;
    letter-spacing: 1px;
}
QLabel#section_title {
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(0,229,208,0.45);
    letter-spacing: -0.3px;
}
QLabel#status_active {
    background: rgba(0,217,126,0.18);
    color: #00d97e;
    border: 1px solid rgba(0,217,126,0.4);
    border-radius: 12px;
    padding: 4px 14px;
    font-weight: 700;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
QLabel#status_pending {
    background: rgba(255,159,67,0.18);
    color: #ff9f43;
    border: 1px solid rgba(255,159,67,0.4);
    border-radius: 12px;
    padding: 4px 14px;
    font-weight: 700;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
QLabel#status_expired {
    background: rgba(255,71,87,0.18);
    color: #ff4757;
    border: 1px solid rgba(255,71,87,0.4);
    border-radius: 12px;
    padding: 4px 14px;
    font-weight: 700;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}

/* ══════════════════════════════════════════════════════════════
   Card surfaces · Glass with gradient borders (via bg layers)
   ══════════════════════════════════════════════════════════════ */
QFrame#card {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 rgba(24,33,54,0.80),
                                stop:1 rgba(14,20,34,0.70));
    border: 1px solid rgba(130,170,240,0.18);
    border-radius: 14px;
    padding: 18px;
}
QFrame#card:hover {
    border: 1px solid rgba(0,229,208,0.45);
}
QFrame#kpi_card {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 rgba(24,33,54,0.90),
                                stop:1 rgba(14,20,34,0.85));
    border: 1px solid rgba(130,170,240,0.22);
    border-left: 4px solid #00e5d0;
    border-radius: 14px;
    padding: 22px;
    min-width: 170px;
}
QFrame#kpi_card:hover {
    border-left: 4px solid #00e5d0;
    border-top: 1px solid rgba(0,229,208,0.35);
    border-right: 1px solid rgba(0,229,208,0.35);
    border-bottom: 1px solid rgba(0,229,208,0.35);
}
QFrame#alert_card {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 rgba(255,71,87,0.18),
                                stop:1 rgba(255,61,139,0.08));
    border: 1px solid rgba(255,71,87,0.45);
    border-radius: 12px;
    padding: 14px;
}
QFrame#info_card {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 rgba(48,193,255,0.18),
                                stop:1 rgba(0,229,208,0.08));
    border: 1px solid rgba(48,193,255,0.45);
    border-radius: 12px;
    padding: 14px;
}
QFrame#hero_banner {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #0a1028,
                                stop:0.45 #1e0d36,
                                stop:1 #120a28);
    border: 1px solid rgba(177,75,255,0.35);
    border-radius: 18px;
    padding: 28px;
}

/* ══════════════════════════════════════════════════════════════
   List Widget
   ══════════════════════════════════════════════════════════════ */
QListWidget {
    background-color: rgba(12,18,30,0.75);
    color: #e9eef7;
    border: 1px solid rgba(130,170,240,0.18);
    border-radius: 12px;
    outline: none;
    padding: 4px;
}
QListWidget::item {
    padding: 10px 14px;
    border-bottom: 1px solid rgba(130,170,240,0.08);
    border-radius: 8px;
}
QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 rgba(0,229,208,0.22),
                                stop:1 rgba(24,183,255,0.10));
    color: #ffffff;
    border-bottom-color: transparent;
}
QListWidget::item:hover {
    background-color: rgba(0,229,208,0.08);
}
"""
