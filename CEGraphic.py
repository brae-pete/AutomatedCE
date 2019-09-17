# Standard library modules
import os
import logging

# Installed modules
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import matplotlib.pyplot as plt


cwd = os.getcwd()
contents = os.listdir(cwd)

# Locate the directory of icons
if "icons" in contents:
    ICON_FOLDER = os.path.join(cwd, "icons")
elif "CEGraphic" in contents:
    contents = os.listdir(os.chdir(os.path.join(contents, "CEGraphic")))
    if "icons" in contents:
        ICON_FOLDER = os.path.join(os.getcwd(), "icons")
else:  # fixme prompt for program folder if it is not the cwd or within the cwd.
    ICON_FOLDER = os.getcwd()

CUSTOM = True


# Class for main gui
class MainWindow(QtWidgets.QTabWidget):
    def __init__(self, parent):
        QtWidgets.QTabWidget.__init__(self)
        self.parent = parent
        self.setWindowTitle('Barracuda CE')
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

    def closeEvent(self, *args, **kwargs):
        self.parent.close_program()


class MainTabBar(QtWidgets.QTabBar):
    def __init__(self):
        QtWidgets.QTabBar.__init__(self)
        if CUSTOM:
            with open("style.qss", "r") as qss:
                self.setStyleSheet(qss.read())


class GettingStartedScreen(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtGui.QColor(250,250,250))
        self.setPalette(palette)

        main_options = self.init_load_new_options()
        main_options.setFixedSize(1050, 500)
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addStretch()
        main_layout.addWidget(main_options)
        main_layout.addStretch()
        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def init_load_new_options(self):
        central_widget = QtWidgets.QWidget()
        layouts = QtWidgets.QVBoxLayout()
        self.options = LoadNewMainWidget()
        self.options = wrap_widget(self.options)
        systems = SystemSelectionWidget()
        systems = wrap_widget(systems)
        layouts.addStretch()
        layouts.addWidget(self.options)
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
            QtGui.QIcon(os.path.join(ICON_FOLDER, "folder2.png")), "")

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

        self.draw_circle_action = QtWidgets.QAction(QtGui.QIcon(os.path.join(ICON_FOLDER, "oval.png")), "")
        self.draw_circle_action.setToolTip('Drawing single circles')

        self.draw_rectangle_action = QtWidgets.QAction(QtGui.QIcon(os.path.join(ICON_FOLDER, "rectangle.png")), "")
        self.draw_rectangle_action.setToolTip('Draw rectangle')

        self.draw_array_action = QtWidgets.QAction(QtGui.QIcon(os.path.join(ICON_FOLDER, "menu.png")), "")
        self.draw_array_action.setToolTip('Drawing array of circles')

        self.clear_object_action = QtWidgets.QAction(QtGui.QIcon(os.path.join(ICON_FOLDER, "eraser.png")), "")
        self.clear_object_action.setToolTip('Delete object')

        self.load_insert_action = QtWidgets.QAction(QtGui.QIcon(os.path.join(ICON_FOLDER, "open-archive.png")), "")
        self.load_insert_action.setToolTip('Load an old insert')

        self.clear_area_action = QtWidgets.QAction(QtGui.QIcon(os.path.join(ICON_FOLDER, "clear.png")), "")
        self.clear_area_action.setToolTip('Clear objects in an area')

        self.joystick_action = QtWidgets.QAction(QtGui.QIcon(os.path.join(ICON_FOLDER, "game.png")), "")
        self.joystick_action.setToolTip('Start shape at current point')

        self.init_grid_action = QtWidgets.QAction(QtGui.QIcon(os.path.join(ICON_FOLDER, "grid.png")), "")
        self.init_grid_action.setToolTip('Initialize stage dimensions')

        # self.select_action = QtWidgets.QAction(QtGui.QIcon(r"C:\Users\kalec\Documents\Research_Allbritton\CEGraphic\pointing.png"))
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
            with open("style.qss", "r") as qss:
                self.insert_tool_bar.setStyleSheet(qss.read())

    def init_graphics_view(self):
        self.pixel_map = QtGui.QPixmap(os.path.join(ICON_FOLDER, "black_grid_thick_lines_mirror.png"))
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
            QtGui.QIcon(os.path.join(ICON_FOLDER, "open-archive.png")), "")
        self.reload_button = QtWidgets.QPushButton(
            QtGui.QIcon(os.path.join(ICON_FOLDER, "refresh-button.png")), "")
        self.well_label = QtWidgets.QLineEdit()
        self.well_location = QtWidgets.QLineEdit()
        self.file_name_save = QtWidgets.QLineEdit()
        self.save_file = QtWidgets.QPushButton('Save')
        self.select_file_save = QtWidgets.QPushButton(
            QtGui.QIcon(os.path.join(ICON_FOLDER, "folder2.png")), "")
        self.load_file_method = QtWidgets.QPushButton('Open')

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
        self.pixel_map = QtGui.QPixmap(os.path.join(ICON_FOLDER, "black_grid_thick_lines_mirror.png"))
        self.image_frame = GraphicsScene()
        self.image_frame.addPixmap(self.pixel_map)
        self.image_view = QtWidgets.QGraphicsView(self.image_frame)
        self.insert_main_window.setCentralWidget(self.image_view)
        temp_widget = QtWidgets.QWidget()
        temp_dock = QtWidgets.QDockWidget()

        wid_layout = QtWidgets.QVBoxLayout()

        temp_layout = QtWidgets.QHBoxLayout()
        temp_layout.addWidget(QtWidgets.QLabel('Insert'))
        temp_layout.addSpacing(7)
        temp_layout.addWidget(self.file_name)
        temp_layout.addWidget(self.select_file)
        temp_layout.addWidget(self.reload_button)

        temp_layout2 = QtWidgets.QHBoxLayout()
        self.well_label.setReadOnly(True)
        self.well_label.setPlaceholderText('Well Name (none selected)')
        self.well_location.setReadOnly(True)
        self.well_location.setPlaceholderText('Well Location (none selected)')
        temp_layout2.addWidget(self.well_label)
        temp_layout2.addWidget(self.well_location)
        temp_layout2.addSpacing(230)

        temp_layout3 = QtWidgets.QHBoxLayout()
        temp_layout3.addWidget(QtWidgets.QLabel('Method'))
        temp_layout3.addWidget(self.file_name_save)
        temp_layout3.addWidget(self.select_file_save)
        temp_layout3.addWidget(self.save_file)
        temp_layout3.addWidget(self.load_file_method)

        wid_layout.addLayout(temp_layout2)
        wid_layout.addLayout(temp_layout)
        wid_layout.addLayout(temp_layout3)

        temp_widget.setLayout(wid_layout)
        temp_dock.setWidget(temp_widget)
        temp_dock.setTitleBarWidget(QtWidgets.QWidget())
        self.insert_main_window.addDockWidget(QtCore.Qt.BottomDockWidgetArea, temp_dock)

    def init_table(self):
        self.insert_table.setRowCount(0)
        self.insert_table.setColumnCount(10)
        self.insert_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.insert_table.setHorizontalHeaderLabels(["", 'Time (min)', 'Event', 'Value', 'Duration',
                                                     'Inlet Vial', 'Outlet Vial', 'Inlet Travel', 'Outlet Travel',
                                                     'Summary'])
        self.insert_table.setColumnWidth(0, 30)
        self.insert_table.setColumnWidth(9, 200)
        self.insert_table.verticalHeader().setVisible(False)
        self.insert_table.setMinimumWidth(800)


class SequenceScreen(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        main_layout = QtWidgets.QHBoxLayout()
        self.method_table = QtWidgets.QTableWidget()
        self.init_table()
        self.method_container = wrap_widget(self.method_table)

        main_layout.addStretch()
        main_layout.addWidget(self.method_container)
        main_layout.addStretch()

        wid = QtWidgets.QWidget()
        wid.setLayout(main_layout)

        self.setCentralWidget(wid)

    def init_table(self):
        self.method_table.setRowCount(0)
        self.method_table.setColumnCount(7)
        self.method_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.method_table.setHorizontalHeaderLabels(["", 'Sample Inject Inlet', 'Sample Inject Duration',
                                                     'Sample', 'Method', 'Filename', 'Sample Amt.'])
        self.method_table.setColumnWidth(0, 30)
        self.method_table.setColumnWidth(1, 180)
        self.method_table.setColumnWidth(2, 180)
        self.method_table.setColumnWidth(3, 80)
        self.method_table.setColumnWidth(4, 400)
        self.method_table.setColumnWidth(5, 240)
        self.method_table.setColumnWidth(6, 80)

        self.method_table.verticalHeader().setVisible(True)
        self.method_table.setMinimumWidth(800)


class RunScreen(QtWidgets.QMainWindow):
    feed_updated = QtCore.pyqtSignal()
    xy_updated = QtCore.pyqtSignal()

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.init_run_control()
        self.init_hardware_control()
        self.init_live_display()

        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.hardware_control_panel)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.live_feed_panel)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.run_control_panel)

    def init_hardware_control(self):
        self.xy_stage_form = QtWidgets.QGroupBox('XY Stage')
        self.init_xy_stage_form()

        self.objective_form = QtWidgets.QGroupBox('Objective')
        self.init_objective_form()

        self.outlet_form = QtWidgets.QGroupBox('Outlet')
        self.init_outlet_form()

        self.z_stage_form = QtWidgets.QGroupBox('Z Stage')
        self.init_z_stage_form()

        self.pressure_form = QtWidgets.QGroupBox('Pressure')
        self.init_pressure_form()

        self.laser_form = QtWidgets.QGroupBox('Laser')
        self.init_laser_form()

        self.voltage_form = QtWidgets.QGroupBox('Voltage')
        self.init_voltage_form()

        self.stop_form = QtWidgets.QGroupBox()
        self.init_stop_form()

        self.temp_calibrate_layout = QtWidgets.QHBoxLayout()
        self.temp_calibrate_layout.addStretch()
        self.temp_calibrate_button = QtWidgets.QPushButton('Calibrate FIXME')
        self.temp_calibrate_layout.addWidget(self.temp_calibrate_button)
        self.temp_find_button = QtWidgets.QPushButton('FIND FIXME')
        self.temp_calibrate_layout.addWidget(self.temp_find_button)
        self.temp_pixel_conversion_button = QtWidgets.QPushButton('CONVERSION FIXME')
        self.temp_calibrate_layout.addWidget(self.temp_pixel_conversion_button)
        self.temp_laser_set = QtWidgets.QPushButton('LASER FIXME')
        self.temp_calibrate_layout.addWidget(self.temp_laser_set)
        self.temp_focus_button = QtWidgets.QPushButton('FOCUS FIXME')
        self.temp_calibrate_layout.addWidget(self.temp_focus_button)
        self.temp_pic_button = QtWidgets.QPushButton('PIC FIXME')
        self.temp_calibrate_layout.addWidget(self.temp_pic_button)
        self.temp_calibrate_layout.addStretch()

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addStretch()
        main_layout.addLayout(self.temp_calibrate_layout)
        main_layout.addWidget(self.xy_stage_form)
        main_layout.addSpacing(20)
        motor_layout = QtWidgets.QHBoxLayout()
        motor_layout.addWidget(self.objective_form)
        motor_layout.addWidget(self.outlet_form)
        motor_layout.addWidget(self.z_stage_form)
        main_layout.addLayout(motor_layout)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.pressure_form)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.laser_form)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.voltage_form)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.stop_form)
        main_layout.addStretch()

        self.hardware_control_panel = QtWidgets.QDockWidget()
        self.hardware_control_panel.setTitleBarWidget(QtWidgets.QWidget())
        temper_wid = QtWidgets.QWidget()
        temper_wid.setLayout(main_layout)
        temper_wid = wrap_widget(temper_wid)
        temper_wid.setFixedWidth(380)
        self.hardware_control_panel.setWidget(temper_wid)

    def init_xy_stage_form(self):
        self.xy_up = QtWidgets.QToolButton()
        self.xy_up.setArrowType(QtCore.Qt.UpArrow)
        self.xy_down = QtWidgets.QToolButton()
        self.xy_down.setArrowType(QtCore.Qt.DownArrow)
        self.xy_left = QtWidgets.QToolButton()
        self.xy_left.setArrowType(QtCore.Qt.LeftArrow)
        self.xy_right = QtWidgets.QToolButton()
        self.xy_right.setArrowType(QtCore.Qt.RightArrow)
        self.xy_x_value = ValueDisplay()
        self.xy_y_value = ValueDisplay()
        self.xy_step_size = QtWidgets.QDoubleSpinBox()
        self.xy_origin = QtWidgets.QPushButton('Home')
        self.xy_set_origin = QtWidgets.QPushButton('Set Home')
        self.xy_stop = QtWidgets.QPushButton('Stop')

        self.xy_step_size.setSuffix(" µm")
        self.xy_step_size.setValue(50)
        self.xy_step_size.setMaximum(100000)

        form_layout = QtWidgets.QFormLayout()
        row_outer = QtWidgets.QHBoxLayout()
        column_arrows = QtWidgets.QVBoxLayout()
        top_arrow = QtWidgets.QHBoxLayout()
        top_arrow.addStretch()
        top_arrow.addWidget(self.xy_up)
        top_arrow.addStretch()
        column_arrows.addLayout(top_arrow)
        row_arrow = QtWidgets.QHBoxLayout()
        row_arrow.addWidget(self.xy_left)
        row_arrow.addSpacing(30)
        row_arrow.addWidget(self.xy_right)
        column_arrows.addLayout(row_arrow)
        bottom_arrow = QtWidgets.QHBoxLayout()
        bottom_arrow.addStretch()
        bottom_arrow.addWidget(self.xy_down)
        bottom_arrow.addStretch()
        column_arrows.addLayout(bottom_arrow)
        step_row = QtWidgets.QHBoxLayout()
        step_row.addStretch()
        step_row.addWidget(self.xy_step_size)
        step_row.addStretch()
        column_arrows.addLayout(step_row)
        row_outer.addLayout(column_arrows)
        column_control = QtWidgets.QVBoxLayout()
        row_one = QtWidgets.QHBoxLayout()
        row_one.addWidget(self.xy_x_value)
        row_one.addWidget(self.xy_y_value)
        column_control.addLayout(row_one)
        row_two = QtWidgets.QHBoxLayout()
        row_two.addWidget(self.xy_origin)
        row_two.addWidget(self.xy_set_origin)
        row_two.addWidget(self.xy_stop)
        column_control.addLayout(row_two)
        row_outer.addLayout(column_control)
        form_layout.addRow(row_outer)

        self.xy_stage_form.setLayout(form_layout)

    def init_objective_form(self):
        self.objective_up = QtWidgets.QToolButton()
        self.objective_up.setArrowType(QtCore.Qt.UpArrow)
        self.objective_down = QtWidgets.QToolButton()
        self.objective_down.setArrowType(QtCore.Qt.DownArrow)
        self.objective_value = ValueDisplay()
        self.objective_stop = QtWidgets.QPushButton('Stop')
        self.objective_step_size = QtWidgets.QDoubleSpinBox()
        self.objective_set_home = QtWidgets.QPushButton('Set Home')
        self.objective_home = QtWidgets.QPushButton('Home')

        self.objective_step_size.setSuffix(" µm")
        self.objective_step_size.setValue(5)
        self.objective_step_size.setMaximum(1000)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addWidget(self.objective_value)
        col_one = QtWidgets.QVBoxLayout()
        col_one.addSpacing(10)
        col_one.addWidget(self.objective_up)
        col_one.addWidget(self.objective_down)
        col_one.addSpacing(10)
        row = QtWidgets.QHBoxLayout()
        row.addStretch()
        row.addLayout(col_one)
        row.addStretch()
        form_layout.addRow(row)
        form_layout.addWidget(self.objective_step_size)
        form_layout.addWidget(self.objective_set_home)
        form_layout.addWidget(self.objective_home)
        form_layout.addWidget(self.objective_stop)

        self.objective_form.setLayout(form_layout)

    def init_outlet_form(self):
        self.outlet_up = QtWidgets.QToolButton()
        self.outlet_up.setArrowType(QtCore.Qt.UpArrow)
        self.outlet_down = QtWidgets.QToolButton()
        self.outlet_down.setArrowType(QtCore.Qt.DownArrow)
        self.outlet_value = ValueDisplay()
        self.outlet_stop = QtWidgets.QPushButton('Stop')
        self.outlet_step_size = QtWidgets.QDoubleSpinBox()
        self.outlet_set_home = QtWidgets.QPushButton('Set Home')
        self.outlet_home = QtWidgets.QPushButton('Home')

        self.outlet_step_size.setSuffix(" mm")
        self.outlet_step_size.setValue(1)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addWidget(self.outlet_value)
        col_one = QtWidgets.QVBoxLayout()
        col_one.addSpacing(10)
        col_one.addWidget(self.outlet_up)
        col_one.addWidget(self.outlet_down)
        col_one.addSpacing(10)
        row = QtWidgets.QHBoxLayout()
        row.addStretch()
        row.addLayout(col_one)
        row.addStretch()
        form_layout.addRow(row)
        form_layout.addWidget(self.outlet_step_size)
        form_layout.addWidget(self.outlet_set_home)
        form_layout.addWidget(self.outlet_home)
        form_layout.addWidget(self.outlet_stop)

        self.outlet_form.setLayout(form_layout)

    def init_z_stage_form(self):
        self.z_up = QtWidgets.QToolButton()
        self.z_up.setArrowType(QtCore.Qt.UpArrow)
        self.z_down = QtWidgets.QToolButton()
        self.z_down.setArrowType(QtCore.Qt.DownArrow)
        self.z_value = ValueDisplay()
        self.z_stop = QtWidgets.QPushButton('Stop')
        self.z_step_size = QtWidgets.QDoubleSpinBox()
        self.z_set_home = QtWidgets.QPushButton('Set Home')
        self.z_home = QtWidgets.QPushButton('Home')

        self.z_step_size.setSuffix(" mm")
        self.z_step_size.setValue(3)

        form_layout = QtWidgets.QFormLayout()
        col_one = QtWidgets.QVBoxLayout()
        form_layout.addWidget(self.z_value)
        col_one.addSpacing(10)
        col_one.addWidget(self.z_up)
        col_one.addWidget(self.z_down)
        col_one.addSpacing(10)
        row = QtWidgets.QHBoxLayout()
        row.addStretch()
        row.addLayout(col_one)
        row.addStretch()
        form_layout.addRow(row)
        form_layout.addWidget(self.z_step_size)
        form_layout.addWidget(self.z_set_home)
        form_layout.addWidget(self.z_home)
        form_layout.addWidget(self.z_stop)

        self.z_stage_form.setLayout(form_layout)

    def init_pressure_form(self):
        self.pressure_off = QtWidgets.QPushButton('Stop')
        self.pressure_rinse_state = SwitchButton(w1='On', w2='Off')
        self.pressure_valve_state = SwitchButton(w1='Open', w2='Closed', width=80)


        form_layout = QtWidgets.QFormLayout()
        row_one = QtWidgets.QHBoxLayout()
        row_one.addWidget(QtWidgets.QLabel('Rinse'))
        row_one.addWidget(self.pressure_rinse_state)
        row_one.addStretch()

        row_one.addWidget(QtWidgets.QLabel('Valve'))
        row_one.addWidget(self.pressure_valve_state)
        row_one.addWidget(self.pressure_off)
        form_layout.addRow(row_one)

        self.pressure_form.setLayout(form_layout)

    def init_laser_form(self):
        self.laser_pfn = ValueDisplay()
        self.laser_attenuation = ValueDisplay()
        self.laser_burst_count = ValueDisplay()
        self.laser_fire = QtWidgets.QPushButton('Fire')
        self.laser_stop = QtWidgets.QPushButton('Stop Firing')
        self.laser_timer = QtWidgets.QTimeEdit()
        self.laser_standby = QtWidgets.QPushButton('Standby')
        self.laser_on_check = QtWidgets.QCheckBox()
        self.laser_fire_check = QtWidgets.QCheckBox()
        self.laser_timer = QtWidgets.QLabel()
        self.laser_off = QtWidgets.QPushButton('Off')
        self.laser_check = QtWidgets.QPushButton('Check Status')

        self.laser_pfn.setFixedWidth(40)
        self.laser_attenuation.setFixedWidth(40)
        self.laser_burst_count.setFixedWidth(40)

        self.laser_on_check.stateChanged.connect(lambda: self.enable_button(self.laser_standby, self.laser_on_check))
        self.laser_fire_check.stateChanged.connect(lambda: self.enable_button(self.laser_fire, self.laser_fire_check))

        self.laser_fire.setEnabled(False)
        self.laser_standby.setEnabled(False)
        self.laser_fire_check.setEnabled(False)
        # self.laser_timer.setReadOnly(True)
        self.laser_timer.setText('0s')


        form_layout = QtWidgets.QFormLayout()
        col_one = QtWidgets.QVBoxLayout()
        row_one = QtWidgets.QHBoxLayout()
        row_one.addSpacing(15)
        row_one.addWidget(self.laser_on_check)
        row_one.addWidget(self.laser_standby)
        row_one.addStretch()
        row_one.addWidget(self.laser_fire_check)
        row_one.addWidget(self.laser_fire)
        row_one.addStretch()
        row_one.addWidget(self.laser_timer)
        col_one.addLayout(row_one)
        row_two = QtWidgets.QHBoxLayout()
        row_two.addStretch()
        row_two.addWidget(QtWidgets.QLabel('PFN'))
        row_two.addWidget(self.laser_pfn)
        row_two.addSpacing(5)
        row_two.addWidget(QtWidgets.QLabel('Attenuation'))
        row_two.addWidget(self.laser_attenuation)
        row_two.addSpacing(5)
        row_two.addWidget(QtWidgets.QLabel('Burst'))
        row_two.addWidget(self.laser_burst_count)
        row_two.addStretch()
        col_one.addLayout(row_two)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.laser_stop)
        row.addWidget(self.laser_off)
        row.addWidget(self.laser_check)
        col_one.addLayout(row)
        form_layout.addRow(col_one)

        self.laser_form.setLayout(form_layout)

    def init_voltage_form(self):
        self.voltage_value = QtWidgets.QDoubleSpinBox()
        self.voltage_off = QtWidgets.QPushButton('Stop')
        # self.voltage_on = QtWidgets.QPushButton('On')
        self.voltage_on_check = QtWidgets.QCheckBox()

        self.voltage_on_check.stateChanged.connect(lambda: self.enable_button(self.voltage_value, self.voltage_on_check))

        self.voltage_value.setEnabled(False)
        self.voltage_value.setSuffix(" kV")
        self.voltage_value.setValue(0.00)
        self.voltage_value.setSingleStep(0.1)
        self.voltage_value.setMaximum(25)

        form_layout = QtWidgets.QFormLayout()
        row_one = QtWidgets.QHBoxLayout()
        row_one.addWidget(self.voltage_on_check)
        # row_one.addWidget(self.voltage_on)
        # row_one.addStretch()
        row_one.addWidget(self.voltage_value)
        row_one.addSpacing(10)
        row_one.addWidget(self.voltage_off)
        row_one.addStretch()
        form_layout.addRow(row_one)

        self.voltage_form.setLayout(form_layout)

    def init_stop_form(self):
        self.all_stop = QtWidgets.QPushButton('STOP')

        self.all_stop.setFixedHeight(50)
        self.all_stop.setFixedWidth(200)

        form_layout = QtWidgets.QFormLayout()
        col = QtWidgets.QVBoxLayout()
        row = QtWidgets.QHBoxLayout()
        row.addStretch()
        row.addWidget(self.all_stop)
        row.addStretch()
        col.addLayout(row)
        form_layout.addRow(col)

        self.stop_form.setLayout(form_layout)

    def init_run_control(self):
        self.start_sequence = QtWidgets.QPushButton('Start')
        self.pause_sequence = QtWidgets.QPushButton('Pause')
        self.stop_sequence = QtWidgets.QPushButton('Stop')
        self.sequence_timer = QtWidgets.QLineEdit()
        self.sequence_display = QtWidgets.QTableWidget()
        self.repetition_input = QtWidgets.QSpinBox()
        self.output_window = QtWidgets.QPlainTextEdit()
        self.clear_output = QtWidgets.QPushButton('Clear')
        self.save_output = QtWidgets.QPushButton('Save')

        #Injection Steps
        self.inject_label = QtWidgets.QLabel('Injection Control:')
        self.inject_cell_box = QtWidgets.QCheckBox('Cell Z Stack')
        self.inject_cap_box = QtWidgets.QCheckBox('Cap. Z Stack')
        self.inject_capture_button = QtWidgets.QPushButton('Capture')
        self.inject_cell_box.checkState()

        self.sequence_display.setColumnCount(3)
        self.sequence_display.setColumnWidth(0, 30)
        self.sequence_display.setColumnWidth(1, 390)
        self.sequence_display.setColumnWidth(2, 160)
        self.sequence_display.setHorizontalHeaderLabels(['', 'Method', 'Summary'])
        self.sequence_display.setFixedWidth(600)
        self.output_window.appendPlainText('::System Updates::')
        self.repetition_input.setSuffix(' Repetitions')

        main_layout = QtWidgets.QHBoxLayout()
        col = QtWidgets.QVBoxLayout()
        col.addWidget(self.sequence_display)
        row = QtWidgets.QHBoxLayout()
        # row.addWidget(self.add_method)
        # row.addWidget(self.remove_method)
        # row.addSpacing(100)
        row.addWidget(self.start_sequence)
        row.addWidget(self.pause_sequence)
        row.addWidget(self.stop_sequence)
        row.addSpacing(10)
        row.addWidget(self.repetition_input)
        row.addStretch()
        col.addLayout(row)
        row_2 = QtWidgets.QHBoxLayout()
        row_2.addWidget(self.inject_label)
        row_2.addWidget(self.inject_cell_box)
        row_2.addWidget(self.inject_cap_box)
        row_2.addWidget(self.inject_capture_button)
        row_2.addStretch()
        col.addLayout(row_2)
        main_layout.addLayout(col)

        col = QtWidgets.QVBoxLayout()
        # col.addWidget(self.output_window)
        # row = QtWidgets.QHBoxLayout()
        # row.addWidget(self.clear_output)
        # row.addWidget(self.save_output)
        # row.addStretch()
        # col.addLayout(row)
        col.addWidget(self.output_window)
        main_layout.addLayout(col)

        self.run_control_panel = QtWidgets.QDockWidget()
        self.run_control_panel.setTitleBarWidget(QtWidgets.QWidget())
        temper_wid = QtWidgets.QWidget()
        temper_wid.setLayout(main_layout)
        temper_wid = wrap_widget(temper_wid)
        temper_wid.setFixedHeight(250)
        self.run_control_panel.setWidget(temper_wid)

    def init_live_display(self):
        self.live_feed_panel = QtWidgets.QDockWidget()
        self.live_feed_panel.setTitleBarWidget(QtWidgets.QWidget())
        temper_wid = QtWidgets.QWidget()
        temp_layout = QtWidgets.QHBoxLayout()
        # temp_layout.addStretch()
        feed_layout = QtWidgets.QVBoxLayout()
        feed_layout.addStretch()
        feed_layout.addWidget(self.init_insert_view())
        feed_layout.addStretch()
        temp_layout.addLayout(feed_layout)
        feed_layout = QtWidgets.QVBoxLayout()
        feed_layout.addStretch()
        feed_layout.addWidget(self.init_plot_view())
        feed_layout.addStretch()
        temp_layout.addLayout(feed_layout)
        # temp_layout.addStretch()
        temper_wid.setLayout(temp_layout)
        temper_wid = wrap_widget(temper_wid)
        self.live_feed_panel.setWidget(temper_wid)

    def init_insert_view(self):
        self.live_option = SwitchButton(w1='Live', w2='Insert', width=80)
        self.focus_feed = QtWidgets.QPushButton('Temp Focus Button')
        self.live_feed_scene = GraphicsScene()
        self.live_feed_scene.setSceneRect(0, 0, 512, 384)
        self.live_feed_view = QtWidgets.QGraphicsView()
        self.live_feed_pixmap = QtWidgets.QGraphicsPixmapItem()
        live_feed_window = QtWidgets.QMainWindow()

        # self.live_feed_view.setFixedWidth(584)
        # self.live_feed_view.setFixedHeight(312)

        live_feed_control = QtWidgets.QDockWidget()
        control_widget = QtWidgets.QWidget()
        control_layout = QtWidgets.QHBoxLayout()
        control_layout.addWidget(self.live_option)
        control_layout.addWidget(self.focus_feed)
        control_layout.addStretch()
        control_widget.setLayout(control_layout)
        live_feed_control.setWidget(control_widget)

        self.live_feed_pixmap = QtGui.QPixmap(os.path.join(ICON_FOLDER, "black_grid_thick_lines_mirror.png"))
        self.feed_pointer = self.live_feed_scene.addPixmap(self.live_feed_pixmap)
        self.live_feed_view.setScene(self.live_feed_scene)
        live_feed_window.setCentralWidget(self.live_feed_view)
        live_feed_window.addDockWidget(QtCore.Qt.TopDockWidgetArea, live_feed_control)
        live_feed_control.setTitleBarWidget(QtWidgets.QWidget())
        # live_feed_window = wrap_widget(live_feed_window)
        self.live_feed_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.live_feed_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        return live_feed_window

    def init_plot_view(self):
        self.save_plot = QtWidgets.QPushButton('Save')
        self.reset_plot = QtWidgets.QPushButton('Reset')
        self.view_plot = QtWidgets.QPushButton('Live Plot')
        self.view_plot.setCheckable(True)

        self.plot_panel = PlotPanel()
        live_plot_window = QtWidgets.QMainWindow()

        live_plot_control = QtWidgets.QDockWidget()
        control_widget = QtWidgets.QWidget()
        control_layout = QtWidgets.QHBoxLayout()
        control_layout.addWidget(self.save_plot)
        control_layout.addWidget(self.reset_plot)
        control_layout.addWidget(self.view_plot)
        control_layout.addStretch()
        control_widget.setLayout(control_layout)
        live_plot_control.setWidget(control_widget)

        self.save_plot.setFixedWidth(60)
        live_plot_window.setCentralWidget(self.plot_panel)
        live_plot_window.addDockWidget(QtCore.Qt.TopDockWidgetArea, live_plot_control)  # fixme when you want to add buttons
        live_plot_control.setTitleBarWidget(QtWidgets.QWidget())
        # live_plot_window = wrap_widget(live_plot_window)

        return live_plot_window

    def enable_xy_stage_form(self, enabled):
        self.xy_up.setEnabled(enabled)
        self.xy_down.setEnabled(enabled)
        self.xy_left.setEnabled(enabled)
        self.xy_right.setEnabled(enabled)
        self.xy_x_value.setEnabled(enabled)
        self.xy_y_value.setEnabled(enabled)
        self.xy_step_size.setEnabled(enabled)
        self.xy_origin.setEnabled(enabled)
        self.xy_set_origin.setEnabled(enabled)
        self.xy_stop.setEnabled(enabled)

    def enable_objective_form(self, enabled):
        self.objective_up.setEnabled(enabled)
        self.objective_down.setEnabled(enabled)
        self.objective_value.setEnabled(enabled)
        self.objective_stop.setEnabled(enabled)
        self.objective_step_size.setEnabled(enabled)

    def enable_outlet_form(self, enabled):
        self.outlet_up.setEnabled(enabled)
        self.outlet_down.setEnabled(enabled)
        self.outlet_value.setEnabled(enabled)
        self.outlet_stop.setEnabled(enabled)
        self.outlet_step_size.setEnabled(enabled)

    def enable_z_stage_form(self, enabled):
        self.z_up.setEnabled(enabled)
        self.z_down.setEnabled(enabled)
        self.z_value.setEnabled(enabled)
        self.z_stop.setEnabled(enabled)
        self.z_step_size.setEnabled(enabled)

    def enable_pressure_form(self, enabled):
        self.pressure_off.setEnabled(enabled)
        self.pressure_rinse_state.setEnabled(enabled)
        self.pressure_valve_state.setEnabled(enabled)

    def enable_laser_form(self, enabled):
        self.laser_pfn.setEnabled(enabled)
        self.laser_attenuation.setEnabled(enabled)
        self.laser_burst_count.setEnabled(enabled)
        self.laser_fire.setEnabled(enabled)
        self.laser_off.setEnabled(enabled)
        self.laser_timer.setEnabled(enabled)
        self.laser_standby.setEnabled(enabled)
        self.laser_on_check.setEnabled(enabled)
        self.laser_fire_check.setEnabled(enabled)
        self.laser_off.setEnabled(enabled)
        self.laser_check.setEnabled(enabled)

    def enable_voltage_form(self, enabled):
        self.voltage_value.setEnabled(enabled)
        self.voltage_off.setEnabled(enabled)
        # self.voltage_on.setEnabled(enabled)
        self.voltage_on_check.setEnabled(enabled)

    def enable_live_feed(self, enabled):
        self.live_option.setEnabled(enabled)

    @staticmethod
    def enable_button(button, checkbox):
        button.setEnabled(checkbox.isChecked())

    @staticmethod
    def update_pixmap(camera=False):
        if not camera:
            return QtGui.QPixmap(os.path.join(ICON_FOLDER, "black_grid_thick_lines_mirror.png"))
        else:
            return QtGui.QPixmap('recentImg.png')

    def clear_feed_scene(self):
        self.live_feed_scene.remove_crosshairs()

        for item in self.live_feed_scene.items():
            if item != self.feed_pointer:
                self.live_feed_scene.removeItem(item)

        for item in self.live_feed_scene.items():
            if item != self.feed_pointer:
                self.live_feed_scene.removeItem(item)

    def update_plots(self, rfu, current):
        self.plot_panel.canvas.update_rfu(rfu)
        self.plot_panel.canvas.update_current(current)
        self.plot_panel.canvas.set_style()
        self.plot_panel.canvas.draw()


class DataScreen(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)


class SystemScreen(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)


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
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt)
            painter.restore()


class AlteredTabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QTabWidget.__init__(self, *args, **kwargs)
        self.setTabBar(AlteredTabBar(self))
        if CUSTOM:
            with open("style.qss", "r") as qss:
                self.setStyleSheet(qss.read())
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
    calibrating_crosshairs = QtCore.pyqtSignal()

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
        self.calibrating = False
        self.crosshair_location = None

        self._selecting = False
        self._clearing = False
        self._start = QtCore.QPointF()
        self._current_rect_item = None
        self._current_ellipse_item = None
        self._top_hair = None
        self._bottom_hair = None
        self._left_hair = None
        self._right_hair = None
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
        logging.info('Getting shape with {}'.format(location))
        highlighted_item = self.itemAt(location[0], location[1], QtGui.QTransform())
        # logging.info(highlighted_item)
        if highlighted_item and type(highlighted_item) != QtWidgets.QGraphicsPixmapItem:
            # logging.info(highlighted_item.boundingRect().getRect())
            return highlighted_item.boundingRect().getRect()
        else:
            logging.info('Not found.')

    def get_shape(self, location):
        highlighted_item = self.itemAt(location[0], location[1], QtGui.QTransform())
        if highlighted_item and type(highlighted_item) != QtWidgets.QGraphicsPixmapItem:
            if type(highlighted_item) == QtWidgets.QGraphicsRectItem:
                return 'RECT'
            else:
                return 'ELLIPSE'

    def highlight_item(self, location):
        if not self._clearing:
            logging.debug('Highlighting at {}'.format(location))
            if self._highlighted_location:
                logging.debug('There is an item highlighted at {}'.format(self._highlighted_location))
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

                    self._highlighted_location = None

            highlighted_item = self.itemAt(location[0],
                                           location[1],
                                           QtGui.QTransform())
            for item in self.items():
                logging.debug(item.boundingRect())

            logging.debug(highlighted_item)

            if type(highlighted_item) != QtWidgets.QGraphicsPixmapItem:
                self._highlighted_location = location

                logging.debug('The type is not a pixmap.')
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
            else:
                highlighted_item.setZValue(-200)
                self.draw_crosshairs(location)

    def draw_rect(self, event, single=False):
        if single:
            self._current_rect_item = QtWidgets.QGraphicsRectItem()
            # self._current_rect_item.setBrush(QtCore.Qt.red)
            self._current_rect_item.setPen(QtGui.QPen(QtCore.Qt.green))
            self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self._current_rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            self.addItem(self._current_rect_item)
            r = QtCore.QRectF(QtCore.QPointF(event[0], event[1]), QtCore.QPointF(event[2], event[3]))
            self._current_rect_item.setRect(r)
            self._current_rect_item = None
            return

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
        self._current_rect_item.setZValue(200)

    def draw_circle(self, event, single=False):
        if single:
            self._current_ellipse_item = QtWidgets.QGraphicsEllipseItem()
            self._current_ellipse_item.setBrush(QtCore.Qt.red)
            self._current_ellipse_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self._current_ellipse_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            self.addItem(self._current_ellipse_item)
            r = QtCore.QRectF(event[0] - event[2], event[1] - event[2], event[2] * 2, event[2] * 2)
            self._current_ellipse_item.setRect(r)
            return

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
            r = QtCore.QRectF(event[0]-event[2], event[1]-event[2], event[2]*2, event[2]*2)
            logging.debug(r)
            self._current_ellipse_item.setRect(r)
            # self._current_ellipse_item = None
        self._current_ellipse_item.setZValue(200)

    def draw_array(self, event):
        marked_area = list(self._current_rect_item.boundingRect().getRect())
        if not self.joystick:
            pass
            logging.info('Cannot drag out an array yet.')
        else:
            radius = event[2]
            x = marked_area[0]
            y = marked_area[1]
            dx = marked_area[2] / (event[3] - 1)
            dy = marked_area[3] / (event[4] - 1)

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
                    self._current_ellipse_item.setZValue(200)
                    self._current_ellipse_item = None
                    # self.controller.add_row([x, y])
                    logging.info('adding shape with {}'.format([x, y]))
                    y += dy
                y = marked_area[1]
                x += dx

    def draw_line(self, event):
        pass

    def draw_crosshairs(self, event):
        self.crosshair_location = event
        self.calibrating_crosshairs.emit()

        crosshair_width = 2
        crosshair_length = 12
        center_radius = 4

        self.remove_crosshairs()

        top_hair_rect = QtCore.QRectF(event[0] - crosshair_width/2, event[1] - center_radius - crosshair_length,
                                      crosshair_width, crosshair_length)
        left_hair_rect = QtCore.QRectF(event[0] - center_radius - crosshair_length, event[1] - crosshair_width/2,
                                       crosshair_length, crosshair_width)
        right_hair_rect = QtCore.QRectF(event[0] + crosshair_width/2 + center_radius, event[1] - crosshair_width/2,
                                        crosshair_length, crosshair_width)
        bottom_hair_rect = QtCore.QRectF(event[0] - crosshair_width/2, event[1] + crosshair_width/2 + center_radius,
                                         crosshair_width, crosshair_length)

        self._top_hair = QtWidgets.QGraphicsRectItem()
        self._top_hair.setBrush(QtCore.Qt.yellow)
        self.addItem(self._top_hair)
        self._top_hair.setRect(top_hair_rect)

        self._bottom_hair = QtWidgets.QGraphicsRectItem()
        self._bottom_hair.setBrush(QtCore.Qt.yellow)
        self.addItem(self._bottom_hair)
        self._bottom_hair.setRect(bottom_hair_rect)

        self._left_hair = QtWidgets.QGraphicsRectItem()
        self._left_hair.setBrush(QtCore.Qt.yellow)
        self.addItem(self._left_hair)
        self._left_hair.setRect(left_hair_rect)

        self._right_hair = QtWidgets.QGraphicsRectItem()
        self._right_hair.setBrush(QtCore.Qt.yellow)
        self.addItem(self._right_hair)
        self._right_hair.setRect(right_hair_rect)

    def remove_crosshairs(self):
        if self._top_hair:
            self.removeItem(self._top_hair)
            self.removeItem(self._bottom_hair)
            self.removeItem(self._left_hair)
            self.removeItem(self._right_hair)

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

        self._current_rect_item = None
        self._current_ellipse_item = None

        if not self.joystick:
            super(GraphicsScene, self).mouseReleaseEvent(event)


class ValueDisplay(QtWidgets.QLineEdit):
    selected = QtCore.pyqtSignal()
    unselected = QtCore.pyqtSignal()

    def __init__(self):
        super(ValueDisplay, self).__init__()

    def focusInEvent(self, QFocusEvent):
        self.selected.emit()
        super(ValueDisplay, self).focusInEvent(QFocusEvent)

    def focusOutEvent(self, QFocusEvent):
        self.unselected.emit()
        super(ValueDisplay, self).focusOutEvent(QFocusEvent)


class WidgetContainer(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        if CUSTOM:
            with open("style.qss", "r") as qss:
                self.setStyleSheet(qss.read())


class SwitchButton(QtWidgets.QWidget):
    positive_selected = QtCore.pyqtSignal()
    negative_selected = QtCore.pyqtSignal()

    def __init__(self, parent=None, w1="Yes", l1=12, w2="No", l2=33, width=60):
        super(SwitchButton, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.__labeloff = QtWidgets.QLabel(self)
        self.__labeloff.setText(w2)
        self.__labeloff.setStyleSheet("""color: rgb(120, 120, 120); font-weight: bold;""")
        self.__background = Background(self)
        self.__labelon = QtWidgets.QLabel(self)
        self.__labelon.setText(w1)
        self.__labelon.setStyleSheet("""color: rgb(255, 255, 255); font-weight: bold;""")
        self.__circle = Circle(self)
        self.__circlemove = None
        self.__ellipsemove = None
        self.__enabled = True
        self.__duration = 100
        self.__value = False
        self.setFixedSize(width, 24)

        self.__background.resize(20, 20)
        self.__background.move(2, 2)
        self.__circle.move(2, 2)
        self.__labelon.move(l1, 5)
        self.__labeloff.move(l2, 5)

    def setDuration(self, time):
        self.__duration = time

    def mousePressEvent(self, event):
        if not self.__enabled:
            return

        self.__circlemove = QtCore.QPropertyAnimation(self.__circle, b"pos")
        self.__circlemove.setDuration(self.__duration)

        self.__ellipsemove = QtCore.QPropertyAnimation(self.__background, b"size")
        self.__ellipsemove.setDuration(self.__duration)

        xs = 2
        y = 2
        xf = self.width()-22
        hback = 20
        isize = QtCore.QSize(hback, hback)
        bsize = QtCore.QSize(self.width()-4, hback)
        if self.__value:
            xf = 2
            xs = self.width()-22
            bsize = QtCore.QSize(hback, hback)
            isize = QtCore.QSize(self.width()-4, hback)

        self.__circlemove.setStartValue(QtCore.QPoint(xs, y))
        self.__circlemove.setEndValue(QtCore.QPoint(xf, y))

        self.__ellipsemove.setStartValue(isize)
        self.__ellipsemove.setEndValue(bsize)

        self.__circlemove.start()
        self.__ellipsemove.start()

        if self.__value:
            self.negative_selected.emit()
        else:
            self.positive_selected.emit()

        self.__value = not self.__value

    def paintEvent(self, event):
        s = self.size()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
        pen = QtGui.QPen(QtCore.Qt.NoPen)
        qp.setPen(pen)
        qp.setBrush(QtGui.QColor(120, 120, 120))
        qp.drawRoundedRect(0, 0, s.width(), s.height(), 12, 12)
        lg = QtGui.QLinearGradient(35, 30, 35, 0)
        lg.setColorAt(0, QtGui.QColor(210, 210, 210, 255))
        lg.setColorAt(0.25, QtGui.QColor(255, 255, 255, 255))
        lg.setColorAt(0.82, QtGui.QColor(255, 255, 255, 255))
        lg.setColorAt(1, QtGui.QColor(210, 210, 210, 255))
        qp.setBrush(lg)
        qp.drawRoundedRect(1, 1, s.width()-2, s.height()-2, 10, 10)

        qp.setBrush(QtGui.QColor(210, 210, 210))
        qp.drawRoundedRect(2, 2, s.width() - 4, s.height() - 4, 10, 10)

        if self.__enabled:
            lg = QtGui.QLinearGradient(50, 30, 35, 0)
            lg.setColorAt(0, QtGui.QColor(230, 230, 230, 255))
            lg.setColorAt(0.25, QtGui.QColor(255, 255, 255, 255))
            lg.setColorAt(0.82, QtGui.QColor(255, 255, 255, 255))
            lg.setColorAt(1, QtGui.QColor(230, 230, 230, 255))
            qp.setBrush(lg)
            qp.drawRoundedRect(3, 3, s.width() - 6, s.height() - 6, 7, 7)
        else:
            lg = QtGui.QLinearGradient(50, 30, 35, 0)
            lg.setColorAt(0, QtGui.QColor(200, 200, 200, 255))
            lg.setColorAt(0.25, QtGui.QColor(230, 230, 230, 255))
            lg.setColorAt(0.82, QtGui.QColor(230, 230, 230, 255))
            lg.setColorAt(1, QtGui.QColor(200, 200, 200, 255))
            qp.setBrush(lg)
            qp.drawRoundedRect(3, 3, s.width() - 6, s.height() - 6, 7, 7)
        qp.end()


class Circle(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Circle, self).__init__(parent)
        self.__enabled = True
        self.setFixedSize(20, 20)

    def paintEvent(self, event):
        s = self.size()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
        qp.setPen(QtCore.Qt.NoPen)
        qp.setBrush(QtGui.QColor(120, 120, 120))
        qp.drawEllipse(0, 0, 20, 20)
        rg = QtGui.QRadialGradient(int(self.width() / 2), int(self.height() / 2), 12)
        rg.setColorAt(0, QtGui.QColor(255, 255, 255))
        rg.setColorAt(0.6, QtGui.QColor(255, 255, 255))
        rg.setColorAt(1, QtGui.QColor(205, 205, 205))
        qp.setBrush(QtGui.QBrush(rg))
        qp.drawEllipse(1,1, 18, 18)

        qp.setBrush(QtGui.QColor(210, 210, 210))
        qp.drawEllipse(2, 2, 16, 16)

        if self.__enabled:
            lg = QtGui.QLinearGradient(3, 18,20, 4)
            lg.setColorAt(0, QtGui.QColor(255, 255, 255, 255))
            lg.setColorAt(0.55, QtGui.QColor(230, 230, 230, 255))
            lg.setColorAt(0.72, QtGui.QColor(255, 255, 255, 255))
            lg.setColorAt(1, QtGui.QColor(255, 255, 255, 255))
            qp.setBrush(lg)
            qp.drawEllipse(3,3, 14, 14)
        else:
            lg = QtGui.QLinearGradient(3, 18, 20, 4)
            lg.setColorAt(0, QtGui.QColor(230, 230, 230))
            lg.setColorAt(0.55, QtGui.QColor(210, 210, 210))
            lg.setColorAt(0.72, QtGui.QColor(230, 230, 230))
            lg.setColorAt(1, QtGui.QColor(230, 230, 230))
            qp.setBrush(lg)
            qp.drawEllipse(3, 3, 14, 14)
        qp.end()


class Background(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Background, self).__init__(parent)
        self.__enabled = True
        self.setFixedHeight(20)

    def paintEvent(self, event):
        s = self.size()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
        pen = QtGui.QPen(QtCore.Qt.NoPen)
        qp.setPen(pen)
        qp.setBrush(QtGui.QColor(154,205,50))
        if self.__enabled:
            qp.setBrush(QtGui.QColor(154, 190, 50))
            qp.drawRoundedRect(0, 0, s.width(), s.height(), 10, 10)

            lg = QtGui.QLinearGradient(0, 25, 70, 0)
            lg.setColorAt(0, QtGui.QColor(154, 184, 50))
            lg.setColorAt(0.35, QtGui.QColor(154, 210, 50))
            lg.setColorAt(0.85, QtGui.QColor(154, 184, 50))
            qp.setBrush(lg)
            qp.drawRoundedRect(1, 1, s.width() - 2, s.height() - 2, 8, 8)
        else:
            qp.setBrush(QtGui.QColor(150, 150, 150))
            qp.drawRoundedRect(0, 0, s.width(), s.height(), 10, 10)

            lg = QtGui.QLinearGradient(5, 25, 60, 0)
            lg.setColorAt(0, QtGui.QColor(190, 190, 190))
            lg.setColorAt(0.35, QtGui.QColor(230, 230, 230))
            lg.setColorAt(0.85, QtGui.QColor(190, 190, 190))
            qp.setBrush(lg)
            qp.drawRoundedRect(1, 1, s.width() - 2, s.height() - 2, 8, 8)
        qp.end()


class QPlainTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()

        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setMinimumWidth(self.widget.parent().frameGeometry().width())
        # self.widget.setFixedHeight(self.widget.parent().frameGeometry().height())
        self.widget.setStyleSheet("background-color: rgb(230, 230, 230);")

        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class MicroscopeView(QtWidgets.QWidget):
    update_feed = QtCore.pyqtSignal()
    def __init__(self):
        super(MicroscopeView, self).__init__()
        self.image = QtGui.QImage()

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        painter.drawImage(0, 0, self.image)
        self.setMinimumWidth(self.image.width())

    @QtCore.pyqtSlot(QtGui.QImage)
    def setImage(self, image):
        self.image = image
        self.update()


class PlotPanel(QtWidgets.QWidget):
    def __init__(self):
        super(PlotPanel, self).__init__()
        self.setWindowTitle("Graphing Area")

        self.canvas = RunPlot()
        self.linestyle = 'None'

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.canvas)

        self.setLayout(hbox)


class RunPlot(FigureCanvas):
    def __init__(self):
        fig = plt.figure()
        fig.set_facecolor('#F6F6F6')
        self.axes_rfu = fig.add_subplot(111)
        self.axes_current = self.axes_rfu.twinx()
        self.set_style()
        FigureCanvas.__init__(self, fig)

    def set_style(self):
        title_font_size = 12
        self.axes_current.set_ylabel("Current (mA)", fontsize=title_font_size)
        self.axes_current.set_facecolor('#FFFFFF')
        self.axes_rfu.set_xlabel("Time (µs)", fontsize=title_font_size)
        self.axes_rfu.set_ylabel("RFU (kV)", fontsize=title_font_size)
        self.axes_rfu.set_facecolor('#FFFFFF')

    def update_rfu(self, rfu):
        self.axes_rfu.clear()
        self.axes_rfu.plot(rfu, linewidth=3)

    def update_current(self, current):
        self.axes_current.clear()
        self.axes_current.plot(current, linewidth=3, color="C2")


def wrap_widget(widget):
    wrapper_widget = QtWidgets.QFrame()
    if CUSTOM:
        with open("style.qss", "r") as qss:
            wrapper_widget.setStyleSheet(qss.read())
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


class LoadNewMainWidget(AlteredTabWidget):
    def __init__(self):
        AlteredTabWidget.__init__(self)
        if CUSTOM:
            self.setStyle(AlteredProxyStyle())

        tab1 = QtWidgets.QWidget()
        tab2 = QtWidgets.QWidget()

        self.addTab(tab1, QtGui.QIcon(os.path.join(ICON_FOLDER, "folder.png")), "   Load")
        self.addTab(tab2, QtGui.QIcon(os.path.join(ICON_FOLDER, "add-file.png")), "   New")

        v1 = QtWidgets.QHBoxLayout()
        v2 = QtWidgets.QHBoxLayout()

        layouts = QtWidgets.QVBoxLayout()
        self.load_data = QtWidgets.QPushButton("                   Data")
        self.load_data.setObjectName('MAIN')
        if CUSTOM:
            with open("style.qss", "r") as qss:
                self.load_data.setStyleSheet(qss.read())
        self.load_data.setIcon(QtGui.QIcon(os.path.join(ICON_FOLDER, "graph.png")))
        self.load_data.setIconSize(QtCore.QSize(48, 48))

        self.load_method = QtWidgets.QPushButton("                   Method")
        self.load_method.setObjectName('MAIN')
        if CUSTOM:
            with open("style.qss", "r") as qss:
                self.load_method.setStyleSheet(qss.read())
        self.load_method.setIcon(QtGui.QIcon(os.path.join(ICON_FOLDER, "meter.png")))
        self.load_method.setIconSize(QtCore.QSize(48, 48))

        self.load_insert = QtWidgets.QPushButton("                   Insert")
        self.load_insert.setObjectName('MAIN')
        if CUSTOM:
            with open("style.qss", "r") as qss:
                self.load_insert.setStyleSheet(qss.read())
        self.load_insert.setIcon(QtGui.QIcon(os.path.join(ICON_FOLDER, "plastic.png")))
        self.load_insert.setIconSize(QtCore.QSize(48, 48))

        self.load_sequence = QtWidgets.QPushButton("                   Sequence")
        self.load_sequence.setObjectName('MAIN')
        if CUSTOM:
            with open("style.qss", "r") as qss:
                self.load_sequence.setStyleSheet(qss.read())
        self.load_sequence.setIcon(QtGui.QIcon(os.path.join(ICON_FOLDER, "tick.png")))
        self.load_sequence.setIconSize(QtCore.QSize(48, 48))

        v1.addSpacing(40)
        v1.addWidget(self.load_data)
        v1.addSpacing(40)
        v1.addWidget(self.load_method)
        v1.addSpacing(40)
        v2.addSpacing(40)
        v2.addWidget(self.load_insert)
        v2.addSpacing(40)
        v2.addWidget(self.load_sequence)
        v2.addSpacing(40)

        layouts.addLayout(v1)
        layouts.addLayout(v2)

        tab1.setLayout(layouts)

        v3 = QtWidgets.QHBoxLayout()
        v4 = QtWidgets.QHBoxLayout()

        layouts = QtWidgets.QVBoxLayout()
        self.new_data = QtWidgets.QPushButton("                   Data")
        self.new_data.setObjectName('MAIN')
        if CUSTOM:
            with open("style.qss", "r") as qss:
                self.new_data.setStyleSheet(qss.read())
        self.new_data.setIcon(QtGui.QIcon(os.path.join(ICON_FOLDER, "graph.png")))
        self.new_data.setIconSize(QtCore.QSize(48, 48))

        self.new_method = QtWidgets.QPushButton("                   Method")
        self.new_method.setObjectName('MAIN')
        if CUSTOM:
            with open("style.qss", "r") as qss:
                self.new_method.setStyleSheet(qss.read())
        self.new_method.setIcon(QtGui.QIcon(os.path.join(ICON_FOLDER, "meter.png")))
        self.new_method.setIconSize(QtCore.QSize(48, 48))

        self.new_insert = QtWidgets.QPushButton("                   Insert")
        self.new_insert.setObjectName('MAIN')
        if CUSTOM:
            with open("style.qss", "r") as qss:
                self.new_insert.setStyleSheet(qss.read())
        self.new_insert.setIcon(QtGui.QIcon(os.path.join(ICON_FOLDER, "plastic.png")))
        self.new_insert.setIconSize(QtCore.QSize(48, 48))

        self.new_sequence = QtWidgets.QPushButton("                   Sequence")
        self.new_sequence.setObjectName('MAIN')
        if CUSTOM:
            with open("style.qss", "r") as qss:
                self.new_sequence.setStyleSheet(qss.read())
        self.new_sequence.setIcon(QtGui.QIcon(os.path.join(ICON_FOLDER, "tick.png")))
        self.new_sequence.setIconSize(QtCore.QSize(48, 48))

        v3.addSpacing(40)
        v3.addWidget(self.new_data)
        v3.addSpacing(40)
        v3.addWidget(self.new_method)
        v3.addSpacing(40)
        v4.addSpacing(40)
        v4.addWidget(self.new_insert)
        v4.addSpacing(40)
        v4.addWidget(self.new_sequence)
        v4.addSpacing(40)

        layouts.addLayout(v3)
        layouts.addLayout(v4)

        tab2.setLayout(layouts)

        self.setFixedSize(1000, 240)

        # self.load_data.released.connect(lambda: )


class SystemSelectionWidget(AlteredTabWidget):
    def __init__(self):
        AlteredTabWidget.__init__(self)
        if CUSTOM:
            with open("style.qss", "r") as qss:
                self.setStyleSheet(qss.read())

        tab1 = QtWidgets.QWidget()

        self.addTab(tab1, "   System")
        tab1.layout = QtWidgets.QVBoxLayout()

        barracuda_button = QtWidgets.QPushButton("       Barracuda")
        barracuda_button.setObjectName('MAIN')
        barracuda_button.setIcon(QtGui.QIcon(os.path.join(ICON_FOLDER, "7079-200.png")))
        barracuda_button.setIconSize(QtCore.QSize(48, 48))
        finch_button = QtWidgets.QPushButton("       Finch")
        finch_button.setObjectName('MAIN')
        finch_button.setIcon(QtGui.QIcon(os.path.join(ICON_FOLDER, "angry-birds.png")))
        finch_button.setIconSize(QtCore.QSize(48, 48))
        ostrich_button = QtWidgets.QPushButton("       Ostrich")
        ostrich_button.setObjectName('MAIN')
        ostrich_button.setIcon(QtGui.QIcon(os.path.join(ICON_FOLDER, "ostrich.png")))
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


class RinseDialog(QtWidgets.QDialog):
    def __init__(self, pos_function=None, inlet=None, outlet=None):
        self._inlet = inlet
        self._outlet = outlet

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

        single_cell_check = QtWidgets.QCheckBox()
        self.form_data['SingleCell'] = single_cell_check.isChecked
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        if pos_function:
            button_box.accepted.connect(lambda: pos_function('Rinse', self.form_data))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        forms_layout = QtWidgets.QVBoxLayout()
        top_forms = QtWidgets.QHBoxLayout()
        lower_forms = QtWidgets.QHBoxLayout()
        lower_right_forms = QtWidgets.QVBoxLayout()
        bottom_options = QtWidgets.QHBoxLayout()

        lower_right_forms.addWidget(self.pressure_direction_form)
        lower_right_forms.addWidget(self.at_time_form)
        lower_forms.addWidget(self.tray_positions_form)
        lower_forms.addLayout(lower_right_forms)
        top_forms.addWidget(self.pressure_type_form)
        top_forms.addWidget(self.values_form)
        forms_layout.addLayout(top_forms)
        forms_layout.addLayout(lower_forms)
        main_layout.addLayout(forms_layout)
        # bottom_options.addWidget(single_cell_check)
        # bottom_options.addWidget(QtWidgets.QLabel('Single Cell'))
        bottom_options.addStretch()
        bottom_options.addWidget(button_box)
        main_layout.addLayout(bottom_options)

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

        wid = QtWidgets.QLabel('s')
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
        wid.setText(self._inlet)
        wid.setReadOnly(True)
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
        wid.setText(self._outlet)
        wid.setEnabled(False)
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
        # row = QtWidgets.QHBoxLayout()
        # wid = QtWidgets.QPushButton('Trays ...')
        # # self.form_data['TrayPositionsTraysPushbutton'] = wid
        # wid.setFixedWidth(60)
        # wid.setEnabled(True)
        # row.addSpacing(30)
        # row.addWidget(wid)
        # layout.addRow(row)

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
        row.addWidget(QtWidgets.QLabel('s'))
        row.addStretch()
        layout.addRow(row)

        self.at_time_form.setLayout(layout)


class SeparateDialog(QtWidgets.QDialog):
    def __init__(self, pos_function=None, inlet=None, outlet=None):
        QtWidgets.QDialog.__init__(self)
        self._inlet = inlet
        self._outlet = outlet

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

        single_cell_check = QtWidgets.QCheckBox()
        self.form_data['SingleCell'] = single_cell_check.isChecked
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        if pos_function:
            button_box.accepted.connect(lambda: pos_function('Separate', self.form_data))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        forms_layout = QtWidgets.QHBoxLayout()
        left_column = QtWidgets.QVBoxLayout()
        center_column = QtWidgets.QVBoxLayout()
        right_column = QtWidgets.QVBoxLayout()
        bottom_options = QtWidgets.QHBoxLayout()

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
        # bottom_options.addWidget(single_cell_check)
        # bottom_options.addWidget(QtWidgets.QLabel('Single Cell'))
        bottom_options.addStretch()
        bottom_options.addWidget(button_box)
        main_layout.addLayout(bottom_options)

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
        row.addWidget(QtWidgets.QLabel('kV'))
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
        row.addWidget(QtWidgets.QLabel('s'))
        row.addStretch()
        layout.addRow(row)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel('Ramp Time:'))
        wid = QtWidgets.QLineEdit()
        self.form_data['ValuesRampTimeEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)
        row.addWidget(QtWidgets.QLabel('s'))
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
        wid.setText(self._inlet)
        wid.setReadOnly(True)
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
        wid.setText(self._outlet)
        wid.setEnabled(False)
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
        # row = QtWidgets.QHBoxLayout()
        # wid = QtWidgets.QPushButton('Trays ...')
        # # self.form_data['TrayPositionsTraysPushbutton'] = wid
        # wid.setFixedWidth(60)
        # wid.setEnabled(True)
        # row.addSpacing(30)
        # row.addWidget(wid)
        # layout.addRow(row)

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
        row.addWidget(QtWidgets.QLabel('s'))
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
    def __init__(self, pos_function=None, inlet=None, outlet=None):
        QtWidgets.QDialog.__init__(self)
        self._inlet = inlet
        self._outlet = outlet

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

        self.single_cells_form = QtWidgets.QGroupBox('Single Cell')
        self.init_single_cell_form()

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        if pos_function:
            button_box.accepted.connect(lambda: pos_function('Inject', self.form_data))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        form_layout = QtWidgets.QHBoxLayout()
        left_column = QtWidgets.QVBoxLayout()
        right_column = QtWidgets.QVBoxLayout()
        bottom_options = QtWidgets.QHBoxLayout()

        left_column.addWidget(self.injection_type_form)
        left_column.addWidget(self.polarity_form)
        left_column.addWidget(self.pressure_direction_form)
        left_column.addWidget(self.sequence_table_form)
        right_column.addWidget(self.values_form)
        right_column.addWidget(self.tray_positions_form)
        form_layout.addLayout(left_column)
        form_layout.addLayout(right_column)
        main_layout.addLayout(form_layout)
        bottom_options.addWidget(self.single_cells_form)
        bottom_options.addStretch()
        bottom_options.addWidget(button_box)
        main_layout.addLayout(bottom_options)

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

        # VOLTAGE
        row = QtWidgets.QHBoxLayout()
        wid = QtWidgets.QLabel('Voltage:')
        row.addWidget(wid)

        wid = QtWidgets.QLineEdit()
        self.form_data['ValuesVoltageEdit'] = wid.text
        wid.setFixedWidth(60)
        row.addWidget(wid)

        wid = QtWidgets.QLabel('kV')
        row.addWidget(wid)

        row.addStretch()
        row.setAlignment(QtCore.Qt.AlignLeft)
        layout.addRow(row)

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

        wid = QtWidgets.QLabel('s')
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
        wid.setText(self._inlet)
        wid.setReadOnly(True)
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
        wid.setText(self._outlet)
        wid.setEnabled(False)
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
        # row = QtWidgets.QHBoxLayout()
        # wid = QtWidgets.QPushButton('Trays ...')
        # # self.form_data['TrayPositionsTraysPushbutton'] = wid
        # wid.setFixedWidth(60)
        # wid.setEnabled(True)
        # row.addSpacing(30)
        # row.addWidget(wid)
        # layout.addRow(row)

        self.tray_positions_form.setLayout(layout)

    def init_single_cell_form(self):
        def enable_options(enabled):
            auto_check.setEnabled(enabled)
            manual_check.setEnabled(enabled)

        layout = QtWidgets.QFormLayout()

        single_cell_check = QtWidgets.QCheckBox()
        auto_check = QtWidgets.QCheckBox()
        manual_check = QtWidgets.QCheckBox()

        auto_check.setEnabled(False)
        manual_check.setEnabled(False)
        single_cell_check.stateChanged.connect(lambda: enable_options(single_cell_check.isChecked()))

        row = QtWidgets.QHBoxLayout()
        row.addWidget(single_cell_check)
        row.addWidget(QtWidgets.QLabel('Single Cell'))
        row.addWidget(auto_check)
        row.addWidget(QtWidgets.QLabel('Auto'))
        row.addWidget(manual_check)
        row.addWidget(QtWidgets.QLabel('Manual'))
        layout.addRow(row)

        self.form_data['SingleCell'] = single_cell_check.isChecked
        self.form_data['AutoSingleCell'] = auto_check.isChecked
        self.form_data['ManualSingleCell'] = manual_check.isChecked

        self.single_cells_form.setLayout(layout)


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


class PermissionsMessageUI(QtWidgets.QDialog):
    def __init__(self, permissions_message=None, pos_function=None, neg_function=None, other_function=None, other_label=None, pos_label=None):
        super(PermissionsMessageUI, self).__init__()
        self.setWindowTitle('Permission')
        message = QtWidgets.QLabel(permissions_message)
        self.pos_button = QtWidgets.QPushButton('Okay') if not pos_label else QtWidgets.QPushButton(pos_label)
        self.neg_button = QtWidgets.QPushButton('Cancel')

        self.setMinimumWidth(300)
        self.setMinimumWidth(80)
        self.pos_button.setFixedWidth(80)
        self.neg_button.setFixedWidth(80)

        if pos_function:
            self.pos_button.released.connect(lambda: pos_function())

        if neg_function:
            self.neg_button.released.connect(lambda: neg_function())

        self.neg_button.released.connect(lambda: self.close())
        self.pos_button.released.connect(lambda: self.close())

        col = QtWidgets.QVBoxLayout()
        col.addWidget(message)
        col.setAlignment(message, QtCore.Qt.AlignCenter)
        row = QtWidgets.QHBoxLayout()

        if other_function and other_label:
            self.other_button = QtWidgets.QPushButton(other_label)
            self.other_button.setFixedWidth(80)
            self.other_button.released.connect(lambda: other_function())
            self.other_button.released.connect(lambda: self.close())
            row.addWidget(self.other_button)

        row.addWidget(self.pos_button)
        row.addWidget(self.neg_button)
        row.setAlignment(self.pos_button, QtCore.Qt.AlignRight)
        row.setAlignment(self.neg_button, QtCore.Qt.AlignLeft)
        col.addLayout(row)
        self.setLayout(col)

        self.exec_()


class InputMessageUI(QtWidgets.QDialog):
    def __init__(self, message=None):
        print(message)
