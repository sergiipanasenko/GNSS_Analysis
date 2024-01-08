from PyQt5 import QtWidgets
from dTEC_viewer import DTECViewerForm


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = DTECViewerForm()
    MainWindow.show()
    sys.exit(app.exec_())
