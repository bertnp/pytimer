"""PyTimer: A minimalistic cross-platform timer and stopwatch widget

http://github.com/bertnp/pytimer
"""

import math
import functools
from PyQt5.QtCore import QTimer, QTime, Qt, QElapsedTimer
from PyQt5.QtWidgets import QApplication, QLCDNumber, QAction, QDialog
from PyQt5.QtWidgets import QVBoxLayout, QTimeEdit, QDialogButtonBox
from PyQt5.QtWidgets import QMessageBox, QWidget
from PyQt5.QtGui import QRegion

""" Main window class"""
class Stopwatch(QLCDNumber):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setKeyBinds()

        # percentage of the standard 400x150 pixel size
        self.parent = parent
        self.size = 100
        self.base_w = 240
        self.base_h = 58
        self.opacity = 0.8
        self.recordedTime = 0
        self.timeMode = 1 # 0 = count down, 1 = count up
        self.setPaused(True)
        # default timer duration (in ms)
        self.baseTime = 3*1000

        self.ontop = False
        self.baseFlags = Qt.WindowFlags()
        self.baseFlags |= Qt.Window

        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setWindowFlags(self.baseFlags)
        self.changeSize(0)
        self.toggleAlwaysOnTop()
        self.setSegmentStyle(QLCDNumber.Flat)
        self.setDigitCount(12)
        self.display('00:00:00:000')
        self.setStyleSheet('background: black; color: green;')
        self.setWindowTitle('PyTimer')
        self.setWindowOpacity(self.opacity)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.ringTimer)
        self.timer.setSingleShot(True)

        self.stopwatch = QElapsedTimer()

        self.displayTimer = QTimer(self)
        self.displayTimer.timeout.connect(self.showTime)
        self.displayTimer.start(50)


    def setKeyBinds(self):
        """ Set shortcut keys
        q : Quit
        t : Timer mode
        s : Stopwatch mode
        k : Increase size
        j : Decrease size
        r : Reset counter
        p : Pause counter
        c : Set countdown time
        a : Toggle always on top
        + : Increase opacity
        - : Decrease opacity
        """
        quitAction = QAction("&Quit", self, shortcut='q',
                triggered=self.quitApp)
        timerModeAction = QAction("&Timer Mode", self, shortcut='t',
                triggered=functools.partial(self.setMode, 0))
        stopwatchModeAction = QAction("&Stopwatch Mode", self, shortcut='s',
                triggered=functools.partial(self.setMode, 1))
        increaseSizeAction = QAction("Increase Size", self, shortcut='k',
                triggered=functools.partial(self.changeSize, 1))
        decreaseSizeAction = QAction("Decrease Size", self, shortcut='j',
                triggered=functools.partial(self.changeSize, -1))
        resetCounterAction = QAction("&Reset Counter", self, shortcut='r',
                triggered=self.resetCounter)
        pauseCounterAction = QAction("&Pause Counter", self, shortcut='p',
                triggered=self.pauseCounter)
        setCounterAction = QAction("Set Counter", self, shortcut='c',
                triggered=self.setCounter)
        toggleAlwaysTopAction = QAction("Toggle &Always on Top", self,
                shortcut='a', triggered=self.toggleAlwaysOnTop)
        self.addAction(quitAction)
        self.addAction(timerModeAction)
        self.addAction(stopwatchModeAction)
        self.addAction(increaseSizeAction)
        self.addAction(decreaseSizeAction)
        self.addAction(resetCounterAction)
        self.addAction(pauseCounterAction)
        self.addAction(setCounterAction)
        self.addAction(toggleAlwaysTopAction)

    def quitApp(self):
        QApplication.instance().quit()


    def toggleAlwaysOnTop(self):
        flags = Qt.WindowFlags()
        flags |= self.baseFlags

        if self.ontop:
            self.ontop = False
        else:
            self.ontop = True
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()


    def keyPressEvent(self, event):
        # increase opacity
        if event.key() == Qt.Key_Plus:
            self.opacity += 0.1
            if self.opacity > 1:
                self.opacity = 1
            self.setWindowOpacity(self.opacity)
        # decrease opacity
        elif event.key() == Qt.Key_Minus:
            self.opacity -= 0.1
            if self.opacity < 0.1:
                self.opacity = 0.1
            self.setWindowOpacity(self.opacity)


    def ringTimer(self):
        self.recordedTime = 0
        self.setPaused(True)
        # TODO: play a sound
        reply = QMessageBox.information(None, "Time is up!", "Time is up!")


    def setPaused(self, state):
        self.isPaused = state
        self.needsUpdate = True


    def setMode(self, mode):
        self.timeMode = mode
        self.recordedTime = 0
        self.setPaused(True)


    """Convert milliseconds to a tupple
    Tupple format: (hours, minutes, seconds, milliseconds)
    """
    def ms2tupple(self, ms):

        h,ms = divmod(ms, 3600000)
        m,ms = divmod(ms, 60000)
        s,ms = divmod(ms, 1000)
        return (h, m, s, ms)


    def showTime(self):
        if self.needsUpdate:
            if self.isPaused:
                time = self.recordedTime
                self.needsUpdate = False
            elif self.timeMode == 0:
                time = self.timer.remainingTime()
            elif self.timeMode == 1:
                time = self.stopwatch.elapsed() + self.recordedTime

            time_tupple = self.ms2tupple(time)
            s = '{0:0=2d}:{1:0=2d}:{2:0=2d}:{3:0=3d}'.format(*time_tupple)
            self.display(s)


    """Allow dragging of window"""
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPosition = \
                    event.globalPos() - self.frameGeometry().topLeft()
            event.accept()


    """Allow dragging of window"""
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.dragPosition)
            event.accept()


    """Show timer config dialog with baseTime"""
    def setCounter(self):
        editor_time = self.ms2tupple(self.baseTime)
        time, ok = TimeDialog.getTime(time=QTime(*editor_time))
        if ok:
            self.baseTime = (
                    1000*(time.hour()*3600 + time.minute()*60 + time.second()))


    """Toggle pause state"""
    def pauseCounter(self):
        # unpause if already paused
        if self.isPaused:
            if self.timeMode == 0:
                self.timer.start(self.recordedTime)
            elif self.timeMode == 1:
                self.stopwatch.restart()
            self.setPaused(False)
        # pause if timer is running
        else:
            if self.timeMode == 0:
                self.recordedTime = self.timer.remainingTime()
            elif self.timeMode == 1:
                self.recordedTime = (self.stopwatch.elapsed()
                                     + self.recordedTime)
            self.setPaused(True)


    """Change window size"""
    def changeSize(self, sign):
        self.size += sign*5
        w = math.floor(self.size/100.0*self.base_w)
        h = math.floor(self.size/100.0*self.base_h)
        self.resize(w, h)


    """Reset timer to baseTime or stopwatch to 0"""
    def resetCounter(self):
        self.setPaused(False)
        self.recordedTime = 0
        if self.timeMode == 0:
            self.timer.start(self.baseTime)
        if self.timeMode == 1:
            self.stopwatch.restart()

    def resizeEvent(self, event):
        mask = QRegion(0, 0, self.width(), self.height(), QRegion.Rectangle)
        self.setMask(mask)


"""Dialog box for setting base time"""
class TimeDialog(QDialog):
    def __init__(self, parent=None, time=QTime(0,10,0)):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.datetime = QTimeEdit(parent=self, time=time)
        self.datetime.setDisplayFormat('hh:mm:ss')
        layout.addWidget(self.datetime)

        buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def dateTime(self):
        return self.datetime.dateTime()

    # static method for launching dialog
    @staticmethod
    def getTime(parent=None, time=QTime(0,10,0)):
        dialog = TimeDialog(parent=parent, time=time)
        result = dialog.exec_()
        date = dialog.dateTime()
        return (date.time(), result == QDialog.Accepted)


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    watch = Stopwatch()
    watch.show()
    sys.exit(app.exec())

