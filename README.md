# IIS Log Analyser

A modern, high-performance desktop application for parsing, filtering, and analyzing IIS (W3C format) log files. Built with Python, PyQt5, and pandas, this tool allows you to visualize traffic trends and drill down into specific logs with ease.


## Features

- **Robust W3C Parsing**: Automatically handles `#Fields` directives and skips comments.
- **Multi-File & Folder Support**: Load multiple `.log` files or entire directories at once.
- **Combined Analysis**: Toggle "Analyse Together" to merge multiple logs into a single timeline.
- **Device Classification**: Automatically detects and separates **Web**, **Mobile**, and **Bot** traffic using User-Agent analysis.
- **Interactive Time-Series Chart**: Visualize log volume trends over time (per minute).
- **Advanced Filtering**:
  - Checkbox-based sidebar for Status Codes, Methods, Device Types, Users, and Server IPs.
  - Global real-time search across all log fields.
  - Sidebar counts for every filter value.
- **Color-Coded View**: Instant visual feedback for HTTP status codes (2xx, 4xx, 5xx) and Device Types.
- **Cumulative Loading**: Add more files to your session without losing previous data.

## Installation

### Prerequisites

- Python 3.8 or higher.

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/IISLogAnalyser.git
   cd LogAnalyser
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Launch the application**:
   ```bash
   python main.py
   ```

2. **Load Logs**:
   - Use **"Open Log Files"** to select specific files.
   - Use **"Open Folder"** to automatically load all `.log` files in a directory.

3. **Analyze**:
   - Check/Uncheck files in the **LOADED FILES** sidebar.
   - Use the **FILTERS** sidebar to narrow down specific status codes or methods.
   - Toggle **Analyse Together** to see a unified view of your selected logs.

## Technologies Used

- **GUI**: [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- **Data Engine**: [pandas](https://pandas.pydata.org/)
- **Visualizations**: [pyqtgraph](https://www.pyqtgraph.org/)
- **Numeric Ops**: [numpy](https://numpy.org/)

## License

MIT License. See `LICENSE` for details.
