#!/usr/bin/env python3

import sys
import sqlite3
import matplotlib
from PySide6.QtWidgets import (QApplication, QMainWindow, QMenu, QTabWidget, QVBoxLayout, QWidget, QTableWidget,
                               QTableWidgetItem, QDateEdit, QHBoxLayout, QLabel, QPushButton, QDialog, QLineEdit,
                               QFormLayout, QMessageBox, QDialogButtonBox, QHeaderView)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QDate, Qt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


def create_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS egg_laying
                 (date TEXT, count INTEGER, note TEXT)''')
    conn.commit()
    conn.close()


def insert_data(date, count, note=""):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO egg_laying (date, count, note) VALUES (?, ?, ?)", (date, count, note))
    conn.commit()
    conn.close()


def update_data(date, new_count, new_note):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE egg_laying SET count = ?, note = ? WHERE date = ?", (new_count, new_note, date))
    conn.commit()
    conn.close()


def delete_data(date):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM egg_laying WHERE date = ?", (date,))
    conn.commit()
    conn.close()


def fetch_data(start_date=None, end_date=None):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    query = "SELECT date, count, note FROM egg_laying"
    params = ()
    if start_date and end_date:
        query += " WHERE date BETWEEN ? AND ?"
        params = (start_date, end_date)
    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    return data


class AddRecordDialog(QDialog):
    def __init__(self, parent=None, date=None, count=None, note=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Record")

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")

        self.count_edit = QLineEdit()
        self.count_edit.setPlaceholderText("Egg count")

        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Note (optional)")

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_record)

        layout = QFormLayout()
        layout.addRow("Date:", self.date_edit)
        layout.addRow("Egg count:", self.count_edit)
        layout.addRow("Note:", self.note_edit)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

        if date and count is not None:
            self.date_edit.setDate(QDate.fromString(date, "dd.MM.yyyy"))
            self.count_edit.setText(str(count))
            self.note_edit.setText(note if note else "")
        self.record_data = None

    def save_record(self):
        date = self.date_edit.date().toString("dd.MM.yyyy")
        count = self.count_edit.text()
        note = self.note_edit.text()

        if not count.isdigit():
            QMessageBox.warning(self, "Error", "Egg count must be a number.")
            return

        count = int(count)
        self.record_data = (date, count, note)
        self.accept()


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About the Application")
        self.setGeometry(100, 100, 400, 400)

        layout = QVBoxLayout()

        icon_label = QLabel()
        icon_pixmap = QIcon("resources/app_logopng.png").pixmap(64, 64)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        app_info = QLabel(
            "Egg Laying Tracker<br>Version 1.0<br><br>Developer: Your Name<br>"
            "This application helps you track the number of eggs laid over time."
        )
        app_info.setTextFormat(Qt.RichText)
        app_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(app_info)

        social_media_layout = QVBoxLayout()

        icons_html = {
            "GitHub": ("fab fa-github", "https://github.com/yourusername"),
            "GitLab": ("fab fa-gitlab", "https://gitlab.com/yourusername"),
            "Mastodon": ("fab fa-mastodon", "https://mastodon.social/@yourusername"),
            "Facebook": ("fab fa-facebook", "https://www.facebook.com/yourusername"),
            "Instagram": ("fab fa-instagram", "https://www.instagram.com/yourusername"),
            "Twitter": ("fab fa-twitter", "https://twitter.com/yourusername"),
            "Pinterest": ("fab fa-pinterest", "https://www.pinterest.com/yourusername"),
        }

        for platform, (icon_class, url) in icons_html.items():
            icon_label = QLabel(
                f'<a href="{url}" style="text-decoration:none;"><i class="{icon_class}" style="font-size:24px; color:black;"></i></a>')
            icon_label.setTextFormat(Qt.RichText)
            icon_label.setOpenExternalLinks(True)
            social_media_layout.addWidget(icon_label)

        layout.addLayout(social_media_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Egg Laying Tracker")
        self.setGeometry(100, 100, 800, 600)

        self.setWindowIcon(QIcon("resources/app_icon.png"))

        self.create_menu()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.create_tabs()

    def create_menu(self):
        file_menu = self.menuBar().addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        egg_menu = self.menuBar().addMenu("Egg Laying")
        add_data_action = QAction("Add Record", self)
        add_data_action.triggered.connect(self.add_data)
        egg_menu.addAction(add_data_action)

        help_menu = self.menuBar().addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_tabs(self):
        self.weekly_tab = QWidget()
        self.create_weekly_tab(self.weekly_tab)
        self.tabs.addTab(self.weekly_tab, "Weekly Chart")

        self.monthly_tab = QWidget()
        self.create_monthly_tab(self.monthly_tab)
        self.tabs.addTab(self.monthly_tab, "Monthly Chart")

        self.yearly_tab = QWidget()
        self.create_yearly_tab(self.yearly_tab)
        self.tabs.addTab(self.yearly_tab, "Yearly Chart")

        self.overview_tab = QWidget()
        self.create_overview_tab(self.overview_tab)
        self.tabs.addTab(self.overview_tab, "Overview")

    def create_weekly_tab(self, tab):
        layout = QVBoxLayout()

        date_selection_layout = QHBoxLayout()
        date_selection_label = QLabel("Select a date in the week:")
        self.date_edit_weekly = QDateEdit(QDate.currentDate())
        self.date_edit_weekly.setCalendarPopup(True)
        self.date_edit_weekly.setDisplayFormat("dd.MM.yyyy")
        self.date_edit_weekly.dateChanged.connect(self.update_weekly_plot)

        date_selection_layout.addWidget(date_selection_label)
        date_selection_layout.addWidget(self.date_edit_weekly)
        layout.addLayout(date_selection_layout)

        self.fig_weekly, self.ax_weekly = plt.subplots()
        self.canvas_weekly = FigureCanvas(self.fig_weekly)

        layout.addWidget(self.canvas_weekly)
        tab.setLayout(layout)

        self.update_weekly_plot()

    def update_weekly_plot(self):
        selected_date = self.date_edit_weekly.date()
        week_start = selected_date.addDays(-(selected_date.dayOfWeek() - 1))
        week_end = week_start.addDays(6)

        data = fetch_data()
        dates_dict = {datetime.strptime(d, "%d.%m.%Y").date(): c for d, c, _ in data}

        all_dates = [week_start.toPython() + timedelta(days=i) for i in range(7)]
        all_counts = [dates_dict.get(date, 0) for date in all_dates]

        self.ax_weekly.clear()
        self.ax_weekly.bar(all_dates, all_counts)
        self.ax_weekly.set_title(
            f"Weekly Chart ({week_start.toString('dd.MM.yyyy')} - {week_end.toString('dd.MM.yyyy')})")
        self.ax_weekly.set_xlabel("Date")
        self.ax_weekly.set_ylabel("Egg Count")

        self.ax_weekly.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        self.fig_weekly.autofmt_xdate()

        self.ax_weekly.set_ylim(bottom=0)

        self.canvas_weekly.draw()

    def create_monthly_tab(self, tab):
        layout = QVBoxLayout()

        date_selection_layout = QHBoxLayout()
        date_selection_label = QLabel("Select a date in the month:")
        self.date_edit_monthly = QDateEdit(QDate.currentDate())
        self.date_edit_monthly.setCalendarPopup(True)
        self.date_edit_monthly.setDisplayFormat("dd.MM.yyyy")
        self.date_edit_monthly.dateChanged.connect(self.update_monthly_plot)

        date_selection_layout.addWidget(date_selection_label)
        date_selection_layout.addWidget(self.date_edit_monthly)
        layout.addLayout(date_selection_layout)

        self.fig_monthly, self.ax_monthly = plt.subplots()
        self.canvas_monthly = FigureCanvas(self.fig_monthly)

        layout.addWidget(self.canvas_monthly)
        tab.setLayout(layout)

        self.update_monthly_plot()

    def update_monthly_plot(self):
        selected_date = self.date_edit_monthly.date()
        month_start = QDate(selected_date.year(), selected_date.month(), 1)
        month_end = month_start.addMonths(1).addDays(-1)

        data = fetch_data(start_date=month_start.toString("dd.MM.yyyy"), end_date=month_end.toString("dd.MM.yyyy"))
        dates_dict = {datetime.strptime(d, "%d.%m.%Y").date(): c for d, c, _ in data}

        all_dates = [month_start.toPython() + timedelta(days=i) for i in
                     range((month_end.toPython() - month_start.toPython()).days + 1)]
        all_counts = [dates_dict.get(date, 0) for date in all_dates]

        self.ax_monthly.clear()
        self.ax_monthly.bar(all_dates, all_counts)
        self.ax_monthly.set_title(f"Monthly Chart ({month_start.toString('MMMM yyyy')})")
        self.ax_monthly.set_xlabel("Date")
        self.ax_monthly.set_ylabel("Egg Count")

        self.ax_monthly.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        self.fig_monthly.autofmt_xdate()

        self.ax_monthly.set_ylim(bottom=0)

        self.canvas_monthly.draw()

    def create_yearly_tab(self, tab):
        layout = QVBoxLayout()

        date_selection_layout = QHBoxLayout()
        date_selection_label = QLabel("Select a date in the year:")
        self.date_edit_yearly = QDateEdit(QDate.currentDate())
        self.date_edit_yearly.setCalendarPopup(True)
        self.date_edit_yearly.setDisplayFormat("dd.MM.yyyy")
        self.date_edit_yearly.dateChanged.connect(self.update_yearly_plot)

        date_selection_layout.addWidget(date_selection_label)
        date_selection_layout.addWidget(self.date_edit_yearly)
        layout.addLayout(date_selection_layout)

        self.fig_yearly, self.ax_yearly = plt.subplots()
        self.canvas_yearly = FigureCanvas(self.fig_yearly)

        layout.addWidget(self.canvas_yearly)
        tab.setLayout(layout)

        self.update_yearly_plot()

    def update_yearly_plot(self):
        selected_date = self.date_edit_yearly.date()
        year_start = QDate(selected_date.year(), 1, 1)
        year_end = QDate(selected_date.year(), 12, 31)

        data = fetch_data(start_date=year_start.toString("dd.MM.yyyy"), end_date=year_end.toString("dd.MM.yyyy"))
        dates_dict = {datetime.strptime(d, "%d.%m.%Y").date(): c for d, c, _ in data}

        all_dates = [year_start.toPython() + timedelta(days=i) for i in
                     range((year_end.toPython() - year_start.toPython()).days + 1)]
        all_counts = [dates_dict.get(date, 0) for date in all_dates]

        self.ax_yearly.clear()
        self.ax_yearly.bar(all_dates, all_counts)
        self.ax_yearly.set_title(f"Yearly Chart ({selected_date.year()})")
        self.ax_yearly.set_xlabel("Date")
        self.ax_yearly.set_ylabel("Egg Count")

        self.ax_yearly.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        self.fig_yearly.autofmt_xdate()

        self.ax_yearly.set_ylim(bottom=0)

        self.canvas_yearly.draw()

    def create_overview_tab(self, tab):
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "Count", "Note", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.table)
        tab.setLayout(layout)

        self.populate_table()

    def populate_table(self):
        self.table.setRowCount(0)
        data = fetch_data()
        for row_index, (date, count, note) in enumerate(data):
            self.table.insertRow(row_index)
            self.table.setItem(row_index, 0, QTableWidgetItem(date))
            self.table.setItem(row_index, 1, QTableWidgetItem(str(count)))
            self.table.setItem(row_index, 2, QTableWidgetItem(note if note else ""))

            edit_button = QPushButton("Edit")
            delete_button = QPushButton("Delete")

            edit_button.clicked.connect(lambda _, r=row_index: self.edit_record(r))
            delete_button.clicked.connect(lambda _, r=row_index: self.delete_record(r))

            self.table.setCellWidget(row_index, 3, QWidget())
            button_layout = QHBoxLayout()
            button_layout.addWidget(edit_button)
            button_layout.addWidget(delete_button)
            button_layout.setContentsMargins(0, 0, 0, 0)
            self.table.cellWidget(row_index, 3).setLayout(button_layout)

    def show_context_menu(self, pos):
        index = self.table.indexAt(pos)
        if not index.isValid():
            return

        context_menu = QMenu(self)
        edit_action = context_menu.addAction("Edit")
        delete_action = context_menu.addAction("Delete")

        action = context_menu.exec_(self.table.viewport().mapToGlobal(pos))

        if action == edit_action:
            self.edit_record(index.row())
        elif action == delete_action:
            self.delete_record(index.row())

    def add_data(self):
        dialog = AddRecordDialog(self)
        if dialog.exec_():
            date, count, note = dialog.record_data
            insert_data(date, count, note)
            self.populate_table()
            self.update_weekly_plot()
            self.update_monthly_plot()
            self.update_yearly_plot()

    def edit_record(self, row):
        date_item = self.table.item(row, 0)
        count_item = self.table.item(row, 1)
        note_item = self.table.item(row, 2)

        dialog = AddRecordDialog(self, date_item.text(), int(count_item.text()), note_item.text())
        if dialog.exec_():
            new_date, new_count, new_note = dialog.record_data
            update_data(date_item.text(), new_count, new_note)
            self.populate_table()
            self.update_weekly_plot()
            self.update_monthly_plot()
            self.update_yearly_plot()

    def delete_record(self, row):
        date_item = self.table.item(row, 0)
        result = QMessageBox.question(self, "Delete Record",
                                      f"Are you sure you want to delete the record for {date_item.text()}?",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if result == QMessageBox.Yes:
            delete_data(date_item.text())
            self.populate_table()
            self.update_weekly_plot()
            self.update_monthly_plot()
            self.update_yearly_plot()

    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()


if __name__ == "__main__":
    create_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
