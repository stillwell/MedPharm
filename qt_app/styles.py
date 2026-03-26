# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
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
MedPharm ERP - Qt Application Stylesheet
Professional dark medical theme with teal accents.
"""

STYLESHEET = """
/* ── Global ─────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #1a1d23;
    color: #e0e0e0;
    font-family: "Segoe UI", "Roboto", sans-serif;
    font-size: 13px;
}

/* ── Menu Bar ───────────────────────────────────────── */
QMenuBar {
    background-color: #12151a;
    color: #b0b0b0;
    border-bottom: 1px solid #2a2d35;
    padding: 2px;
}
QMenuBar::item:selected {
    background-color: #00BCD4;
    color: #ffffff;
    border-radius: 4px;
}
QMenu {
    background-color: #1e2129;
    color: #e0e0e0;
    border: 1px solid #2a2d35;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item:selected {
    background-color: #00BCD4;
    color: #ffffff;
    border-radius: 4px;
}
QMenu::separator {
    height: 1px;
    background-color: #2a2d35;
    margin: 4px 8px;
}

/* ── Status Bar ─────────────────────────────────────── */
QStatusBar {
    background-color: #12151a;
    color: #808080;
    border-top: 1px solid #2a2d35;
    font-size: 12px;
}

/* ── Sidebar Navigation ────────────────────────────── */
QWidget#sidebar {
    background-color: #12151a;
    border-right: 1px solid #2a2d35;
}
QPushButton#nav_button {
    background-color: transparent;
    color: #808080;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
    margin: 2px 8px;
}
QPushButton#nav_button:hover {
    background-color: #1e2129;
    color: #e0e0e0;
}
QPushButton#nav_button:checked {
    background-color: rgba(0, 188, 212, 0.15);
    color: #00BCD4;
    border-left: 3px solid #00BCD4;
}

/* ── Buttons ────────────────────────────────────────── */
QPushButton {
    background-color: #2a2d35;
    color: #e0e0e0;
    border: 1px solid #3a3d45;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #3a3d45;
    border-color: #4a4d55;
}
QPushButton:pressed {
    background-color: #1a1d23;
}
QPushButton:disabled {
    background-color: #1a1d23;
    color: #505050;
    border-color: #2a2d35;
}
QPushButton#primary_button {
    background-color: #00BCD4;
    color: #ffffff;
    border: none;
    font-weight: 600;
}
QPushButton#primary_button:hover {
    background-color: #00ACC1;
}
QPushButton#primary_button:pressed {
    background-color: #0097A7;
}
QPushButton#danger_button {
    background-color: #E53935;
    color: #ffffff;
    border: none;
}
QPushButton#danger_button:hover {
    background-color: #D32F2F;
}
QPushButton#success_button {
    background-color: #43A047;
    color: #ffffff;
    border: none;
}
QPushButton#success_button:hover {
    background-color: #388E3C;
}
QPushButton#warning_button {
    background-color: #FB8C00;
    color: #ffffff;
    border: none;
}

/* ── Line Edits / Inputs ───────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #12151a;
    color: #e0e0e0;
    border: 1px solid #2a2d35;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #00BCD4;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #00BCD4;
}
QLineEdit:disabled, QTextEdit:disabled {
    background-color: #1a1d23;
    color: #505050;
}

/* ── Combo Boxes ────────────────────────────────────── */
QComboBox {
    background-color: #12151a;
    color: #e0e0e0;
    border: 1px solid #2a2d35;
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 20px;
}
QComboBox:focus {
    border-color: #00BCD4;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #808080;
    margin-right: 10px;
}
QComboBox QAbstractItemView {
    background-color: #1e2129;
    color: #e0e0e0;
    border: 1px solid #2a2d35;
    selection-background-color: #00BCD4;
    selection-color: #ffffff;
    border-radius: 6px;
}

/* ── Spin Boxes / Date Edits ───────────────────────── */
QSpinBox, QDoubleSpinBox, QDateEdit, QDateTimeEdit {
    background-color: #12151a;
    color: #e0e0e0;
    border: 1px solid #2a2d35;
    border-radius: 6px;
    padding: 8px 12px;
}
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QDateTimeEdit:focus {
    border-color: #00BCD4;
}
QSpinBox::up-button, QDoubleSpinBox::up-button, QDateEdit::up-button {
    background-color: #2a2d35;
    border-radius: 3px;
    width: 20px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button, QDateEdit::down-button {
    background-color: #2a2d35;
    border-radius: 3px;
    width: 20px;
}

/* ── Tables ─────────────────────────────────────────── */
QTableWidget, QTableView {
    background-color: #12151a;
    color: #e0e0e0;
    gridline-color: #2a2d35;
    border: 1px solid #2a2d35;
    border-radius: 8px;
    selection-background-color: rgba(0, 188, 212, 0.2);
    selection-color: #ffffff;
    alternate-background-color: #161920;
    font-size: 12px;
}
QTableWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #1e2129;
}
QTableWidget::item:selected {
    background-color: rgba(0, 188, 212, 0.2);
    color: #ffffff;
}
QHeaderView::section {
    background-color: #1e2129;
    color: #00BCD4;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid #00BCD4;
    font-weight: 600;
    font-size: 12px;
}
QHeaderView::section:hover {
    background-color: #2a2d35;
}

/* ── Tab Widget ─────────────────────────────────────── */
QTabWidget::pane {
    background-color: #1a1d23;
    border: 1px solid #2a2d35;
    border-radius: 8px;
    border-top-left-radius: 0;
}
QTabBar::tab {
    background-color: #12151a;
    color: #808080;
    border: 1px solid #2a2d35;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 20px;
    margin-right: 2px;
    font-weight: 500;
}
QTabBar::tab:selected {
    background-color: #1a1d23;
    color: #00BCD4;
    border-bottom: 2px solid #00BCD4;
}
QTabBar::tab:hover:!selected {
    background-color: #1e2129;
    color: #e0e0e0;
}

/* ── Group Box ──────────────────────────────────────── */
QGroupBox {
    background-color: #1e2129;
    border: 1px solid #2a2d35;
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px;
    padding-top: 28px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    color: #00BCD4;
    font-size: 13px;
}

/* ── Scroll Areas ───────────────────────────────────── */
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical {
    background-color: #12151a;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #3a3d45;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #4a4d55;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #12151a;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background-color: #3a3d45;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #4a4d55;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ── Check Box / Radio ──────────────────────────────── */
QCheckBox {
    spacing: 8px;
    color: #e0e0e0;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #3a3d45;
    background-color: #12151a;
}
QCheckBox::indicator:checked {
    background-color: #00BCD4;
    border-color: #00BCD4;
}
QRadioButton {
    spacing: 8px;
    color: #e0e0e0;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #3a3d45;
    background-color: #12151a;
}
QRadioButton::indicator:checked {
    background-color: #00BCD4;
    border-color: #00BCD4;
}

/* ── Progress Bar ───────────────────────────────────── */
QProgressBar {
    background-color: #12151a;
    border: 1px solid #2a2d35;
    border-radius: 6px;
    text-align: center;
    color: #e0e0e0;
    height: 20px;
}
QProgressBar::chunk {
    background-color: #00BCD4;
    border-radius: 5px;
}

/* ── Tool Tips ──────────────────────────────────────── */
QToolTip {
    background-color: #1e2129;
    color: #e0e0e0;
    border: 1px solid #00BCD4;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ── Splitter ───────────────────────────────────────── */
QSplitter::handle {
    background-color: #2a2d35;
    width: 2px;
    height: 2px;
}
QSplitter::handle:hover {
    background-color: #00BCD4;
}

/* ── Dialog ─────────────────────────────────────────── */
QDialog {
    background-color: #1a1d23;
    color: #e0e0e0;
}

/* ── Message Box ────────────────────────────────────── */
QMessageBox {
    background-color: #1a1d23;
    color: #e0e0e0;
}
QMessageBox QPushButton {
    min-width: 80px;
}

/* ── Calendar Widget ────────────────────────────────── */
QCalendarWidget {
    background-color: #12151a;
    color: #e0e0e0;
}
QCalendarWidget QToolButton {
    background-color: #1e2129;
    color: #e0e0e0;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
}
QCalendarWidget QToolButton:hover {
    background-color: #2a2d35;
}
QCalendarWidget QMenu {
    background-color: #1e2129;
    color: #e0e0e0;
}
QCalendarWidget QAbstractItemView {
    background-color: #12151a;
    color: #e0e0e0;
    selection-background-color: #00BCD4;
    selection-color: #ffffff;
}

/* ── Labels ─────────────────────────────────────────── */
QLabel {
    color: #e0e0e0;
}
QLabel#heading {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
}
QLabel#subheading {
    font-size: 16px;
    font-weight: 600;
    color: #b0b0b0;
}
QLabel#card_value {
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
}
QLabel#card_label {
    font-size: 12px;
    color: #808080;
    font-weight: 500;
}
QLabel#card_title {
    font-size: 14px;
    font-weight: 600;
    color: #00BCD4;
}
QLabel#section_title {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
    padding-bottom: 8px;
    border-bottom: 2px solid #00BCD4;
}
QLabel#status_active {
    background-color: rgba(67, 160, 71, 0.2);
    color: #43A047;
    border-radius: 10px;
    padding: 4px 12px;
    font-weight: 600;
    font-size: 11px;
}
QLabel#status_pending {
    background-color: rgba(251, 140, 0, 0.2);
    color: #FB8C00;
    border-radius: 10px;
    padding: 4px 12px;
    font-weight: 600;
    font-size: 11px;
}
QLabel#status_expired {
    background-color: rgba(229, 57, 53, 0.2);
    color: #E53935;
    border-radius: 10px;
    padding: 4px 12px;
    font-weight: 600;
    font-size: 11px;
}

/* ── Card Container ─────────────────────────────────── */
QFrame#card {
    background-color: #1e2129;
    border: 1px solid #2a2d35;
    border-radius: 10px;
    padding: 16px;
}
QFrame#card:hover {
    border-color: #3a3d45;
}
QFrame#kpi_card {
    background-color: #1e2129;
    border: 1px solid #2a2d35;
    border-radius: 12px;
    padding: 20px;
    min-width: 160px;
}
QFrame#alert_card {
    background-color: rgba(229, 57, 53, 0.1);
    border: 1px solid rgba(229, 57, 53, 0.3);
    border-radius: 8px;
    padding: 12px;
}
QFrame#info_card {
    background-color: rgba(3, 155, 229, 0.1);
    border: 1px solid rgba(3, 155, 229, 0.3);
    border-radius: 8px;
    padding: 12px;
}

/* ── List Widget ────────────────────────────────────── */
QListWidget {
    background-color: #12151a;
    color: #e0e0e0;
    border: 1px solid #2a2d35;
    border-radius: 8px;
    outline: none;
}
QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #1e2129;
}
QListWidget::item:selected {
    background-color: rgba(0, 188, 212, 0.2);
    color: #ffffff;
}
QListWidget::item:hover {
    background-color: #1e2129;
}
"""
