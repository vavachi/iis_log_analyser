# User Guide: IIS Log Analyser Deep Dive

This document provides a detailed explanation of the internal workings and operational flow of the IIS Log Analyser application.

## 1. Technical Architecture

The application follows a modular design, separating the raw log parsing from the graphical presentation.

### 1.1 Core Parser (`iis_parser.py`)
The parser is built to handle the W3C Extended Log File Format. 
- **Header Detection**: It scans for the `#Fields:` prefix to dynamically map column indices to field names. 
- **Performance**: Uses `pandas` for bulk data loading, ensuring that even logs with thousands of entries are loaded within milliseconds.
- **Device Classification**: 
  - It analyzes the `cs(User-Agent)` field.
  - Classification logic:
    - **Bot**: Matches known crawler strings (e.g., Googlebot, Bingbot).
    - **Mobile**: Matches common mobile identifiers (e.g., iPhone, Android, Mobile).
    - **Web**: Defaults to web if neither of the above are matched but a User-Agent is present.

### 1.2 GUI Engine (`gui.py`)
Implemented using **PyQt5**, the GUI utilizes a custom `PandasModel` (inheriting from `QAbstractTableModel`) to bind the pandas DataFrame directly to the `QTableView`. This allows for highly efficient rendering and smooth scrolling.

---

## 2. Feature Workflows

### 2.1 Multi-File & Folder Management
The application manages multiple logs through a central `loaded_files` dictionary.
- **Cumulative Loading**: Opening files or folders adds to the `loaded_files` collection without clearing the current session.
- **Sorting**: The sidebar list is sorted alphabetically by filename for quick identification.

### 2.2 Analysis Modes
- **Single File Analysis**: (Default) Clicking a checkbox in the "LOADED FILES" sidebar swaps the active dataset to that specific file.
- **Analyse Together**: When enabled, the application uses `pd.concat` to merge all checked DataFrames. This re-calculates all sidebar counts and timeline charts across the entire combined dataset.

### 2.3 Filtering System
The filtering is decentralized but unified. 
- **Sidebar Filters**: Each group (Status, Method, etc.) allows multi-selection via checkboxes.
- **Global Search**: A real-time search box wraps a string-contains check across all visible log columns (excluding Datetime for performance).
- **Instant Updates**: Any change in the sidebar or search box triggers a re-slice of the master DataFrame, followed by a model reset on the table.

---

## 3. Visualization

### 3.1 Timeline Chat (`pyqtgraph`)
- The top chart displays log frequency.
- It calculates `value_counts()` on the `Datetime` column, floored to the nearest minute.
- This gives an immediate visual indicator of traffic spikes or server failure windows.

### 3.2 UI Styling & Badges
- **Status Badges**: The `QTableView` uses custom background roles to color-code response codes:
  - **Green**: 2xx (Success)
  - **Yellow**: 3xx (Redirect)
  - **Orange**: 4xx (Client Error)
  - **Red**: 5xx (Server Error)
- **Device Badges**: Distinct colors for Mobile (Blue) and Web (Pink) traffic types.

---

## 4. Troubleshooting
- **Missing Fields**: If a log file doesn't contain `#Fields:`, the parser will fail. Ensure your IIS logs are in the standard W3C format.
- **Permissions**: Ensure the user has read permissions for the target `.log` files or directories.
