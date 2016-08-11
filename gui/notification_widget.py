import sys
from PySide.QtGui import *
from PySide.QtCore import *


NOTIFICATION_SIZE_WIDTH = 350
NOTIFICATION_SIZE_RATIO = 2
NOTIFICATION_SIZE = QSize(NOTIFICATION_SIZE_WIDTH, NOTIFICATION_SIZE_WIDTH / NOTIFICATION_SIZE_RATIO)


class TestWidget(QDialog):
    def __init__(self):
        super(TestWidget, self).__init__()
        layout = QBoxLayout(QBoxLayout.BottomToTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.notification_view = NotificationView(self)
        layout.addWidget(self.notification_view)
        layout.addSpacing(NOTIFICATION_SIZE.width() / 4)
        self.setLayout(layout)
        # Create a border-less transparent window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet('background:transparent;')
        # Set it's size
        self.setGeometry(QRect(QPoint(0, 0), QSize(NOTIFICATION_SIZE.width() * 1.2, NOTIFICATION_SIZE.height() * 1.6)))
        msg_geo = self.geometry()  # type: QRect
        # Move it to the bottom right corner
        # noinspection PyArgumentList
        msg_geo.moveBottomRight(QApplication.desktop().availableGeometry().bottomRight())
        self.move(msg_geo.topLeft())

        self.ani = QGraphicsBlurEffect()
        self.ani.setBlurRadius(0)
        self.notification_view.setGraphicsEffect(self.ani)
        self.animate = QPropertyAnimation(self.ani, 'blurRadius')
        self.animate.setStartValue(30)
        self.animate.setEndValue(0)
        self.animate.setDuration(500)
        self.animate.start()

        # self.ani2 = QGraphicsOpacityEffect()
        # self.ani2.setOpacity(0)
        # self.notification_view.setGraphicsEffect(self.ani)
        self.animate2 = QPropertyAnimation(self, 'windowOpacity')
        self.animate2.setStartValue(0)
        self.animate2.setEndValue(1)
        self.animate2.setDuration(200)
        self.animate2.start()

    def get_opacity(self):
        return self.windowOpacity()

    def set_opacity(self, value):
        return self.setWindowOpacity(value)

    opacity = Property(int, get_opacity, set_opacity)

    def mouseDoubleClickEvent(self, event):
        self.close()


class NotificationView(QGraphicsView):
    def __init__(self, parent, color=None):  # QColor.fromRgb(0x01, 0x64, 0xc9)):
        super(NotificationView, self).__init__(parent)
        # noinspection PyCallByClass,PyTypeChecker
        self.color = color or QColor.fromRgb(0x95, 0xc8, 0x01)  # type: QColor
        self._scene = QGraphicsScene(self)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setScene(self._scene)
        self.setStyleSheet("QGraphicsView { border-style: none; }")
        self._inner_rect = QRect(QPoint(0, 0), NOTIFICATION_SIZE)
        self.arrow_middle_point = QPointF(self._inner_rect.width() / 3.5, self._inner_rect.center().y())
        self.text_body_x = self.arrow_middle_point.x()
        self.circle_text = u'26\u00b0C'
        self._bg_rect_item = self.make_background()
        self.title_text_item = None
        arrow = self.create_arrow(self._inner_rect.topLeft(), self.arrow_middle_point, self._inner_rect.bottomLeft())
        self.make_text(self.circle_text, 15, self.make_circle(arrow))
        self.make_close_circle_button()
        self.make_title_text('Mazgan has been clicked!')
        self.make_body_text('Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt'
                            ' ut labore et dolore magna al')

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
        return bg_rect

    def create_arrow(self, a, b, c, position=None, rotation=None):
        # type: (QPoint, QPoint, QPoint) -> QGraphicsPolygonItem
        arrow_polygon = QPolygonF()
        arrow_polygon += a
        arrow_polygon += b
        arrow_polygon += c
        arrow_gradient = QLinearGradient(a.x(), 0, b.x(), 0)
        arrow_gradient.setColorAt(0, self.color.darker())
        arrow_gradient.setColorAt(0.5, self.color)
        arrow = QGraphicsPolygonItem(arrow_polygon)
        arrow.a, arrow.b, arrow.c = (a, b, c)
        arrow.setPen(Qt.NoPen)
        arrow.setBrush(QBrush(arrow_gradient))
        arrow_shadow_polygon = QPolygonF()
        arrow_shadow_polygon += a + QPoint(5, 5)
        arrow_shadow_polygon += b + QPoint(0, 10)
        arrow_shadow_polygon += c + QPoint(5, 0)
        arrow_shadow = QGraphicsPolygonItem(arrow_shadow_polygon, arrow)
        arrow_shadow.setParentItem(arrow)
        arrow_shadow.setPen(Qt.NoPen)
        arrow_shadow.setBrush(Qt.black)
        arrow_shadow.effect = QGraphicsBlurEffect()
        arrow_shadow.effect.setBlurRadius(10)
        arrow_shadow.setGraphicsEffect(arrow_shadow.effect)

        if rotation:
            arrow.setRotation(rotation)
            arrow_shadow.setRotation(rotation)
        if position:
            arrow.setPos(position)
            arrow_shadow.setPos(position)

        self._scene.addItem(arrow_shadow)
        self._scene.addItem(arrow)
        return arrow

    def make_circle(self, parent, custom_cls=None):
        circle_size = parent.b.x() / 2
        circle_rect = QRectF(0, 0, circle_size, circle_size)
        circle_rect.moveCenter(QPointF(parent.b.x() / 2 - circle_size / 4, parent.b.y()))
        cls = custom_cls or QGraphicsEllipseItem
        circle = cls(circle_rect, parent=parent)
        circle.setPen(QPen(self.color, circle_rect.width() / 15))
        circle.setBrush(Qt.white)
        return circle

    def make_text(self, text, size, parent, color=None, weight=None):
        color = color or self.color.darker().lighter()
        text_item = QGraphicsTextItem(text, parent)
        text_item.setFont(QFont('Calibri', size, weight=weight or QFont.Bold))
        text_item.setDefaultTextColor(color)
        text_rect = text_item.boundingRect()
        text_rect.moveCenter(parent.boundingRect().center())
        text_item.setPos(text_rect.topLeft())
        return text_item

    def make_close_circle_button(self):
        close_arrow = self.create_arrow(QPoint(0, 0),
                                        QPoint(35, 35),
                                        QPoint(0, 70),
                                        position=self._inner_rect.topRight() - QPoint(0, 10),
                                        rotation=90)

        close_circle = self.make_circle(close_arrow, CloseWindowButton)
        close_circle.set_window(self.parent())
        close_circle.setTransformOriginPoint(close_circle.boundingRect().center())
        close_circle.setRotation(-90)
        self.make_text('X', 12, close_circle)

    def make_title_text(self, text):
        text_item = self.make_text(text, 16, self._bg_rect_item)
        text_item.setPos(QPoint(self.text_body_x, self._inner_rect.height() / 5))
        text_item.setTextWidth(self._inner_rect.width() - self.text_body_x)
        self.title_text_item = text_item

    def make_body_text(self, text):
        text_item = self.make_text(text, 12, self._bg_rect_item, QColor(Qt.darkGray).darker(), QFont.Normal)
        text_item.setPos(QPoint(self.text_body_x, self.title_text_item.pos().y() + 30))
        text_item.setTextWidth(self._inner_rect.width() - self.text_body_x)


class CloseWindowButton(QGraphicsEllipseItem):
    def __init__(self, rect, parent):
        super(CloseWindowButton, self).__init__(rect, parent)
        self._window = None
        self.setCursor(Qt.PointingHandCursor)

    def set_window(self, window):
        self._window = window

    def mousePressEvent(self, event):
        self._window.close()
        super(CloseWindowButton, self).mousePressEvent(event)


def main():
    app = QApplication(sys.argv)
    a = TestWidget()
    a.show()
    app.exec_()


if __name__ == '__main__':
    main()