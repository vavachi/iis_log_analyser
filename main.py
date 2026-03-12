import sys
from PyQt5.QtWidgets import QApplication
from gui import IISLogAnalyserApp

def main():
    app = QApplication(sys.argv)
    
    # Optional: Set a clean Fusion style
    app.setStyle("Fusion")
    
    window = IISLogAnalyserApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
