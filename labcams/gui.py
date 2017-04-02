# Qt imports
import sys
import os
from .utils import display
from .cams import *
import cv2
import ctypes
try:
    from PyQt5.QtWidgets import (QWidget,
                                 QApplication,
                                 QGridLayout,
                                 QFormLayout,
                                 QVBoxLayout,
                                 QTabWidget,
                                 QCheckBox,
                                 QTextEdit,
                                 QSlider,
                                 QLabel,
                                 QAction,
                                 QMenuBar,
                                 QGraphicsView,
                                 QGraphicsScene,
                                 QGraphicsItem,
                                 QGraphicsLineItem,
                                 QGroupBox,
                                 QTableWidget,
                                 QMainWindow,
                                 QDockWidget,
                                 QFileDialog)
    from PyQt5.QtGui import QImage, QPixmap,QBrush,QPen,QColor
    from PyQt5.QtCore import Qt,QSize,QRectF,QLineF,QPointF,QTimer
    print("Using Qt5 framework.")
except:
    from PyQt4.QtGui import (QWidget,
                             QApplication,
                             QAction,
                             QMenuBar,
                             QGridLayout,
                             QFormLayout,
                             QVBoxLayout,
                             QCheckBox,
                             QTextEdit,
                             QSlider,
                             QLabel,
                             QGraphicsView,
                             QGraphicsScene,
                             QGraphicsItem,
                             QGraphicsLineItem,
                             QGroupBox,
                             QTableWidget,
                             QFileDialog,
                             QImage,
                             QPixmap)
    from PyQt4.QtCore import Qt,QSize,QRectF,QLineF,QPointF


class LabCamsGUI(QMainWindow):
    app = None
    cams = []
    def __init__(self,app = None, camDescriptions = []):
        super(LabCamsGUI,self).__init__()
        display('Starting labcams interface.')
        self.app = app
        self.cam_descriptions = camDescriptions
        # Init cameras
        self.cam_descriptions = range(3)
        for c,cam in enumerate(self.cam_descriptions):
            display("Connecting to " + str(c) + ' camera')
            self.cams.append(DummyCam())
            self.cams[-1].daemon = True
        self.resize(900,200)

        self.initUI()
        for cam in self.cams:
            cam.start()
            
    def experimentMenuTrigger(self,q):
        display(q.text()+ "clicked. ")
        
    def initUI(self):
        # Menu
        bar = self.menuBar()
        editmenu = bar.addMenu("Experiment")
        editmenu.addAction("New")
        editmenu.triggered[QAction].connect(self.experimentMenuTrigger)
        self.setWindowTitle("LabCams")
        self.tabs = []
        self.camwidgets = []
        for c,cam in enumerate(self.cams):
            self.tabs.append(QDockWidget("Camera: "+str(c),self))
            layout = QVBoxLayout()
            self.camwidgets.append(CamWidget(frame = np.zeros([200,200],dtype=np.float32)))
            self.tabs[-1].setWidget(self.camwidgets[-1])
            self.tabs[-1].setFloating(False)
            self.addDockWidget(Qt.RightDockWidgetArea,self.tabs[-1])
            display('Init view: ' + str(c))
        self.show()
        self.timer = QTimer()
        self.timer.timeout.connect(self.timerUpdate)
        self.timer.start(30)
        self.camframes = []
        for c,cam in enumerate(self.cams):
            self.camframes.append(np.frombuffer(cam.frame.get_obj(),
                                                dtype = ctypes.c_ubyte).reshape(
                                                    [cam.h,cam.w]))
    def timerUpdate(self):
        for c,frame in enumerate(self.camframes):
            self.camwidgets[c].image(frame)
class CamWidget(QWidget):
    def __init__(self,frame):
        super(CamWidget,self).__init__()
        self.scene=QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.image(np.array(frame))
        self.show()
    def image(self,image):
        self.scene.clear()
        frame = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_GRAY2BGR)
        self.qimage = QImage(frame, frame.shape[1], frame.shape[0], 
                             frame.strides[0], QImage.Format_RGB888)
        self.scene.addPixmap(QPixmap.fromImage(self.qimage))
        #self.view.fitInView(QRectF(0,0,
        #                           frame.shape[1],
        #                           frame.shape[0]),
        #                    Qt.KeepAspectRatio)
        self.scene.update()

def main():
    app = QApplication(sys.argv)
    w = LabCamsGUI(app = app)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
