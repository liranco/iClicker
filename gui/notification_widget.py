import sys
from PySide.QtGui import *
from PySide.QtCore import *


NOTIFICATION_SIZE_WIDTH = 440
NOTIFICATION_SIZE_RATIO = 2
NOTIFICATION_SIZE = QSize(NOTIFICATION_SIZE_WIDTH, NOTIFICATION_SIZE_WIDTH / NOTIFICATION_SIZE_RATIO)


class TestWidget(QDialog):
    def __init__(self):
        super(TestWidget, self).__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.notification_view = NotificationView(self)
        layout.addWidget(self.notification_view)
        self.setLayout(layout)
        # Create a border-less transparent window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setStyleSheet('background:transparent;')
        self.setStyleSheet('background:rgba(89, 255, 192, 100);')
        # Set it's size
        self.setGeometry(QRect(QPoint(0, 0), NOTIFICATION_SIZE))
        msg_geo = self.geometry()  # type: QRect
        # Move it to the bottom right corner
        # noinspection PyArgumentList
        msg_geo.moveBottomRight(QApplication.desktop().availableGeometry().bottomRight())
        msg_geo.adjust(-20, -20, 0, 0)
        self.move(msg_geo.topLeft())

    def mouseDoubleClickEvent(self, event):
        self.close()


class NotificationView(QGraphicsView):
    def __init__(self, parent, color=None):
        super(NotificationView, self).__init__(parent)
        # noinspection PyCallByClass,PyTypeChecker
        self.color = color or QColor.fromRgb(0x95, 0xc8, 0x01)
        self._scene = QGraphicsScene(self)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setScene(self._scene)
        self.setStyleSheet("QGraphicsView { border-style: none; }")
        self._inner_rect = QRect(QPoint(0, 0), NOTIFICATION_SIZE * 0.8)
        self.make_background()
        self.make_arrow()

    def make_background(self):
        gradient = QRadialGradient(self._inner_rect.center(), 200)
        gradient.setColorAt(0, Qt.white)
        gradient.setColorAt(1, Qt.gray)
        bg_rect = self._scene.addRect(self._inner_rect, pen=Qt.NoPen, brush=QBrush(gradient))  # type: QGraphicsRectItem
        bg_rect.setZValue(-100)
        bg_shadow_rect = QRect(0, 0, self._inner_rect.width() + 30, self._inner_rect.height() * 0.10)
        bg_shadow_rect.moveCenter(self._inner_rect.center())
        bg_shadow_rect.moveBottom(self._inner_rect.bottom() + 5)
        bg_shadow = self._scene.addRect(bg_shadow_rect, pen=Qt.NoPen, brush=QBrush(Qt.black))  # type: QGraphicsRectItem
        bg_shadow.effect = QGraphicsBlurEffect()
        bg_shadow.effect.setBlurRadius(20)
        bg_shadow.setGraphicsEffect(bg_shadow.effect)
        bg_shadow.setZValue(bg_rect.zValue() - 1)

    def make_arrow(self):
        arrow_polygon = QPolygonF()
        arrow_middle_point = QPointF(self._inner_rect.width() / 3.5, self._inner_rect.center().y())
        arrow_polygon += self._inner_rect.topLeft()
        arrow_polygon += arrow_middle_point
        arrow_polygon += self._inner_rect.bottomLeft()
        arrow_gradient = QLinearGradient(0, 0, arrow_middle_point.x(), 0)
        arrow_gradient.setColorAt(0, self.color.darker())
        arrow_gradient.setColorAt(0.5, self.color)
        arrow = self._scene.addPolygon(arrow_polygon, pen=Qt.NoPen, brush=QBrush(arrow_gradient))
        arrow_shadow_polygon = QPolygonF()
        arrow_shadow_polygon += self._inner_rect.topLeft() + QPoint(5, 5)
        arrow_shadow_polygon += arrow_middle_point + QPointF(0, 10)
        arrow_shadow_polygon += self._inner_rect.bottomLeft() + QPoint(5, 0)
        arrow_shadow = self._scene.addPolygon(arrow_shadow_polygon, pen=Qt.NoPen, brush=QBrush(QColor(Qt.black)))
        arrow_shadow.setZValue(arrow.zValue() - 1)
        arrow_shadow.effect = QGraphicsBlurEffect()
        arrow_shadow.effect.setBlurRadius(10)
        arrow_shadow.setGraphicsEffect(arrow_shadow.effect)

        circle_size = arrow_middle_point.x() / 2
        circle_rect = QRectF(0, 0, circle_size, circle_size)
        circle_rect.moveCenter(QPointF(arrow_middle_point.x() / 2 - circle_size / 4, arrow_middle_point.y()))
        self._scene.addEllipse(circle_rect, pen=QPen(self.color, 4), brush=QBrush(Qt.white))


def main():
    app = QApplication(sys.argv)
    a = TestWidget()
    a.show()
    app.exec_()


if __name__ == '__main__':
    main()