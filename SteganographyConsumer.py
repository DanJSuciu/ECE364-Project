from PySide.QtGui import *
from PySide.QtCore import *
from SteganographyGUI import *
import Steganography
import sys
import scipy
from scipy import ndimage


class Consumer(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(Consumer, self).__init__(parent)
        self.setupUi(self)
        self.compression = 0
        self.chkApplyCompression.stateChanged.connect(self.compressionCheck)
        self.slideCompression.valueChanged.connect(self.slider)
        self.viewPayload1 = Viewer(self.grpPayload1)
        self.viewPayload1.setGeometry(QtCore.QRect(10, 40, 361, 281))
        self.viewPayload1.scene_var.changed.connect(self.newImage)
        self.viewCarrier1 = Viewer(self.grpCarrier1)
        self.viewCarrier1.setGeometry(QtCore.QRect(10, 40, 361, 281))
        self.viewCarrier2 = Viewer(self.grpCarrier2)
        self.viewCarrier2.setGeometry(QtCore.QRect(10, 40, 361, 281))

    def compressionCheck(self):
        if self.chkApplyCompression.isChecked() is True:
            self.slideCompression.setEnabled(True)
            self.txtCompression.setEnabled(True)
        else:
            self.slideCompression.setEnabled(False)
            self.txtCompression.setEnabled(False)

    def slider(self):
        self.compression = self.slideCompression.value()
        self.newImage()
        self.txtCompression.setText("{0}".format(self.compression))

    def newImage(self):
        try:
            payload = Steganography.Payload(self.viewPayload1.imageArray, self.compression, None)
            self.txtPayloadSize.setText("{0}".format(len(payload.xml)))
        except ValueError:
            self.txtPayloadSize.setText("0")


class Viewer(QtGui.QGraphicsView):
    def __init__(self, parent):
        super(Viewer, self).__init__(parent)
        self.setAcceptDrops(True)
        self.imageArray = None
        self.scene_var = QGraphicsScene()

    def dragEnterEvent(self, obj):
        if obj.mimeData().hasUrls:
            obj.accept()
        else:
            obj.ignore()

    def dragMoveEvent(self, obj):
        if obj.mimeData().hasUrls:
            obj.accept()
        else:
            obj.ignore()

    def dropEvent(self, obj):
        if obj.mimeData().hasUrls:
            obj.accept()
            path = obj.mimeData().urls()[0].toLocalFile()
            pixmap = QtGui.QPixmap(path)
            self.scene_var.clear()
            self.scene_var.addPixmap(pixmap)
            self.setScene(self.scene_var)
            self.fitInView(self.scene_var.itemsBoundingRect(), Qt.KeepAspectRatio)
            self.imageArray = ndimage.imread(path)
        else:
            obj.ignore()


if __name__ == "__main__":
    currentApp = QApplication(sys.argv)
    currentForm = Consumer()

    currentForm.show()
    currentApp.exec_()
