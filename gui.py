import sys
import pandas as pd
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
    QLineEdit, QLabel, QPushButton, QFileDialog, QMessageBox, 
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView, QAbstractItemView,
    QCheckBox, QComboBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant
from PyQt5.QtGui import QColor, QBrush, QFont

from iis_parser import IISLogParser

STYLESHEET = """
QMainWindow {
    background-color: #f3f2f1;
}
QSplitter::handle {
    background-color: #e1dfdd;
    border: none;
}
QTreeWidget {
    background-color: white;
    border: none;
    border-right: 1px solid #e1dfdd;
    font-size: 13px;
}
QTreeWidget::item {
    padding: 6px;
}
QTableView {
    background-color: white;
    border: 1px solid #e1dfdd;
    gridline-color: #f3f2f1;
    selection-background-color: #cce8ff;
    selection-color: black;
    font-size: 13px;
}
QHeaderView::section {
    background-color: #faf9f8;
    padding: 8px;
    border: none;
    border-right: 1px solid #e1dfdd;
    border-bottom: 2px solid #0078d4;
    font-weight: bold;
    color: #323130;
}
QLineEdit {
    padding: 8px 12px;
    border: 1px solid #8a8886;
    border-radius: 4px;
    background-color: white;
    font-size: 14px;
}
QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}
QPushButton#openLogBtn {
    background-color: #0078d4;
    color: white;
}
QPushButton:hover {
    background-color: #106ebe;
}
QLabel#titleLabel {
    font-size: 20px;
    font-weight: bold;
    color: #323130;
}
"""

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
            
        val = self._data.iloc[index.row(), index.column()]
        col_name = self._data.columns[index.column()]
        
        if role == Qt.DisplayRole:
            # We don't display NaT or NaN
            if pd.isna(val):
                return ""
            return str(val)
            
        if role == Qt.BackgroundRole:
            if col_name == 'sc-status':
                try:
                    status = int(val)
                    if status >= 500:
                        return QBrush(QColor('#e81123')) # Red
                    elif status >= 400:
                        return QBrush(QColor('#d83b01')) # Orange/Warning
                    elif status >= 300:
                        return QBrush(QColor('#ffb900')) # Yellow
                    else:
                        return QBrush(QColor('#107c10')) # Green
                except:
                    pass
            elif col_name == 'Device-Type':
                if val == 'Mobile':
                    return QBrush(QColor('#0078d4'))
                elif val == 'Web':
                    return QBrush(QColor('#e3008c'))
                
        if role == Qt.ForegroundRole:
            if col_name in ('sc-status', 'Device-Type') and pd.notna(val):
                return QBrush(QColor('white'))
                
        if role == Qt.FontRole:
            if col_name in ('sc-status', 'Device-Type'):
                font = QFont()
                font.setBold(True)
                return font

        return QVariant()

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return str(self._data.columns[col])
        return QVariant()

class IISLogAnalyserApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Log Viewer")
        self.resize(1300, 800)
        self.setStyleSheet(STYLESHEET)
        
        self.parser = None
        self.full_df = None
        self.loaded_files = {}
        
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(main_widget)
        
        # Header Area
        header_widget = QWidget()
        header_widget.setObjectName("headerWidget")
        header_widget.setStyleSheet("#headerWidget { background-color: white; border-bottom: 1px solid #e1dfdd; }")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        title = QLabel("Log Viewer")
        title.setObjectName("titleLabel")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.lbl_stats = QLabel("Last 10 minutes (0 Logs)")
        self.lbl_stats.setStyleSheet("font-weight: bold; color: #0078d4; font-size: 14px;")
        header_layout.addWidget(self.lbl_stats)
        
        header_layout.addStretch()
        
        self.chk_combine = QCheckBox("Analyse Together")
        self.chk_combine.setChecked(False)
        self.chk_combine.toggled.connect(self.on_combine_toggled)
        header_layout.addWidget(self.chk_combine)
        
        btn_open = QPushButton("Open Log Files")
        btn_open.setObjectName("openLogBtn")
        btn_open.clicked.connect(self.open_file)
        header_layout.addWidget(btn_open)
        
        btn_open_folder = QPushButton("Open Folder")
        btn_open_folder.setObjectName("openLogBtn") # Re-use same styling
        btn_open_folder.clicked.connect(self.open_folder)
        header_layout.addWidget(btn_open_folder)
        
        main_layout.addWidget(header_widget)
        
        # Splitter Layout
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter, 1)
        
        # Sidebar
        self.sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        file_list_header = QLabel("LOADED FILES")
        file_list_header.setStyleSheet("font-weight: bold; font-size: 12px; padding: 15px; color: #605e5c;")
        sidebar_layout.addWidget(file_list_header)
        
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(150)
        self.file_list.setStyleSheet("border: none; border-bottom: 1px solid #e1dfdd; background-color: white; font-size: 13px;")
        self.file_list.itemChanged.connect(self.on_file_list_changed)
        sidebar_layout.addWidget(self.file_list)
        
        filter_header = QLabel("FILTERS")
        filter_header.setStyleSheet("font-weight: bold; font-size: 12px; padding: 15px; color: #605e5c;")
        sidebar_layout.addWidget(filter_header)
        
        self.filter_tree = QTreeWidget()
        self.filter_tree.setHeaderHidden(True)
        self.filter_tree.itemChanged.connect(self.on_filter_changed)
        sidebar_layout.addWidget(self.filter_tree)
        
        self.splitter.addWidget(self.sidebar_widget)
        
        # Main Content Area
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)
        
        # Chart
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', '#605e5c')
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setFixedHeight(180)
        self.plot_widget.getAxis('left').setTicks([]) 
        self.plot_widget.getAxis('bottom').setTicks([])
        self.plot_widget.setStyleSheet("border: 1px solid #e1dfdd;")
        right_layout.addWidget(self.plot_widget)
        
        # Search & Active Filters
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search logs... (e.g. failure)")
        self.search_box.textChanged.connect(self.apply_filters)
        search_layout.addWidget(self.search_box)
        
        btn_clear = QPushButton("Clear Filters")
        btn_clear.setStyleSheet("background-color: white; color: #0078d4; border: 1px solid #0078d4;")
        btn_clear.clicked.connect(self.clear_filters)
        search_layout.addWidget(btn_clear)
        
        right_layout.addLayout(search_layout)
        
        # Table
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setShowGrid(False)
        self.table_view.setAlternatingRowColors(True)
        # Higher rows to make room to look nice
        self.table_view.verticalHeader().setDefaultSectionSize(35)
        
        right_layout.addWidget(self.table_view)
        
        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([300, 1000])

    def open_file(self):
        options = QFileDialog.Options()
        file_names, _ = QFileDialog.getOpenFileNames(
            self, "Open IIS Log Files", "", "Log Files (*.log);;All Files (*)", options=options)
        
        if file_names:
            self.load_multiple_files(file_names)

    def open_folder(self):
        options = QFileDialog.Options()
        folder_path = QFileDialog.getExistingDirectory(self, "Select Directory containing Log Files", options=options)
        
        if folder_path:
            import os
            # Find all .log files in the directory
            file_names = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.log')]
            if not file_names:
                QMessageBox.warning(self, "No Logs Found", f"No .log files were found in the selected folder.")
                return
            self.load_multiple_files(file_names)

    def load_multiple_files(self, filepaths):
        new_files_count = 0
        for filepath in filepaths:
            if filepath in self.loaded_files:
                continue
            try:
                parser = IISLogParser(filepath)
                df = parser.parse()
                df['Source-File'] = filepath.split('/')[-1]
                self.loaded_files[filepath] = df
                new_files_count += 1
            except Exception as e:
                print(f"Failed to load {filepath}: {e}")
                
        if not self.loaded_files:
            QMessageBox.critical(self, "Error", "No valid log files could be loaded.")
            return
            
        if new_files_count > 0:
            self.update_file_list()

    def update_file_list(self):
        # Capture existing selections
        previously_checked = set()
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.checkState() == Qt.Checked:
                previously_checked.add(item.data(Qt.UserRole))
                
        self.file_list.blockSignals(True)
        self.file_list.clear()
        
        # Sort files by filename alphabetically
        sorted_files = sorted(self.loaded_files.keys(), key=lambda path: path.split('/')[-1].lower())
        
        for filepath in sorted_files:
            filename = filepath.split('/')[-1]
            item = QListWidgetItem(filename)
            item.setData(Qt.UserRole, filepath)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            # Only check if it was checked before. 
            # We don't auto-check new files just because we are in combined mode.
            if filepath in previously_checked:
                 item.setCheckState(Qt.Checked)
            else:
                 item.setCheckState(Qt.Unchecked)
            self.file_list.addItem(item)
            
        # Ensure at least one is checked if not empty
        checked_count = sum(1 for i in range(self.file_list.count()) if self.file_list.item(i).checkState() == Qt.Checked)
        if checked_count == 0 and self.file_list.count() > 0:
            self.file_list.item(0).setCheckState(Qt.Checked)
                
        self.file_list.blockSignals(False)
        self.refresh_data_view()

    def on_combine_toggled(self, checked):
        if not self.loaded_files:
            return
            
        self.file_list.blockSignals(True)
        if not checked:
            # Enforce single selection: Uncheck all except the first currently checked one
            found_checked = False
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                if item.checkState() == Qt.Checked and not found_checked:
                    found_checked = True
                else:
                    item.setCheckState(Qt.Unchecked)
            if not found_checked and self.file_list.count() > 0:
                self.file_list.item(0).setCheckState(Qt.Checked)
        # else: if checked, don't do anything, just allow multiple selection now
                
        self.file_list.blockSignals(False)
        self.refresh_data_view()
            
    def on_file_list_changed(self, item):
        if not self.chk_combine.isChecked():
            # Enforce single selection
            if item.checkState() == Qt.Checked:
                self.file_list.blockSignals(True)
                for i in range(self.file_list.count()):
                    other_item = self.file_list.item(i)
                    if other_item != item:
                        other_item.setCheckState(Qt.Unchecked)
                self.file_list.blockSignals(False)
            else:
                # Prevent unchecking the last item if not combined
                item.setCheckState(Qt.Checked)
                return
        self.refresh_data_view()

    def refresh_data_view(self):
        if not self.loaded_files:
            return
            
        selected_dfs = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.checkState() == Qt.Checked:
                filepath = item.data(Qt.UserRole)
                selected_dfs.append(self.loaded_files[filepath])
                
        if not selected_dfs:
            self.full_df = pd.DataFrame()
            self.update_view(self.full_df)
            return
            
        self.full_df = pd.concat(selected_dfs, ignore_index=True)
        self.populate_sidebar(self.full_df)
        self.apply_filters()

    def populate_sidebar(self, df):
        self.filter_tree.blockSignals(True)
        self.filter_tree.clear()
        
        # We will parse these columns into generic grouped filters
        groups = {
            'sc-status': 'Level / Status',
            'cs-method': 'Method',
            'Device-Type': 'Device Type',
            'cs-username': 'User',
            's-ip': 'Server IP'
        }
        
        for col, title in groups.items():
            if col in df.columns:
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) == 0:
                    continue
                    
                parent = QTreeWidgetItem(self.filter_tree, [f"{title} ({len(unique_vals)})"])
                parent.setExpanded(True)
                
                # Make parent bold
                font = parent.font(0)
                font.setBold(True)
                parent.setFont(0, font)

                for val in sorted(unique_vals):
                    # Count occurrences
                    count = (df[col] == val).sum()
                    child = QTreeWidgetItem(parent, [f"{val}"])
                    
                    # Add unselectable count data
                    lbl = QLabel(str(count))
                    lbl.setStyleSheet("color: #a19f9d; font-size: 11px; margin-right: 5px;")
                    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    
                    child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                    child.setCheckState(0, Qt.Unchecked)
                    child.setData(0, Qt.UserRole, (col, val))
                    
                    self.filter_tree.setItemWidget(child, 0, None)
                    # No easy way to put rigth aligned widget in same col without custom item, we just append it
                    child.setText(0, f"{val}  ({count})")
                    
        self.filter_tree.blockSignals(False)

    def on_filter_changed(self, item, column):
        self.apply_filters()

    def clear_filters(self):
        self.search_box.clear()
        self.filter_tree.blockSignals(True)
        root = self.filter_tree.invisibleRootItem()
        for i in range(root.childCount()):
            group = root.child(i)
            for j in range(group.childCount()):
                child = group.child(j)
                child.setCheckState(0, Qt.Unchecked)
        self.filter_tree.blockSignals(False)
        self.apply_filters()

    def apply_filters(self):
        if self.full_df is None:
            return
            
        filtered_df = self.full_df.copy()
        
        root = self.filter_tree.invisibleRootItem()
        active_filters = {}
        for i in range(root.childCount()):
            group = root.child(i)
            col_name = None
            checked_vals = []
            for j in range(group.childCount()):
                child = group.child(j)
                if child.checkState(0) == Qt.Checked:
                    col, val = child.data(0, Qt.UserRole)
                    col_name = col
                    checked_vals.append(val)
            if col_name and checked_vals:
                active_filters[col_name] = checked_vals
                
        for col, vals in active_filters.items():
            filtered_df = filtered_df[filtered_df[col].isin(vals)]
            
        search_text = self.search_box.text().strip().lower()
        if search_text:
            mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
            # Exclude Datetime from string search to avoid slow processing
            cols_to_search = [c for c in filtered_df.columns if c != 'Datetime']
            for col in cols_to_search:
                mask = mask | filtered_df[col].astype(str).str.lower().str.contains(search_text, regex=False, na=False)
            filtered_df = filtered_df[mask]
            
        self.update_view(filtered_df)

    def update_view(self, df):
        model = PandasModel(df)
        self.table_view.setModel(model)
        
        self.lbl_stats.setText(f"Viewing {len(df)} logs")
        
        # Only hide Datetime column from table view
        if 'Datetime' in df.columns:
            idx = df.columns.get_loc('Datetime')
            self.table_view.setColumnHidden(idx, True)

        self.plot_widget.clear()
        
        if 'Datetime' in df.columns and not df.empty:
            valid_times = df['Datetime'].dropna()
            if not valid_times.empty:
                # Group by minute to build timeline
                counts = valid_times.dt.floor('Min').value_counts().sort_index()
                if not counts.empty:
                    x = np.arange(len(counts))
                    y = counts.values
                    bg = pg.BarGraphItem(x=x, height=y, width=0.8, brush='#00a4ef')
                    self.plot_widget.addItem(bg)

def main():
    app = sys.modules.get('PyQt5.QtWidgets').QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = IISLogAnalyserApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
