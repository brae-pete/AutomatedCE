# Standard library modules
import sys

# Installed modules
from PyQt5 import QtCore, QtGui, QtWidgets
import qtmodern.styles
import qtmodern.windows
import qdarkstyle
import numpy as np

CUSTOM = True


# Class for main gui
class MainWindow(QtWidgets.QTabWidget):
    def __init__(self):
        QtWidgets.QTabWidget.__init__(self)
        self.setTabBar(MainTabBar())
        # if CUSTOM:
        #     self.setStyleSheet(open("style.qss", "r").read())
        self.setGeometry(100, 100, 1700, 900)

        getting_started_tab = QtWidgets.QWidget()
        self.addTab(getting_started_tab, "Getting Started")
        self.getting_started_screen = GettingStartedScreen()
        temp_layout = QtWidgets.QVBoxLayout()
        temp_layout.addWidget(self.getting_started_screen)
        getting_started_tab.setLayout(temp_layout)

        insert_tab = QtWidgets.QWidget()
        self.addTab(insert_tab, "Insert")
        self.insert_screen = InsertScreen()
        temp_layout = QtWidgets.QVBoxLayout()
        temp_layout.addWidget(self.insert_screen)
        insert_tab.setLayout(temp_layout)

        method_tab = QtWidgets.QWidget()
        self.addTab(method_tab, "Method")
        self.method_screen = MethodScreen()
        temp_layout = QtWidgets.QVBoxLayout()
        temp_layout.addWidget(self.method_screen)
        method_tab.setLayout(temp_layout)

        sequence_tab = QtWidgets.QWidget()
        self.addTab(sequence_tab, "Sequence")
        self.sequence_screen = SequenceScreen()
        temp_layout = QtWidgets.QVBoxLayout()
        temp_layout.addWidget(self.sequence_screen)
        sequence_tab.setLayout(temp_layout)

        run_tab = QtWidgets.QWidget()
        self.addTab(run_tab, "Run")
        self.run_screen = RunScreen()
        temp_layout = QtWidgets.QVBoxLayout()
        temp_layout.addWidget(self.run_screen)
        run_tab.setLayout(temp_layout)

        data_tab = QtWidgets.QWidget()
        self.addTab(data_tab, "Data")
        self.data_screen = DataScreen()
        temp_layout = QtWidgets.QVBoxLayout()
        temp_layout.addWidget(self.data_screen)
        data_tab.setLayout(temp_layout)

        system_tab = QtWidgets.QWidget()
        self.addTab(system_tab, "System")
        self.system_screen = SystemScreen()
        temp_layout = QtWidgets.QVBoxLayout()
        temp_layout.addWidget(self.system_screen)
        system_tab.setLayout(temp_layout)


class MainTabBar(QtWidgets.QTabBar):
    def __init__(self):
        QtWidgets.QTabBar.__init__(self)
        if CUSTOM:
            self.setStyleSheet(open("style.qss", "r").read())


# Classes for main tabbed screens
class GettingStartedScreen(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtGui.QColor(250,250,250))
        self.setPalette(palette)

        self.main_options = self.init_load_new_options()
        self.main_options.setFixedSize(1050, 500)
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addStretch()
        main_layout.addWidget(self.main_options)
        main_layout.addStretch()
        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def init_load_new_options(self):
        central_widget = QtWidgets.QWidget()
        layouts = QtWidgets.QVBoxLayout()
        options = LoadNewMainWidget()
        options = wrap_widget(options)
        systems = SystemSelectionWidget()
        systems = wrap_widget(systems)
        layouts.addStretch()
        layouts.addWidget(options)
        layouts.addSpacing(20)
        layouts.addWidget(systems)
        layouts.addStretch()
        central_widget.setLayout(layouts)
        return central_widget


class InsertScreen(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        main_layout = QtWidgets.QVBoxLayout()

        main_layout.addStretch()
        image_view_layout = QtWidgets.QHBoxLayout()
        image_view_layout.addStretch()

        self.insert_tool_bar = QtWidgets.QToolBar()
        self.insert_joystick_tool_bar = QtWidgets.QToolBar()
        self.insert_main_window = QtWidgets.QMainWindow()
        self.insert_table = QtWidgets.QTableWidget()
        self.file_name = QtWidgets.QLineEdit()
        self.save_file = QtWidgets.QPushButton('Save')
        self.select_file = QtWidgets.QPushButton(
            QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\folder2.png"), "")

        self.init_toolbar()
        self.init_graphics_view()
        self.init_table()

        self.insert_main_window = wrap_widget(self.insert_main_window)
        image_view_layout.addWidget(self.insert_main_window)
        image_view_layout.addSpacing(20)
        self.insert_table_container = wrap_widget(self.insert_table)
        image_view_layout.addWidget(self.insert_table_container)

        image_view_layout.addStretch()
        main_layout.addLayout(image_view_layout)
        main_layout.addStretch()

        insert_screen_widget = QtWidgets.QWidget()
        insert_screen_widget.setLayout(main_layout)
        self.setCentralWidget(insert_screen_widget)

    def init_toolbar(self):
        self.insert_tool_bar.setWindowTitle('Draw')
        self.insert_tool_bar.setOrientation(QtCore.Qt.Vertical)
        self.insert_joystick_tool_bar.setOrientation(QtCore.Qt.Horizontal)

        self.draw_circle_action = QtWidgets.QAction(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\oval.png"), "")
        self.draw_circle_action.setToolTip('Drawing single circles')

        self.draw_rectangle_action = QtWidgets.QAction(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\rectangle.png"), "")
        self.draw_rectangle_action.setToolTip('Draw rectangle')

        self.draw_array_action = QtWidgets.QAction(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\menu.png"), "")
        self.draw_array_action.setToolTip('Drawing array of circles')

        self.clear_object_action = QtWidgets.QAction(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\eraser.png"), "")
        self.clear_object_action.setToolTip('Delete object')

        self.load_insert_action = QtWidgets.QAction(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\open-archive.png"), "")
        self.load_insert_action.setToolTip('Load an old insert')

        self.clear_area_action = QtWidgets.QAction(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\clear.png"), "")
        self.clear_area_action.setToolTip('Clear objects in an area')

        self.joystick_action = QtWidgets.QAction(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\game.png"), "")
        self.joystick_action.setToolTip('Start shape at current point')

        self.init_grid_action = QtWidgets.QAction(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\grid.png"), "")
        self.init_grid_action.setToolTip('Initialize stage dimensions')

        # self.select_action = QtWidgets.QAction(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\pointing.png"))
        # self.select_action.setToolTip('Select')

        self.circle_radius_input = QtWidgets.QLineEdit()
        self.circle_radius_input.setToolTip('Specify circle radius (Joystick)')
        self.circle_radius_input.setPlaceholderText('Radius (mm)')
        self.circle_radius_input.setFixedWidth(85)
        self.circle_radius_input.setEnabled(False)

        self.num_circles_horizontal_input = QtWidgets.QLineEdit()
        self.num_circles_horizontal_input.setToolTip('Specify number of wells across.')
        self.num_circles_horizontal_input.setPlaceholderText('# Across')
        self.num_circles_horizontal_input.setFixedWidth(85)
        self.num_circles_horizontal_input.setEnabled(False)

        self.num_circles_vertical_input = QtWidgets.QLineEdit()
        self.num_circles_vertical_input.setToolTip('Specify number of wells down.')
        self.num_circles_vertical_input.setPlaceholderText('# Down')
        self.num_circles_vertical_input.setFixedWidth(85)
        self.num_circles_vertical_input.setEnabled(False)

        self.insert_tool_bar.addAction(self.draw_circle_action)
        self.insert_tool_bar.addAction(self.draw_rectangle_action)
        self.insert_tool_bar.addAction(self.draw_array_action)
        self.insert_tool_bar.addAction(self.clear_object_action)
        self.insert_tool_bar.addAction(self.clear_area_action)
        self.insert_tool_bar.addSeparator()

        self.insert_joystick_tool_bar.addSeparator()
        self.insert_joystick_tool_bar.addSeparator()
        self.insert_joystick_tool_bar.addSeparator()
        self.insert_joystick_tool_bar.addSeparator()

        self.insert_joystick_tool_bar.addAction(self.load_insert_action)
        self.insert_joystick_tool_bar.addAction(self.init_grid_action)
        self.insert_joystick_tool_bar.addAction(self.joystick_action)
        self.insert_joystick_tool_bar.addWidget(self.circle_radius_input)
        self.insert_joystick_tool_bar.addWidget(self.num_circles_horizontal_input)
        self.insert_joystick_tool_bar.addWidget(self.num_circles_vertical_input)

        self.insert_tool_bar.setMovable(True)
        if CUSTOM:
            self.insert_tool_bar.setStyleSheet(open("style.qss", "r").read())

    def init_graphics_view(self):
        self.pixel_map = QtGui.QPixmap(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\black_"
                                       r"grid_thick_lines_mirror.png")
        self.image_frame = GraphicsScene()
        self.image_frame.addPixmap(self.pixel_map)
        self.image_view = QtWidgets.QGraphicsView(self.image_frame)
        self.insert_main_window.setCentralWidget(self.image_view)
        self.insert_main_window.addToolBar(QtCore.Qt.LeftToolBarArea, self.insert_tool_bar)
        self.insert_main_window.addToolBar(QtCore.Qt.TopToolBarArea, self.insert_joystick_tool_bar)

        temp_widget = QtWidgets.QWidget()
        temp_dock = QtWidgets.QDockWidget()
        temp_layout = QtWidgets.QHBoxLayout()
        temp_layout.addWidget(self.file_name)
        temp_layout.addWidget(self.select_file)
        temp_layout.addWidget(self.save_file)
        temp_widget.setLayout(temp_layout)
        temp_dock.setWidget(temp_widget)
        temp_dock.setTitleBarWidget(QtWidgets.QWidget())

        self.insert_main_window.addDockWidget(QtCore.Qt.BottomDockWidgetArea, temp_dock)

    def init_table(self):
        self.insert_table.setRowCount(0)
        self.insert_table.setColumnCount(2)
        self.insert_table.setHorizontalHeaderLabels(['Label', 'Location'])
        self.insert_table.verticalHeader().setVisible(False)


class MethodScreen(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        main_layout = QtWidgets.QVBoxLayout()

        main_layout.addStretch()
        image_view_layout = QtWidgets.QHBoxLayout()
        image_view_layout.addStretch()

        self.insert_main_window = QtWidgets.QMainWindow()
        self.insert_table = QtWidgets.QTableWidget()
        self.file_name = QtWidgets.QLineEdit()
        self.select_file = QtWidgets.QPushButton(
            QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\open-archive.png"), "")
        self.reload_button = QtWidgets.QPushButton(
            QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\refresh-button.png"), "")
        self.well_label = QtWidgets.QLineEdit()
        self.well_location = QtWidgets.QLineEdit()

        self.init_graphics_view()
        self.init_table()

        self.insert_main_window = wrap_widget(self.insert_main_window)
        image_view_layout.addWidget(self.insert_main_window)
        image_view_layout.addSpacing(20)
        self.insert_table_container = wrap_widget(self.insert_table)
        image_view_layout.addWidget(self.insert_table_container)

        image_view_layout.addStretch()
        main_layout.addLayout(image_view_layout)
        main_layout.addStretch()

        insert_screen_widget = QtWidgets.QWidget()
        insert_screen_widget.setLayout(main_layout)
        self.setCentralWidget(insert_screen_widget)

    def init_graphics_view(self):
        self.pixel_map = QtGui.QPixmap(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\black_"
                                       r"grid_thick_lines_mirror.png")
        self.image_frame = GraphicsScene()
        self.image_frame.addPixmap(self.pixel_map)
        self.image_view = QtWidgets.QGraphicsView(self.image_frame)
        self.insert_main_window.setCentralWidget(self.image_view)
        temp_widget = QtWidgets.QWidget()
        temp_dock = QtWidgets.QDockWidget()

        wid_layout = QtWidgets.QVBoxLayout()

        temp_layout = QtWidgets.QHBoxLayout()
        temp_layout.addWidget(self.file_name)
        temp_layout.addWidget(self.select_file)
        temp_layout.addWidget(self.reload_button)

        temp_layout2 = QtWidgets.QHBoxLayout()
        self.well_label.setReadOnly(True)
        self.well_location.setReadOnly(True)
        temp_layout2.addWidget(self.well_label)
        temp_layout2.addWidget(self.well_location)
        temp_layout2.addSpacing(250)

        wid_layout.addLayout(temp_layout2)
        wid_layout.addLayout(temp_layout)

        temp_widget.setLayout(wid_layout)
        temp_dock.setWidget(temp_widget)
        temp_dock.setTitleBarWidget(QtWidgets.QWidget())
        self.insert_main_window.addDockWidget(QtCore.Qt.BottomDockWidgetArea, temp_dock)

    def init_table(self):
        self.insert_table.setRowCount(0)
        self.insert_table.setColumnCount(8)
        # self.insert_table.column(8).setMinimumWidth(200)
        self.insert_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.insert_table.setHorizontalHeaderLabels(["", 'Time (min)', 'Event', 'Value', 'Duration',
                                                     'Inlet Vial', 'Outlet Vial', 'Summary'])
        self.insert_table.setColumnWidth(0, 30)
        self.insert_table.verticalHeader().setVisible(False)
        self.insert_table.setMinimumWidth(800)


class SequenceScreen(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)


class RunScreen(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)


class DataScreen(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)


class SystemScreen(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)


# Altered Widgets
class AlteredTabBar(QtWidgets.QTabBar):

    def tabSizeHint(self, index):
        s = QtWidgets.QTabBar.tabSizeHint(self, index)
        s.transpose()
        return s

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        opt = QtWidgets.QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QtCore.QRect(QtCore.QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt);
            painter.restore()


class AlteredTabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QTabWidget.__init__(self, *args, **kwargs)
        self.setTabBar(AlteredTabBar(self))
        if CUSTOM:
            self.setStyleSheet(open("style.qss", "r").read())
        self.setTabPosition(QtWidgets.QTabWidget.West)


class AlteredProxyStyle(QtWidgets.QProxyStyle):
    def drawControl(self, element, opt, painter, widget):
        if element == QtWidgets.QStyle.CE_TabBarTabLabel:
            r = QtCore.QRect(opt.rect)
            w = 0 if opt.icon.isNull() else opt.rect.width() + self.pixelMetric(QtWidgets.QStyle.PM_TabBarIconSize)
            r.setHeight(opt.fontMetrics.width(opt.text) + w)
            r.moveBottom(opt.rect.bottom())
            opt.rect = r
        QtWidgets.QProxyStyle.drawControl(self, element, opt, painter, widget)


class AnimatedPushButton(QtWidgets.QPushButton):
    def __init__(self, *args, **kwargs):
        QtWidgets.QPushButton.__init__(self, *args, **kwargs)
        self.setAutoFillBackground(True)

        self.anim_enter = QtCore.QPropertyAnimation(self, b"color")
        self.anim_enter.setDuration(100)
        self.anim_enter.setLoopCount(1)
        self.anim_enter.setStartValue(QtGui.QColor(0, 0, 0))
        self.anim_enter.setEndValue(QtGui.QColor(100, 100, 100))

        self.anim_leave = QtCore.QPropertyAnimation(self, b"color")
        self.anim_leave.setDuration(100)
        self.anim_leave.setLoopCount(1)
        self.anim_leave.setStartValue(QtGui.QColor(100, 100, 100))
        self.anim_leave.setEndValue(QtGui.QColor(0, 0, 0))

        self.setMouseTracking(True)

    def _set_color(self, color):
        palette = self.palette()
        palette.setColor(self.foregroundRole(), color)
        self.setPalette(palette)

    def enterEvent(self, event):
        self.anim_enter.start()

    def leaveEvent(self, event):
        self.anim_leave.start()

    color = QtCore.pyqtProperty(QtGui.QColor, fset=_set_color)


class GraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self, parent=None):
        super(GraphicsScene, self).__init__(parent)
        self.controller = None
        self.num_circle_x = 5
        self.num_circle_y = 5
        self.draw_shape = 'SELECT'
        self.shape_type = {'RECT': self.draw_rect,
                           'CIRCLE': self.draw_circle,
                           'LINE': self.draw_line,
                           'ARRAY': self.draw_clear_rect,
                           'REMOVE': self.remove_object,
                           'RAREA': self.draw_clear_rect,
                           'SELECT': self.select_item}
        self.joystick = False

        self._selecting = False
        self._clearing = False
        self._start = QtCore.QPointF()
        self._current_rect_item = None
        self._current_ellipse_item = None
        self._highlighted_location = None
        self._highlight_pen = QtGui.QPen(QtCore.Qt.cyan, 2, QtCore.Qt.SolidLine)

    def clear(self):
        for item in self.items():
            if type(item) != QtWidgets.QGraphicsPixmapItem:
                self.removeItem(item)

    def add_shape(self, shape, bbox):
        if shape == 'RECT':
            self._current_rect_item = QtWidgets.QGraphicsRectItem()
        elif shape == 'ELLIPSE':
            self._current_rect_item = QtWidgets.QGraphicsEllipseItem()
        else:
            return
        r = QtCore.QRectF(bbox[0], bbox[1], bbox[2], bbox[3])

        self._current_rect_item.setBrush(QtCore.Qt.red)
        self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
        self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.addItem(self._current_rect_item)
        self._current_rect_item.setRect(r)
        self._current_rect_item = None

    def select_item(self, event):
        location = [event.scenePos().x(), event.scenePos().y()]
        self.highlight_item(location)

    def get_bounding_rect(self, location):
        highlighted_item = self.itemAt(location[0], location[1], QtGui.QTransform())
        if highlighted_item and type(highlighted_item) != QtWidgets.QGraphicsPixmapItem:
            return highlighted_item.boundingRect().getRect()

    def get_shape(self, location):
        highlighted_item = self.itemAt(location[0], location[1], QtGui.QTransform())
        if highlighted_item and type(highlighted_item) != QtWidgets.QGraphicsPixmapItem:
            if type(highlighted_item) == QtWidgets.QGraphicsRectItem:
                return 'RECT'
            else:
                return 'ELLIPSE'

    def highlight_item(self, location):
        if not self._clearing:
            if self._highlighted_location:
                highlighted_item = self.itemAt(self._highlighted_location[0],
                                               self._highlighted_location[1],
                                               QtGui.QTransform())
                if highlighted_item and type(highlighted_item) != QtWidgets.QGraphicsPixmapItem:
                    r = highlighted_item.boundingRect()
                    if type(highlighted_item) == QtWidgets.QGraphicsRectItem:
                        self._current_rect_item = QtWidgets.QGraphicsRectItem()
                    elif type(highlighted_item) == QtWidgets.QGraphicsEllipseItem:
                        self._current_rect_item = QtWidgets.QGraphicsEllipseItem()

                    self.removeItem(highlighted_item)

                    self._current_rect_item.setBrush(QtCore.Qt.red)
                    self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
                    self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
                    self.addItem(self._current_rect_item)
                    self._current_rect_item.setRect(r)
                    self._current_rect_item = None

            self._highlighted_location = location

            highlighted_item = self.itemAt(self._highlighted_location[0],
                                           self._highlighted_location[1],
                                           QtGui.QTransform())

            if type(highlighted_item) != QtWidgets.QGraphicsPixmapItem:
                r = list(highlighted_item.boundingRect().getRect())
                r = QtCore.QRectF(r[0] + 1, r[1] + 1, r[2] - 2, r[3] - 2)
                if type(highlighted_item) == QtWidgets.QGraphicsRectItem:
                    self._current_rect_item = QtWidgets.QGraphicsRectItem()
                elif type(highlighted_item) == QtWidgets.QGraphicsEllipseItem:
                    self._current_rect_item = QtWidgets.QGraphicsEllipseItem()
                self.removeItem(highlighted_item)

                self._current_rect_item.setBrush(QtCore.Qt.cyan)
                self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
                self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
                self.addItem(self._current_rect_item)
                self._current_rect_item.setRect(r)
                self._current_rect_item = None

    def draw_rect(self, event):
        if not self.joystick:
            self._current_rect_item = QtWidgets.QGraphicsRectItem()
            self._current_rect_item.setBrush(QtCore.Qt.red)
            self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            self.addItem(self._current_rect_item)
            self._start = event.scenePos()
            r = QtCore.QRectF(self._start, self._start)
            self._current_rect_item.setRect(r)
        else:
            self._current_rect_item = QtWidgets.QGraphicsRectItem()
            self._current_rect_item.setBrush(QtCore.Qt.red)
            self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            self.addItem(self._current_rect_item)
            self._start = QtCore.QPointF(event[0], event[1])
            r = QtCore.QRectF(self._start, self._start)
            self._current_rect_item.setRect(r)

    def draw_circle(self, event):
        if not self.joystick:
            self._current_ellipse_item = QtWidgets.QGraphicsEllipseItem()
            self._current_ellipse_item.setBrush(QtCore.Qt.red)
            self._current_ellipse_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self._current_ellipse_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            self.addItem(self._current_ellipse_item)
            self._start = event.scenePos()
            r = QtCore.QRectF(self._start, self._start)
            self._current_ellipse_item.setRect(r)
        else:
            self._current_ellipse_item = QtWidgets.QGraphicsEllipseItem()
            self._current_ellipse_item.setBrush(QtCore.Qt.red)
            self._current_ellipse_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self._current_ellipse_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            self.addItem(self._current_ellipse_item)
            r = QtCore.QRectF(event[0], event[1], event[2]*2, event[2]*2)
            self._current_ellipse_item.setRect(r)
            # self._current_ellipse_item = None

    def draw_array(self, event):
        marked_area = list(self._current_rect_item.boundingRect().getRect())
        if not self.joystick:
            pass
            print('Cannot drag out an array yet.')
        else:
            radius = event[2]
            x = marked_area[0]
            y = marked_area[1]
            dx = marked_area[2] / event[3]
            dy = marked_area[3] / event[4]

            for _ in range(int(event[3])):
                for _ in range(int(event[4])):
                    p1 = QtCore.QPointF(x - radius, y - radius)
                    p2 = QtCore.QPointF(x + radius, y + radius)
                    r = QtCore.QRectF(p1, p2)
                    self._current_ellipse_item = QtWidgets.QGraphicsEllipseItem()
                    self._current_ellipse_item.setBrush(QtCore.Qt.red)
                    self._current_ellipse_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
                    self._current_ellipse_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
                    self.addItem(self._current_ellipse_item)
                    self._current_ellipse_item.setRect(r)
                    self._current_ellipse_item = None
                    self.controller.add_row([x, y])
                    y += dy
                y = marked_area[1]
                x += dx

    def draw_line(self, event):
        pass

    def remove_object(self, event):
        self._clearing = True
        if not self.joystick:
            item = self.itemAt(event.scenePos(), QtGui.QTransform())
            marked_area = list(item.boundingRect().getRect())
            self.controller.remove_item([marked_area[0]+.5*marked_area[2], marked_area[1]+.5*marked_area[3]])
            self.removeItem(self.itemAt(event.scenePos(), QtGui.QTransform()))
        self._clearing = False

    def draw_clear_rect(self, event):
        if not self.joystick:
            self._current_rect_item = QtWidgets.QGraphicsRectItem()
            self._current_rect_item.setBrush(QtCore.Qt.red)
            self._current_rect_item.setOpacity(0.2)
            self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self.addItem(self._current_rect_item)
            self._start = event.scenePos()
            r = QtCore.QRectF(self._start, self._start)
            self._current_rect_item.setRect(r)
        else:
            self._current_rect_item = QtWidgets.QGraphicsRectItem()
            self._current_rect_item.setBrush(QtCore.Qt.red)
            self._current_rect_item.setOpacity(0.2)
            self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self.addItem(self._current_rect_item)
            self._start = QtCore.QPointF(event[0], event[1])
            r = QtCore.QRectF(self._start, self._start)
            self._current_rect_item.setRect(r)

    def clear_area(self):
        self._clearing = True
        marked_area = self._current_rect_item.boundingRect()
        marked_items = self.items(marked_area)
        for item in marked_items:
            if type(item) is not QtWidgets.QGraphicsPixmapItem:
                r = item.boundingRect().getRect()
                self.controller.remove_item([r[0]+.5*r[2], r[1]+.5*r[3]])
                self.removeItem(item)
        self._clearing = False

    def mousePressEvent(self, event):
        if not self.joystick:
            item_type = type(self.itemAt(event.scenePos(), QtGui.QTransform()))

            if ((item_type is not QtWidgets.QGraphicsRectItem and item_type is not QtWidgets.QGraphicsEllipseItem
                and item_type is not QtWidgets.QGraphicsLineItem and self.draw_shape is not 'REMOVE')
                    or (self.draw_shape is 'REMOVE' and item_type is not QtWidgets.QGraphicsPixmapItem))\
                        or self.draw_shape == 'SELECT':
                try:
                    self.shape_type[self.draw_shape](event)
                except AttributeError:
                    pass

            super(GraphicsScene, self).mousePressEvent(event)
        else:
            try:
                self.shape_type[self.draw_shape](event)
            except AttributeError:
                pass

    def mouseMoveEvent(self, event):
        if not self.joystick:
            if self._current_rect_item is not None:
                r = QtCore.QRectF(self._start, event.scenePos()).normalized()
                self._current_rect_item.setRect(r)
            elif self._current_ellipse_item is not None:
                r = QtCore.QRectF(self._start, event.scenePos()).normalized()
                self._current_ellipse_item.setRect(r)
            super(GraphicsScene, self).mouseMoveEvent(event)
        else:
            if self._current_rect_item is not None:
                r = QtCore.QRectF(self._start, QtCore.QPointF(event[0], event[1])).normalized()
                self._current_rect_item.setRect(r)

    def mouseReleaseEvent(self, event):
        try:
            if self.draw_shape == 'RAREA':
                self.clear_area()
                self._current_rect_item = None
            elif self.draw_shape == 'ARRAY':
                self.clear_area()
                self.draw_array(event)
                self._current_rect_item = None
        except AttributeError:
            pass

        if self._current_ellipse_item:
            marked_area = list(self._current_ellipse_item.boundingRect().getRect())
            self.controller.add_row([marked_area[0]+.5*marked_area[2], marked_area[1] + .5*marked_area[3]])
        elif self._current_rect_item:
            marked_area = list(self._current_rect_item.boundingRect().getRect())
            self.controller.add_row([marked_area[0] + .5 * marked_area[2], marked_area[1] + .5 * marked_area[3]])

        self._current_rect_item = None
        self._current_ellipse_item = None

        if not self.joystick:
            super(GraphicsScene, self).mouseReleaseEvent(event)


class WidgetContainer(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        if CUSTOM:
            self.setStyleSheet(open("style.qss", "r").read())


def wrap_widget(widget):
    wrapper_widget = QtWidgets.QFrame()
    if CUSTOM:
        wrapper_widget.setStyleSheet(open("style.qss", "r").read())
    wrapper_widget.setObjectName('WRAPPER')
    v_l = QtWidgets.QVBoxLayout()
    h_l = QtWidgets.QHBoxLayout()
    v_l.addSpacing(20)
    h_l.addSpacing(6)
    h_l.addWidget(widget)
    h_l.addSpacing(20)
    v_l.addLayout(h_l)
    v_l.addSpacing(20)
    wrapper_widget.setLayout(v_l)
    return wrapper_widget


# Class for Loading/Creating options widget in Getting Started.
class LoadNewMainWidget(AlteredTabWidget):
    def __init__(self):
        AlteredTabWidget.__init__(self)
        if CUSTOM:
            self.setStyle(AlteredProxyStyle())

        tab1 = QtWidgets.QWidget()
        tab2 = QtWidgets.QWidget()

        self.addTab(tab1, QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\folder.png"), "   Load")
        self.addTab(tab2, QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\add-file.png"), "   New")

        v1 = QtWidgets.QHBoxLayout()
        v2 = QtWidgets.QHBoxLayout()

        layouts = QtWidgets.QVBoxLayout()
        pushButton1 = QtWidgets.QPushButton("                   Data")
        pushButton1.setObjectName('MAIN')
        if CUSTOM:
            pushButton1.setStyleSheet(open("style.qss", "r").read())
        pushButton1.setIcon(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\graph.png"))
        pushButton1.setIconSize(QtCore.QSize(48, 48))

        pushButton2 = QtWidgets.QPushButton("                   Method")
        pushButton2.setObjectName('MAIN')
        if CUSTOM:
            pushButton2.setStyleSheet(open("style.qss", "r").read())
        pushButton2.setIcon(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\meter.png"))
        pushButton2.setIconSize(QtCore.QSize(48, 48))

        pushButton3 = QtWidgets.QPushButton("                   Insert")
        pushButton3.setObjectName('MAIN')
        if CUSTOM:
            pushButton3.setStyleSheet(open("style.qss", "r").read())
        pushButton3.setIcon(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\plastic.png"))
        pushButton3.setIconSize(QtCore.QSize(48, 48))

        pushButton4 = QtWidgets.QPushButton("                   Sequence")
        pushButton4.setObjectName('MAIN')
        if CUSTOM:
            pushButton4.setStyleSheet(open("style.qss", "r").read())
        pushButton4.setIcon(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\tick.png"))
        pushButton4.setIconSize(QtCore.QSize(48, 48))

        v1.addSpacing(40)
        v1.addWidget(pushButton1)
        v1.addSpacing(40)
        v1.addWidget(pushButton2)
        v1.addSpacing(40)
        v2.addSpacing(40)
        v2.addWidget(pushButton3)
        v2.addSpacing(40)
        v2.addWidget(pushButton4)
        v2.addSpacing(40)

        layouts.addLayout(v1)
        layouts.addLayout(v2)

        tab1.setLayout(layouts)

        v3 = QtWidgets.QHBoxLayout()
        v4 = QtWidgets.QHBoxLayout()

        layouts = QtWidgets.QVBoxLayout()
        pushButton5 = QtWidgets.QPushButton("                   Data")
        pushButton5.setObjectName('MAIN')
        if CUSTOM:
            pushButton5.setStyleSheet(open("style.qss", "r").read())
        pushButton5.setIcon(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\graph.png"))
        pushButton5.setIconSize(QtCore.QSize(48, 48))

        pushButton6 = QtWidgets.QPushButton("                   Method")
        pushButton6.setObjectName('MAIN')
        if CUSTOM:
            pushButton6.setStyleSheet(open("style.qss", "r").read())
        pushButton6.setIcon(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\meter.png"))
        pushButton6.setIconSize(QtCore.QSize(48, 48))

        pushButton7 = QtWidgets.QPushButton("                   Insert")
        pushButton7.setObjectName('MAIN')
        if CUSTOM:
            pushButton7.setStyleSheet(open("style.qss", "r").read())
        pushButton7.setIcon(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\plastic.png"))
        pushButton7.setIconSize(QtCore.QSize(48, 48))

        pushButton8 = QtWidgets.QPushButton("                   Sequence")
        pushButton8.setObjectName('MAIN')
        if CUSTOM:
            pushButton8.setStyleSheet(open("style.qss", "r").read())
        pushButton8.setIcon(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\tick.png"))
        pushButton8.setIconSize(QtCore.QSize(48, 48))

        v3.addSpacing(40)
        v3.addWidget(pushButton5)
        v3.addSpacing(40)
        v3.addWidget(pushButton6)
        v3.addSpacing(40)
        v4.addSpacing(40)
        v4.addWidget(pushButton7)
        v4.addSpacing(40)
        v4.addWidget(pushButton8)
        v4.addSpacing(40)

        layouts.addLayout(v3)
        layouts.addLayout(v4)

        tab2.setLayout(layouts)

        self.setFixedSize(1000, 240)

        # pushButton1.released.connect(lambda: )


# Class for System Selection widget in Getting Started.
class SystemSelectionWidget(AlteredTabWidget):
    def __init__(self):
        AlteredTabWidget.__init__(self)
        if CUSTOM:
            self.setStyleSheet(open("style.qss", "r").read())

        tab1 = QtWidgets.QWidget()

        self.addTab(tab1, "   System")
        tab1.layout = QtWidgets.QVBoxLayout()

        barracuda_button = QtWidgets.QPushButton("       Barracuda")
        barracuda_button.setObjectName('MAIN')
        barracuda_button.setIcon(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\7079-200.png"))
        barracuda_button.setIconSize(QtCore.QSize(48, 48))
        finch_button = QtWidgets.QPushButton("       Finch")
        finch_button.setObjectName('MAIN')
        finch_button.setIcon(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\angry-birds.png"))
        finch_button.setIconSize(QtCore.QSize(48, 48))
        ostrich_button = QtWidgets.QPushButton("       Ostrich")
        ostrich_button.setObjectName('MAIN')
        ostrich_button.setIcon(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\BarracudaQt\ostrich.png"))
        ostrich_button.setIconSize(QtCore.QSize(48, 48))

        layouts = QtWidgets.QVBoxLayout()
        row_1 = QtWidgets.QHBoxLayout()
        row_1.addStretch()
        row_2 = QtWidgets.QHBoxLayout()
        row_2.addSpacing(40)
        row_2.addWidget(ostrich_button)
        row_2.addSpacing(20)
        row_2.addWidget(barracuda_button)
        row_2.addSpacing(20)
        row_2.addWidget(finch_button)
        row_2.addSpacing(40)
        layouts.addLayout(row_1)
        layouts.addLayout(row_2)

        tab1.layout.addLayout(layouts)

        tab1.setLayout(tab1.layout)
        self.setFixedSize(1000, 81)


# Classes for Method Popups
class RinseDialog(QtWidgets.QDialog):
    def __init__(self, pos_function=None):
        super(RinseDialog, self).__init__()
        self.form_data = {}
        self.setWindowTitle('Rinse')

        self.pressure_type_form = QtWidgets.QGroupBox('Pressure Type')
        self.init_pressure_type_form()

        self.values_form = QtWidgets.QGroupBox('Values')
        self.init_values_form()

        self.tray_positions_form = QtWidgets.QGroupBox('Tray Positions')
        self.init_tray_positions_form()

        self.pressure_direction_form = QtWidgets.QGroupBox('Pressure Direction')
        self.init_pressure_direction_form()

        self.at_time_form = QtWidgets.QGroupBox()
        self.init_at_time_form()

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        if pos_function:
            button_box.accepted.connect(lambda: pos_function('RINSE', self.form_data))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        forms_layout = QtWidgets.QVBoxLayout()
        top_forms = QtWidgets.QHBoxLayout()
        lower_forms = QtWidgets.QHBoxLayout()
        lower_right_forms = QtWidgets.QVBoxLayout()

        lower_right_forms.addWidget(self.pressure_direction_form)
        lower_right_forms.addWidget(self.at_time_form)
        lower_forms.addWidget(self.tray_positions_form)
        lower_forms.addLayout(lower_right_forms)
        top_forms.addWidget(self.pressure_type_form)
        top_forms.addWidget(self.values_form)
        forms_layout.addLayout(top_forms)
        forms_layout.addLayout(lower_forms)
        main_layout.addLayout(forms_layout)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)
        self.exec_()

    def init_pressure_type_form(self):
        layout = QtWidgets.QFormLayout()

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['PressureTypePressureRadio'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Pressure')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['PressureTypeVacuumRadio'] = wid.isChecked
        wid.setEnabled(False)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Vacuum')
        wid.setEnabled(False)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        self.pressure_type_form.setLayout(layout)
        # self.pressure_type_form.setFixedWidth(160)

    def init_values_form(self):
        layout = QtWidgets.QFormLayout()

        # PRESSURE
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Pressure:')
        row.addWidget(wid)

        wid = QtWidgets.QLineEdit()
        self.form_data['ValuesPressureEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)

        wid = QtWidgets.QLabel('psi')
        row.addWidget(wid)

        row.addStretch()
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        # DURATION
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Duration:')
        row.addWidget(wid)

        wid = QtWidgets.QLineEdit()
        self.form_data['ValuesDurationEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)

        wid = QtWidgets.QLabel('min')
        row.addWidget(wid)

        row.addStretch()
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        self.values_form.setLayout(layout)
        # self.values_form.setFixedWidth(180)

    def init_tray_positions_form(self):
        layout = QtWidgets.QFormLayout()

        # INLET ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Inlet:   ')
        row.addWidget(wid)

        wid = QtWidgets.QLineEdit()
        self.form_data['TrayPositionsInletEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)

        row.addStretch()
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        # OUTLET ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Outlet:')
        row.addWidget(wid)

        wid = QtWidgets.QLineEdit()
        self.form_data['TrayPositionsOutletEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)

        row.addStretch()
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        # INCREMENT ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Increment:')
        wid.setEnabled(True)
        row.addWidget(wid)

        row.addStretch()
        layout.addRow(row)

        # INLET/OUTLET CHECK ROW
        row = QtWidgets.QHBoxLayout()
        row.addSpacing(30)
        wid = QtWidgets.QCheckBox()
        self.form_data['TrayPositionsInletCheck'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Inlet')
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QCheckBox()
        self.form_data['TrayPositionsOutletCheck'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Outlet')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.addStretch()
        layout.addRow(row)

        # INCREMENT ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Increment Every ')
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLineEdit()
        self.form_data['TrayPositionsIncrementEdit'] = wid.text
        wid.setFixedWidth(25)
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Cycles')
        wid.setEnabled(True)
        row.addWidget(wid)
        layout.addRow(row)

        # TRAYS ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QPushButton('Trays ...')
        # self.form_data['TrayPositionsTraysPushbutton'] = wid
        wid.setFixedWidth(60)
        wid.setEnabled(True)
        row.addSpacing(30)
        row.addWidget(wid)
        layout.addRow(row)

        self.tray_positions_form.setLayout(layout)

    def init_pressure_direction_form(self):
        layout = QtWidgets.QFormLayout()

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['PressureDirectionForwardRadio'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Forward')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['PressureDirectionReverseRadio'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Reverse')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        self.pressure_direction_form.setLayout(layout)

    def init_at_time_form(self):
        layout = QtWidgets.QFormLayout()

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QCheckBox()
        self.form_data['AtTimeCheck'] = wid.isChecked
        row.addWidget(wid)
        row.addWidget(QtWidgets.QLabel('At Time:'))
        row.addStretch()
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLineEdit()
        self.form_data['AtTimeEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)
        row.addWidget(QtWidgets.QLabel('min'))
        row.addStretch()
        layout.addRow(row)

        self.at_time_form.setLayout(layout)


class SeparateDialog(QtWidgets.QDialog):
    def __init__(self, pos_function=None):
        QtWidgets.QDialog.__init__(self)
        self.form_data = {}
        self.setWindowTitle('Separate')

        self.separation_type_form = QtWidgets.QGroupBox('Separation Type')
        self.init_separation_type_form()

        self.polarity_form = QtWidgets.QGroupBox('Polarity')
        self.init_polarity_form()

        self.values_form = QtWidgets.QGroupBox('Values')
        self.init_values_form()

        self.tray_positions_form = QtWidgets.QGroupBox('Tray Positions')
        self.init_tray_positions_form()

        # self.pressure_direction_form = QtWidgets.QGroupBox('Pressure Direction')
        # self.init_pressure_direction_form()

        self.at_time_form = QtWidgets.QGroupBox()
        self.init_at_time_form()

        # self.external_adapter_form = QtWidgets.QGroupBox()
        # self.init_external_adapter_form()

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        if pos_function:
            button_box.accepted.connect(lambda: pos_function('SEPARATE', self.form_data))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        forms_layout = QtWidgets.QHBoxLayout()
        left_column = QtWidgets.QVBoxLayout()
        center_column = QtWidgets.QVBoxLayout()
        right_column = QtWidgets.QVBoxLayout()

        left_column.addWidget(self.separation_type_form)
        left_column.addWidget(self.polarity_form)
        left_column.addStretch()
        center_column.addWidget(self.values_form)
        center_column.addWidget(self.tray_positions_form)
        center_column.addStretch()
        # right_column.addWidget(self.pressure_direction_form)
        left_column.addWidget(self.at_time_form)
        # right_column.addWidget(self.external_adapter_form)
        right_column.addStretch()
        forms_layout.addLayout(left_column)
        forms_layout.addLayout(center_column)
        forms_layout.addLayout(right_column)
        main_layout.addLayout(forms_layout)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)
        self.exec_()

    def init_separation_type_form(self):
        layout = QtWidgets.QFormLayout()

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['SeparationTypeVoltageRadio'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Voltage')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['SeparationTypeCurrentRadio'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Current')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['SeparationTypePowerRadio'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Power')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['SeparationTypePressureRadio'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Pressure')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['SeparationTypeVacuumRadio'] = wid.isChecked
        wid.setEnabled(False)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Vacuum')
        wid.setEnabled(False)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        layout.addWidget(QtWidgets.QLabel('Options:'))

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QCheckBox()
        self.form_data['SeparationTypeWithPressureCheck'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('With Pressure')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QCheckBox()
        self.form_data['SeparationTypeWithVacuumCheck'] = wid.isChecked
        wid.setEnabled(False)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('With Vacuum')
        wid.setEnabled(False)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        self.separation_type_form.setLayout(layout)

    def init_polarity_form(self):
        layout = QtWidgets.QFormLayout()

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['PolarityNormalRadio'] = wid.isChecked
        row.addWidget(wid)

        row.addWidget(QtWidgets.QLabel('Normal'))
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['PolarityReverseRadio'] = wid.isChecked
        row.addWidget(wid)

        row.addWidget(QtWidgets.QLabel('Reverse'))
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        self.polarity_form.setLayout(layout)

    def init_values_form(self):
        layout = QtWidgets.QFormLayout()

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel('Voltage:'))
        row.addSpacing(15)
        wid = QtWidgets.QLineEdit()
        self.form_data['ValuesVoltageEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)
        row.addWidget(QtWidgets.QLabel('KV'))
        row.addStretch()
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel('Pressure:'))
        row.addSpacing(10)
        wid = QtWidgets.QLineEdit()
        self.form_data['ValuesPressureEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)
        row.addWidget(QtWidgets.QLabel('psi'))
        row.addStretch()
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel('Duration:'))
        row.addSpacing(11)
        wid = QtWidgets.QLineEdit()
        self.form_data['ValuesDurationEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)
        row.addWidget(QtWidgets.QLabel('min'))
        row.addStretch()
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel('Ramp Time:'))
        wid = QtWidgets.QLineEdit()
        self.form_data['ValuesRampTimeEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)
        row.addWidget(QtWidgets.QLabel('min'))
        row.addStretch()
        layout.addRow(row)

        self.values_form.setLayout(layout)

    def init_tray_positions_form(self):
        layout = QtWidgets.QFormLayout()

        # INLET ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Inlet:   ')
        row.addWidget(wid)

        wid = QtWidgets.QLineEdit()
        self.form_data['TrayPositionsInletEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)

        row.addStretch()
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        # OUTLET ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Outlet:')
        row.addWidget(wid)

        wid = QtWidgets.QLineEdit()
        self.form_data['TrayPositionsOutletEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)

        row.addStretch()
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        # INCREMENT ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Increment:')
        wid.setEnabled(True)
        row.addWidget(wid)

        row.addStretch()
        layout.addRow(row)

        # INLET/OUTLET CHECK ROW
        row = QtWidgets.QHBoxLayout()
        row.addSpacing(30)
        wid = QtWidgets.QCheckBox()
        self.form_data['TrayPositionsInletCheck'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Inlet')
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QCheckBox()
        self.form_data['TrayPositionsOutletCheck'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Outlet')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.addStretch()
        layout.addRow(row)

        # INCREMENT ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Increment Every ')
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLineEdit()
        self.form_data['TrayPositionsIncrementEdit'] = wid.text
        wid.setFixedWidth(25)
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Cycles')
        wid.setEnabled(True)
        row.addWidget(wid)
        layout.addRow(row)

        # TRAYS ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QPushButton('Trays ...')
        # self.form_data['TrayPositionsTraysPushbutton'] = wid
        wid.setFixedWidth(60)
        wid.setEnabled(True)
        row.addSpacing(30)
        row.addWidget(wid)
        layout.addRow(row)

        self.tray_positions_form.setLayout(layout)

    # def init_pressure_direction_form(self):
    #     layout = QtWidgets.QFormLayout()
    #
    #     row = QtWidgets.QHBoxLayout()
    #     row.addWidget(QtWidgets.QRadioButton())
    #     row.addWidget(QtWidgets.QLabel('Forward'))
    #     layout.addRow(row)
    #
    #     row = QtWidgets.QHBoxLayout()
    #     row.addWidget(QtWidgets.QRadioButton())
    #     row.addWidget(QtWidgets.QLabel('Reverse'))
    #     layout.addRow(row)
    #
    #     self.pressure_direction_form.setLayout(layout)
    #     self.pressure_direction_form.setEnabled(False)

    def init_at_time_form(self):
        layout = QtWidgets.QFormLayout()

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QCheckBox()
        self.form_data['AtTimeCheck'] = wid.isChecked
        row.addWidget(wid)
        row.addWidget(QtWidgets.QLabel('At Time:'))
        row.addStretch()
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLineEdit()
        self.form_data['AtTimeEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)
        row.addWidget(QtWidgets.QLabel('min'))
        row.addStretch()
        layout.addRow(row)

        self.at_time_form.setLayout(layout)

    # def init_external_adapter_form(self):
    #     layout = QtWidgets.QFormLayout()
    #
    #     row = QtWidgets.QHBoxLayout()
    #     row.addWidget(QtWidgets.QCheckBox())
    #     row.addWidget(QtWidgets.QLabel('External Adapter'))
    #     row.addStretch()
    #     layout.addRow(row)
    #
    #     self.external_adapter_form.setLayout(layout)


class InjectDialog(QtWidgets.QDialog):
    def __init__(self, pos_function=None):
        QtWidgets.QDialog.__init__(self)
        self.form_data = {}
        self.setWindowTitle('Inject')

        self.injection_type_form = QtWidgets.QGroupBox('Injection Type')
        self.init_injection_type_form()

        self.polarity_form = QtWidgets.QGroupBox('Polarity')
        self.init_polarity_form()

        self.pressure_direction_form = QtWidgets.QGroupBox('Pressure Direction')
        self.init_pressure_direction_form()

        self.sequence_table_form = QtWidgets.QGroupBox('Sequence Table')
        self.init_sequence_table_form()

        self.values_form = QtWidgets.QGroupBox('Values')
        self.init_values_form()

        self.tray_positions_form = QtWidgets.QGroupBox('Tray Positions')
        self.init_tray_positions_form()

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        if pos_function:
            button_box.accepted.connect(lambda: pos_function('INJECT', self.form_data))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        form_layout = QtWidgets.QHBoxLayout()
        left_column = QtWidgets.QVBoxLayout()
        right_column = QtWidgets.QVBoxLayout()

        left_column.addWidget(self.injection_type_form)
        left_column.addWidget(self.polarity_form)
        left_column.addWidget(self.pressure_direction_form)
        left_column.addWidget(self.sequence_table_form)
        right_column.addWidget(self.values_form)
        right_column.addWidget(self.tray_positions_form)
        form_layout.addLayout(left_column)
        form_layout.addLayout(right_column)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)
        self.exec_()

    def init_injection_type_form(self):
        layout = QtWidgets.QFormLayout()

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['InjectionTypeVoltageRadio'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Voltage')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['InjectionTypePressureRadio'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Pressure')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['InjectionTypeVacuumRadio'] = wid.isChecked
        wid.setEnabled(False)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Vacuum')
        wid.setEnabled(False)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        self.injection_type_form.setLayout(layout)

    def init_polarity_form(self):
        layout = QtWidgets.QFormLayout()

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['PolarityNormalRadio'] = wid.isChecked
        row.addWidget(wid)
        row.addWidget(QtWidgets.QLabel('Normal'))
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['PolarityReverseRadio'] = wid.isChecked
        row.addWidget(wid)
        row.addWidget(QtWidgets.QLabel('Reverse'))
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        self.polarity_form.setLayout(layout)

    def init_pressure_direction_form(self):
        layout = QtWidgets.QFormLayout()

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['PressureDirectionForwardRadio'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Forward')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QRadioButton()
        self.form_data['PressureDirectionReverseRadio'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Reverse')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        self.pressure_direction_form.setLayout(layout)

    def init_sequence_table_form(self):
        layout = QtWidgets.QFormLayout()

        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QCheckBox()
        self.form_data['SequenceTableAllowOverrideCheck'] = wid.isChecked
        row.addWidget(wid)
        row.addWidget(QtWidgets.QLabel('Allow Override'))
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        self.sequence_table_form.setLayout(layout)

    def init_values_form(self):
        layout = QtWidgets.QFormLayout()

        # PRESSURE
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Pressure:')
        row.addWidget(wid)

        wid = QtWidgets.QLineEdit()
        self.form_data['ValuesPressureEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)

        wid = QtWidgets.QLabel('psi')
        row.addWidget(wid)

        row.addStretch()
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        # DURATION
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Duration:')
        row.addWidget(wid)

        wid = QtWidgets.QLineEdit()
        self.form_data['ValuesDurationEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)

        wid = QtWidgets.QLabel('min')
        row.addWidget(wid)

        row.addStretch()
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        # CAPILLARY FILL
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QCheckBox()
        self.form_data['ValuesCapillaryFillCheck'] = wid.isChecked
        row.addWidget(wid)

        wid = QtWidgets.QLabel('For Capillary Fill')
        row.addWidget(wid)

        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        # SET LAYOUT TO WIDGET
        self.values_form.setLayout(layout)

    def init_tray_positions_form(self):
        layout = QtWidgets.QFormLayout()

        # INLET ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Inlet:   ')
        row.addWidget(wid)

        wid = QtWidgets.QLineEdit()
        self.form_data['TrayPositionsInletEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)

        row.addStretch()
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        # OUTLET ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Outlet:')
        row.addWidget(wid)

        wid = QtWidgets.QLineEdit()
        self.form_data['TrayPositionsOutletEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)

        row.addStretch()
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

        # INCREMENT ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Increment:')
        wid.setEnabled(True)
        row.addWidget(wid)

        row.addStretch()
        layout.addRow(row)

        # INLET/OUTLET CHECK ROW
        row = QtWidgets.QHBoxLayout()
        row.addSpacing(30)
        wid = QtWidgets.QCheckBox()
        self.form_data['TrayPositionsInletCheck'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Inlet')
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QCheckBox()
        self.form_data['TrayPositionsOutletCheck'] = wid.isChecked
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Outlet')
        wid.setEnabled(True)
        row.addWidget(wid)
        row.addStretch()
        layout.addRow(row)

        # INCREMENT ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Increment Every ')
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLineEdit()
        self.form_data['TrayPositionsIncrementEdit'] = wid.text
        wid.setFixedWidth(25)
        wid.setEnabled(True)
        row.addWidget(wid)
        wid = QtWidgets.QLabel('Cycles')
        wid.setEnabled(True)
        row.addWidget(wid)
        layout.addRow(row)

        # TRAYS ROW
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QPushButton('Trays ...')
        # self.form_data['TrayPositionsTraysPushbutton'] = wid
        wid.setFixedWidth(60)
        wid.setEnabled(True)
        row.addSpacing(30)
        row.addWidget(wid)
        layout.addRow(row)

        self.tray_positions_form.setLayout(layout)


# Classes for other popups
class ErrorMessageUI(QtWidgets.QDialog):
    def __init__(self, error_message=None, pos_function=None):
        super(ErrorMessageUI, self).__init__()
        self.setWindowTitle('Error')
        message = QtWidgets.QLabel(error_message)
        pos_button = QtWidgets.QPushButton('Okay')
        self.setMinimumWidth(300)
        self.setMinimumHeight(80)
        pos_button.setFixedWidth(80)

        if pos_function:
            pos_button.released.connect(lambda: pos_function())

        pos_button.released.connect(lambda: self.close())

        col = QtWidgets.QVBoxLayout()

        col.addWidget(message)
        col.addWidget(pos_button)
        col.setAlignment(message, QtCore.Qt.AlignCenter)
        col.setAlignment(pos_button, QtCore.Qt.AlignCenter)
        self.setLayout(col)

        self.exec_()

