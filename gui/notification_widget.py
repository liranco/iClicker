from PySide.QtCore import *
from PySide.QtGui import *

from settings import BaseSettingsGroup

NOTIFICATION_SIZE_WIDTH = 350
NOTIFICATION_SIZE_RATIO = 2
NOTIFICATION_SIZE = QSize(NOTIFICATION_SIZE_WIDTH, NOTIFICATION_SIZE_WIDTH / NOTIFICATION_SIZE_RATIO)
# noinspection PyCallByClass,PyTypeChecker
DEFAULT_COLOR = QColor.fromRgb(0x95, 0xc8, 0x01)
DEFAULT_DURATION = 5  # seconds


class NotificationSettings(BaseSettingsGroup):
    @property
    def color(self):
        value = self.value("color", DEFAULT_COLOR)
        if isinstance(value, (tuple, list)):
            value = QColor.fromRgb(*map(int, value))
        assert isinstance(value, QColor), type(value)
        return value

    @color.setter
    def color(self, value):
        assert isinstance(value, QColor)
        self.set_value("color", value.toTuple()[:3])

    @property
    def duration(self):
        value = int(self.value("duration", DEFAULT_DURATION))
        return value

    @duration.setter
    def duration(self, value):
        assert isinstance(value, int)
        self.set_value("duration", value)

    @property
    def notification_expires(self):
        value = self.value("notification_expires", False)
        if isinstance(value, basestring):
            value = value.lower() == 'true'
        assert isinstance(value, bool)
        return value

    @notification_expires.setter
    def notification_expires(self, value):
        self.set_value("notification_expires", bool(value))


class NotificationDialog(QDialog):
    notifications_count_updated = Signal()

    def __init__(self, parent, title, body, remaining_notifications=None, this_notification_count=1, scale=1,
                 duration=None):
        super(NotificationDialog, self).__init__(parent)
        self.size = NOTIFICATION_SIZE * scale  # type: QSize
        layout = QBoxLayout(QBoxLayout.BottomToTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.notification_view = NotificationView(self, title=title, body=body)
        layout.addWidget(self.notification_view)
        layout.addSpacing(self.size.width() / 4)
        self.setLayout(layout)
        # Create a border-less transparent window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet('background:transparent;')
        # Set it's size
        self.setGeometry(QRect(QPoint(0, 0), QSize(self.size.width() * 1.2, self.size.height() * 1.6)))
        msg_geo = self.geometry()  # type: QRect
        # Move it to the bottom right corner
        # noinspection PyArgumentList
        msg_geo.moveBottomRight(QApplication.desktop().availableGeometry().bottomRight())
        self._closing = False
        self.move(msg_geo.topLeft())
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(0)
        self.notification_view.setGraphicsEffect(self.blur_effect)
        self.blur_animator = QPropertyAnimation(self.blur_effect, 'blurRadius', self)
        self.setWindowOpacity(0)
        self.opacity_animator = QPropertyAnimation(self, 'windowOpacity', self)
        self.setMouseTracking(True)
        self.animate_in()
        self.duration_reached_timer = self.startTimer(duration or (NotificationSettings().duration * 1000))
        self.remaining_notifications = remaining_notifications or 0
        self.this_notification_count = this_notification_count or 0
        self.notifications_count_updated.emit()

    def animate_in(self):
        self.blur_animator.setStartValue(30)
        self.blur_animator.setEndValue(0)
        self.blur_animator.setDuration(300)
        self.opacity_animator.setStartValue(self.windowOpacity())
        self.opacity_animator.setEndValue(1)
        self.opacity_animator.setDuration(400)
        self.opacity_animator.start()
        self.blur_animator.start()

    def animate_out(self):
        self._closing = True
        self.blur_animator.setStartValue(0)
        self.blur_animator.setEndValue(30)
        self.blur_animator.setDuration(350)
        self.opacity_animator.setStartValue(self.windowOpacity())
        self.opacity_animator.setEndValue(0)
        self.opacity_animator.setDuration(350)
        self.opacity_animator.start()
        self.blur_animator.start()

    def enterEvent(self, event):
        if self._closing:
            return
        if self.opacity_animator.state() == QPropertyAnimation.Running:
            self.opacity_animator.stop()
        self.opacity_animator.setStartValue(self.windowOpacity())
        self.opacity_animator.setEndValue(0.4)
        self.opacity_animator.setDuration(200)
        self.opacity_animator.start()
        super(NotificationDialog, self).enterEvent(event)

    def leaveEvent(self, event):
        if self.opacity_animator.state() == QPropertyAnimation.Running:
            self.opacity_animator.stop()
        self.opacity_animator.setStartValue(self.windowOpacity())
        self.opacity_animator.setEndValue(1)
        self.opacity_animator.setDuration(200)
        self.opacity_animator.start()
        super(NotificationDialog, self).leaveEvent(event)

    def timerEvent(self, event):
        if (event.timerId() == self.duration_reached_timer and
                not self.underMouse() and
                not NotificationSettings().notification_expires):
            self.close()
        super(NotificationDialog, self).timerEvent(event)

    def set_circle_text(self, text):
        self.notification_view.set_circle_text(text)

    def closeEvent(self, event):
        if self._closing:
            if self.duration_reached_timer:
                self.killTimer(self.duration_reached_timer)
            event.accept()
            super(NotificationDialog, self).closeEvent(event)
        else:
            self.animate_out()
            event.ignore()
            self.blur_animator.finished.connect(self.close)


class NotificationView(QGraphicsView):
    def __init__(self, parent, title, body, color=None):
        assert isinstance(parent, NotificationDialog)
        super(NotificationView, self).__init__(parent)
        self.color = color or NotificationSettings().color  # type: QColor
        self._scene = QGraphicsScene(self)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setScene(self._scene)
        self.setStyleSheet("QGraphicsView { border-style: none; }")
        self._inner_rect = QRect(QPoint(0, 0), parent.size)
        self.arrow_middle_point = QPointF(self._inner_rect.width() / 3.5, self._inner_rect.center().y())
        self.text_body_x = self.arrow_middle_point.x()
        self._bg_rect_item = self.make_background()
        arrow = self.create_arrow(self._inner_rect.topLeft(), self.arrow_middle_point, self._inner_rect.bottomLeft())
        self.circle = self.make_circle(arrow)
        self.circle_text = self.make_text('', 15, self.circle)
        self.make_close_circle_button()
        self.title_text_item = self.make_title_text(title[:25])
        self.body_text_item = self.make_body_text(body)
        self._notifications_count_text = None
        parent.notifications_count_updated.connect(self.notifications_count_updated)

    def set_circle_text(self, text):
        self.circle_text.setPlainText(text)
        text_rect = self.circle_text.boundingRect()
        text_rect.moveCenter(self.circle_text.parentItem().boundingRect().center())
        self.circle_text.setPos(text_rect.topLeft())

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
        return text_item

    def make_body_text(self, text):
        text_item = self.make_text(text, 12, self._bg_rect_item, QColor(Qt.darkGray).darker(), QFont.Normal)
        text_item.setPos(QPoint(self.text_body_x, self.title_text_item.pos().y() + 30))
        text_item.setTextWidth(self._inner_rect.width() - self.text_body_x)
        return text_item

    def notifications_count_updated(self):
        this, remaining = self.parent().this_notification_count, self.parent().remaining_notifications
        if self._notifications_count_text:
            self._scene.removeItem(self._notifications_count_text)
            del self._notifications_count_text
            self._notifications_count_text = None
        if remaining > 0 or this > 0:
            text = '{}/{}'.format(this + 1, remaining + this + 1)
            text_item = self.make_text(text, 12, self._bg_rect_item, QColor(Qt.darkGray).darker(), QFont.Normal)

            text_rect = text_item.boundingRect()
            text_rect.moveBottomRight(self._inner_rect.bottomRight() - QPoint(5, 5))
            text_item.setPos(text_rect.topLeft())
            self._notifications_count_text = text_item


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
