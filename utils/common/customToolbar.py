from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PySide6.QtWidgets import QFileDialog

class CustomToolbar(NavigationToolbar):
    def save_figure(self, *args):
        file_dialog = QFileDialog(self)
        file_dialog.setDefaultSuffix("png")
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilters(["PNG Files (*.png)", "All Files (*)"])

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.canvas.figure.savefig(file_path, dpi=300)
