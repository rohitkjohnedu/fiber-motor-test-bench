# python packages
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QLabel, QGroupBox, QFormLayout, QPushButton, QCheckBox, QScrollArea, QDialog,
                             QComboBox, QLineEdit, QVBoxLayout, QHBoxLayout, QFrame, QFileDialog, QApplication, QTextEdit)
from PyQt6.QtGui import QIcon, QFont
import numpy as np
import time
import threading
from datetime import datetime
import os.path
# custom packages
from PowerSupply.ps_modes.static_characterization.static_ps import Static_PS
from StandaTable.standa_table import StandaTableWidget
from tools.gui_tools.py_toggle import PyToggle

class HelpDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Help: Static Characterization")

        layout = QVBoxLayout()

        # Adding text information with embedded images using HTML
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setFont(QFont("Arial", 12))
        html_content = """
        <style>
            body {
                font-family: Arial, sans-serif;
                font-size: 12pt;
                line-height: 1.5;
            }
        </style>
        <h2 style="text-decoration: underline;">How to use the Static Characterization mode?</h2>
        <p>1. Choose the mode of operation (Auto/Manual) by clicking on the respective label or toggle button.</p>
        <p>2. Choose the folder to save the data by clicking on the corresponding button.</p>
        <p>You can copy the path by clicking on the 'Current Folder' label. The default folder is 'DataFiles' in the program directory.</p>
        <p style="text-decoration: underline; line-height: 1.5;">3. Manual mode.</p>
        <p style="margin: 0 15px; line-height: 1.5;">3.1. Save data if necessary by checking the 'Save data' checkbox.</p>
        <p style="margin: 0 15px; line-height: 1.5;">3.2. Press the 'RUN' button to start the experiment. It unlocks the control panel.</p>
        <p style="margin: 0 15px; line-height: 1.5;">3.3. Click on the 'TARE FORCE' button to tare the force sensor.</p>
        <p style="margin: 0 15px; line-height: 1.5;">3.4. Control the actuator using the control panel box:</p>
        <p style="margin: 0 30px; line-height: 1.5;">3.4.1. Click on the 'Home' button to move the actuator to the home position and set zero.</p>
        <p style="margin: 0 30px; line-height: 1.5;">3.4.2. Control movement with the 'Backward' and 'Forward' buttons.</p>
        <p style="margin: 0 30px; line-height: 1.5;">3.4.3. Set the 'Speed' of the actuator. Max. speed 4 mm/s is for the translational stage.</p>
        <p style="margin: 0 30px; line-height: 1.5;">3.4.4. Set the desired 'Position' of the actuator. Max. resolution is 2.5 um for the translational stage.</p>
        <p style="margin: 0 30px; line-height: 1.5;">3.4.5. Use the 'Move' button to move the actuator to the desired position.</p>
        <p style="margin: 0 30px; line-height: 1.5;">3.4.5. Use the 'STOP' button to stop the actuator.</p>
        <p style="margin: 0 15px; line-height: 1.5;">3.5. Control the power supply using the control panel box:</p>
        <p style="margin: 0 30px; line-height: 1.5;">3.5.1. Set the 'Voltage' of the power supply. Range is 950-4500 V.</p>
        <p style="margin: 0 30px; line-height: 1.5;">3.5.2. Choose the control signal from the drop-down list. The figures below show the signal plots.</p>
        <div style="margin: 5; padding: 0;">
        <img src="Other/images/ABCDEF.png"/>
        </div>
        <div style="margin: 5; padding: 0;">
        <img src="Other/images/ADBECF.png"/>
        </div>
        <div style="margin: 5; padding: 0;">
        <img src="Other/images/Other.png"/>
        </div>
        <p style="line-height: 1.5;">States from 'A' to 'F' are DC voltages on the HV channels. States 'A', 'B', 'C' are opposite and equal to 'D', 'E', 'F'.
        States 'A-D', 'B-E', 'C-F' are unipolar AC voltages on the HV channels. The frequency is set within the range 1-1000 Hz. Duty cycle is always 50%.
        The 'Other' state is used for custom signals. The user can set the frequency, duty cycle, and phase of the signals.</p>
        <p style="margin: 0 30px; line-height: 1.5;">3.5.3. Press the 'SET' button or 'Enter' to set the power supply to the desired state. 
        To reset the power supply, press the 'RESET' button or set 0 V. Change target voltage and press 'Update' to apply changes.</p>
        <p style="margin: 0 15px; line-height: 1.5;">3.6. Write down parameters of the tested motor in the 'Parameters' box.</p>
        <p style="margin: 0 15px; line-height: 1.5;">3.7. Press the 'STOP' button to finish the measurement.</p>
        <p style="text-decoration: underline; line-height: 1.5;">4. Automatic mode.</p>
        <p style="margin: 0 15px; line-height: 1.5;">4.1. Choose the type of experiment from the drop-down list.</p>
        <p style="margin: 0 15px; line-height: 1.5;">4.2. Control the actuator using the control panel box:</p>
        <p style="margin: 0 30px; line-height: 1.5;">4.3.1. Check the 'Go home and set zero position' if you want to.</p>
        <p style="margin: 0 30px; line-height: 1.5;">4.3.2. Set the range of the position change and the step size. The max. resolution is 2.5 um. The max. speed is 4 mm/s.</p>
        <p style="margin: 0 15px; line-height: 1.5;">4.4. Control the power supply using the control panel box:</p>
        <p style="margin: 0 30px; line-height: 1.5;">4.4.1. For the 'Force vs. Position' experiment, set the target voltage and the control sequence.</p>
        <p style="margin: 0 30px; line-height: 1.5;">4.4.2. For the 'Force vs. Voltage and Position' experiment, set the voltage range, step size, and the control sequence.</p>
        <p style="margin: 0 30px; line-height: 1.5;">4.4.3. For the 'Force vs. Frequency and Position' experiment, set the target voltage, frequency range, and step size. The control sequence is modulated.</p>
        <p style="margin: 0 30px; line-height: 1.5;">4.4.4. There are two not-modulated sequences: 'A-B-C' and 'D-E-F'. The modulated sequence is '(A-D)-(B-E)-(C-F)', and requires the modulation frequency to be set.</p>
        <p style="margin: 0 15px; line-height: 1.5;">4.5. Write down parameters of the tested motor in the 'Parameters' box.</p>
        <p style="margin: 0 15px; line-height: 1.5;">4.6. Press the 'RUN' button to start the experiment.</p>
        <p style="margin: 0 15px; line-height: 1.5;">4.7. The data is automatically saved in the selected folder.</p>
        <p style="margin: 0 15px; line-height: 1.5;">4.8. Press the 'STOP' button to stop the experiment if necessary.</p>
        """
        
        info_text.setHtml(html_content)
        layout.addWidget(info_text)

        self.setLayout(layout)

    def show_on_secondary_screen(self):
        screens = QApplication.screens()
        if len(screens) > 1:
            secondary_screen = screens[1]
            screen_geometry = secondary_screen.geometry()
            self.setGeometry(
                screen_geometry.x() + 500,
                screen_geometry.y() + 200,
                1050,
                700
            )
        else:
            self.setGeometry(100, 100, 400, 300)
        self.show()


class StaticMode(QWidget):
    start_recording = pyqtSignal()
    stop_recording = pyqtSignal()
    finished = pyqtSignal()
    
    def __init__(self, power_supply=None, force_sensor=None, actuator=None, debug=1, parent=None):
        QWidget.__init__(self, parent=parent)

        # Event to stop the data recording.
        self.stop_event = threading.Event()

        # Components.
        self.power_supply = power_supply
        self.force_sensor = force_sensor
        self.actuator = actuator

        # Debugging flags.
        self.debug = debug
        if self.debug == 1:
            self.power_supply_debug = 0
            self.force_sensor_debug = 0
            self.actuator_debug = 0
        else:
            self.power_supply_debug = 1
            self.force_sensor_debug = 1
            self.actuator_debug = 1 

        # Variables.
        if not self.debug == 1:
            self.start_time = 0
            self.plot_interval = 50#ms
            self.sample_rate = 400#Hz
            self.interpolation_stop_time = 0

            # Timer for the data interpolation.
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.indiv_data_rcd)

            # Signals.
            self.start_recording.connect(self.start_indiv_rcd)
            self.stop_recording.connect(self.stop_indiv_rcd)
 
    # ************************************************************************************************************ #
    #                                     STATIC CHARACTERIZATION INTERFACE                                        #
    # ************************************************************************************************************ #

        self.characterization_type_layout = QVBoxLayout(self)
        # -------------------------------------------------------------------------------------------------------- #
        # Auto/Manual mode toggle.
        self.auto_mode_toggle = PyToggle()
        self.auto_mode_toggle.setChecked(True)

        self.auto_label = QLabel("Auto")
        self.auto_label.setStyleSheet("font-weight: bold;" "font-size: 22px")
        self.auto_label.setCursor(Qt.CursorShape.PointingHandCursor)

        self.manual_label = QLabel("Manual")
        self.manual_label.setStyleSheet("font-weight: normal;" "font-size: 22px")
        self.manual_label.setCursor(Qt.CursorShape.PointingHandCursor)

        self.auto_mode_layout = QHBoxLayout()
        self.auto_mode_layout.addWidget(self.auto_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.auto_mode_layout.addWidget(self.auto_mode_toggle, alignment=Qt.AlignmentFlag.AlignCenter)
        self.auto_mode_layout.addWidget(self.manual_label, alignment=Qt.AlignmentFlag.AlignCenter)
          
        self.characterization_type_layout.addLayout(self.auto_mode_layout)

        self.auto_mode_toggle.stateChanged.connect(self.auto_mode_changed)
        
        self.bottom_frame = QFrame()
        self.bottom_frame.setFrameShape(QFrame.Shape.HLine)
        self.bottom_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.characterization_type_layout.addWidget(self.bottom_frame)
        # -------------------------------------------------------------------------------------------------------- #
        # Help button.
        help_button = QPushButton("Help ")
        self.characterization_type_layout.addWidget(help_button)
        help_button.clicked.connect(self.show_help)

        help_icon = QIcon(os.path.join("Other/images/question.png"))
        
        help_button.setIcon(help_icon)
        help_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.bottom_frame1 = QFrame()
        self.bottom_frame1.setFrameShape(QFrame.Shape.HLine)
        self.bottom_frame1.setFrameShadow(QFrame.Shadow.Raised)
        self.characterization_type_layout.addWidget(self.bottom_frame1)
        # -------------------------------------------------------------------------------------------------------- #
        # Data save path.
        save_button = QPushButton("Choose folder to save data   ")
        save_button.clicked.connect(self.showSaveDialog)
        self.characterization_type_layout.addWidget(save_button)

        save_icon = QIcon(os.path.join("Other/images/save.png"))
        save_button.setIcon(save_icon)
        save_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.folder_path = "Default"
        self.save_folder_lbl = QLabel(f"Current Folder: {self.folder_path}")
        self.save_folder_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll_area = QScrollArea()
        self.scroll_area.setFixedHeight(40)
        self.scroll_area.setWidget(self.save_folder_lbl)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.characterization_type_layout.addWidget(self.scroll_area)

        self.save_folder_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_folder_lbl.mousePressEvent = self.copyToClipboard
        # -------------------------------------------------------------------------------------------------------- #
        self.init_ui('auto')
    
    # ************************************************************************************************************ #

    def showSaveDialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_path = folder_path
            self.save_folder_lbl.setText(f"Current Folder: {self.folder_path}")
            self.save_folder_lbl.setToolTip("Click to copy the path.")
    
    def copyToClipboard(self, e):
        clipboard = QApplication.clipboard()
        if self.folder_path == "Default":
            clipboard.setText(os.path.join(os.getcwd(), "DataFiles"))
        else:
            clipboard.setText(self.folder_path)

    # ************************************************************************************************************ #

    def init_ui(self, mode):

        self.control_panel_layout = QVBoxLayout()

        if mode == 'auto':
            # Type of experiment.
            experiment_type_layout = QFormLayout()
            experiment_type_label = QLabel("Experiment:")
            self.experiment_type = QComboBox()
            experiments = ['Force vs. Position', 'Force vs. Voltage and Position', 'Force vs. Frequency and Position']
            for experiment in experiments:
                self.experiment_type.addItem(experiment)
            experiment_type_layout.addRow(experiment_type_label, self.experiment_type)
            self.experiment_type.currentIndexChanged.connect(self.experiment_type_widgets)
            self.control_panel_layout.addLayout(experiment_type_layout)

            self.components_control_widgets(mode, exp_type=self.experiment_type.currentText())
            self.characterization_type_layout.addLayout(self.control_panel_layout)
        # -------------------------------------------------------------------------------------------------------- #

        elif mode == 'manual':
            # Data save option.
            data_save_opt_layout = QHBoxLayout()
            self.data_save_lbl = QLabel("Save data:")
            self.data_save_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.data_save_lbl.setFixedWidth(175)
            self.data_save_opt = QCheckBox()
            self.data_save_opt.setChecked(True) # Default is to save the data.
            data_save_opt_layout.addWidget(self.data_save_lbl)
            data_save_opt_layout.addWidget(self.data_save_opt)
            
            self.bottom_frame2 = QFrame()
            self.bottom_frame2.setFrameShape(QFrame.Shape.HLine)
            self.bottom_frame2.setFrameShadow(QFrame.Shadow.Raised)
            
            self.upper_control_layout = QVBoxLayout()
            self.upper_control_layout.addLayout(data_save_opt_layout)
            self.upper_control_layout.addWidget(self.bottom_frame2)
            # -------------------------------------------------------------------------------------------------------- #
            # Force sensor "Tare" button.
            self.tare_btn = QPushButton("TARE FORCE")
            if self.force_sensor is not None:
                self.tare_btn.clicked.connect(self.force_sensor.tare)
            self.tare_btn.setStyleSheet("background-color: white; "
                                    "color: black; "
                                    "font-weight: bold; "
                                    "font-size: 24px; "
                                    "position: center; ")
            self.control_panel_layout.addWidget(self.tare_btn)
        
            self.components_control_widgets(mode)
            self.disable_all_widgets(self.control_panel_layout, disable=1)

            self.upper_control_layout.addLayout(self.control_panel_layout)
            self.characterization_type_layout.addLayout(self.upper_control_layout)

    # ************************************************************************************************************ #

    # Change control interface based on the mode selected.
    def auto_mode_changed(self, auto):
        if auto:
            self.auto_mode_interface()
        else:
            self.manual_mode_interface()
            
    def manual_mode_interface(self):
        self.auto_mode_toggle.setChecked(False)
        self.auto_label.setStyleSheet("font-weight: normal; " "font-size: 22px")
        self.manual_label.setStyleSheet("font-weight: bold; " "font-size: 22px")
        self.clear_layout(self.control_panel_layout)
        self.init_ui('manual')

    def auto_mode_interface(self):
        self.auto_mode_toggle.setChecked(True)
        self.auto_label.setStyleSheet("font-weight: bold; " "font-size: 22px")
        self.manual_label.setStyleSheet("font-weight: normal; " "font-size: 22px")
        self.clear_layout(self.upper_control_layout)
        self.init_ui('auto')

    def mousePressEvent(self, event):
        if self.auto_label.underMouse():
            self.auto_mode_changed(auto=True)
        elif self.manual_label.underMouse():
            self.auto_mode_changed(auto=False)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    # Recursively clear nested layouts
                    self.clear_layout(item.layout())
            layout.deleteLater()

    # ************************************************************************************************************ #

    # Widgets for the control panel.
    def components_control_widgets(self, mode, exp_type=None):
        self.widgets_layout = QVBoxLayout()

        # Actuator control panel.
        self.actuator_control = StandaTableWidget(self.actuator, mode=mode, exp_type=exp_type)

        actuator_groupBox = QGroupBox("Actuator")
        actuator_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.widgets_layout.addWidget(actuator_groupBox)

        actuator_groupBox_layout = QFormLayout(actuator_groupBox)
        actuator_groupBox_layout.addRow(self.actuator_control)
        # -------------------------------------------------------------------------------------------------------- #
            
        # Power supply control panel.
        self.power_supply_control = Static_PS(self.power_supply, mode=mode, exp_type=exp_type, debug=self.debug)

        power_supply_groupBox = QGroupBox("Power Supply")
        power_supply_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.widgets_layout.addWidget(power_supply_groupBox)

        self.power_supply_groupBox_layout = QFormLayout(power_supply_groupBox)
        self.power_supply_groupBox_layout.addRow(self.power_supply_control)

        self.power_supply_control.set_button.clicked.connect(self.update_values)
        self.power_supply_control.update_button.clicked.connect(self.update_values)

        power_supply_groupBox.setLayout(self.power_supply_groupBox_layout)
        # -------------------------------------------------------------------------------------------------------- #

        # Other parameters.
        self.parameters_groupBox = QGroupBox("Parameters")
        self.parameters_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.widgets_layout.addWidget(self.parameters_groupBox)

        motor_type_lbl = QLabel("Motor Type:")
        motor_type_lbl.setFixedWidth(115)
        self.motor_type = QComboBox()
        motor_types = ['Motor Fiber', 'Motor Ribbon']
        for motor in motor_types:
            self.motor_type.addItem(motor)

        self.parameters_groupBox_layout = QFormLayout()
        self.parameters_groupBox_layout.addRow(motor_type_lbl, self.motor_type)
        self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)
        self.motor_type.currentIndexChanged.connect(self.motor_type_changed)

        self.motor_name_lbl = QLabel("Motor name:")
        self.motor_name = QLineEdit()
        self.parameters_groupBox_layout.addRow(self.motor_name_lbl, self.motor_name)

        self.motor_length_lbl = QLabel("Fiber length (mm):")
        self.motor_length = QLineEdit()
        self.parameters_groupBox_layout.addRow(self.motor_length_lbl, self.motor_length)

        self.motor_number_lbl = QLabel("Number of fibers:")
        self.motor_number = QLineEdit()
        self.parameters_groupBox_layout.addRow(self.motor_number_lbl, self.motor_number)

        self.insulator_lbl = QLabel("Insulator:")
        self.insulator = QLineEdit()
        self.parameters_groupBox_layout.addRow(self.insulator_lbl, self.insulator)

        self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)

        self.stator_name_lbl = QLabel("Stator name:")
        self.slider_name_lbl = QLabel("Slider name:")

        self.widgets_layout.addStretch(1)
        self.control_panel_layout.addLayout(self.widgets_layout)
        
    # ************************************************************************************************************ #

    def experiment_type_widgets(self):
        self.clear_layout(self.widgets_layout)
        experiment_text = self.experiment_type.currentText()
        # print("\n[INFO] The experiment type is: ", experiment_text)
        if experiment_text == 'Force vs. Position':
            self.components_control_widgets(mode='auto', exp_type=experiment_text)
        if experiment_text == 'Force vs. Voltage and Position':
            self.components_control_widgets(mode='auto', exp_type=experiment_text)
        elif experiment_text == 'Force vs. Frequency and Position':
            self.components_control_widgets(mode='auto', exp_type=experiment_text)

    # ************************************************************************************************************ #

    def motor_type_changed(self):
        if self.motor_type.currentText() == 'Motor Fiber':
            self.parameters_groupBox_layout.removeRow(self.stator_name_lbl)
            self.parameters_groupBox_layout.removeRow(self.slider_name_lbl)
            # -------------------------------------------------------------------------------------------------------- #
            self.motor_name_lbl = QLabel("Motor name:")
            self.motor_name = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.motor_name_lbl, self.motor_name)
            # -------------------------------------------------------------------------------------------------------- #
            self.motor_length_lbl = QLabel("Fiber length (mm):")
            self.motor_length = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.motor_length_lbl, self.motor_length)
            # -------------------------------------------------------------------------------------------------------- #
            self.motor_number_lbl = QLabel("Number of fibers:")
            self.motor_number = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.motor_number_lbl, self.motor_number)
            # -------------------------------------------------------------------------------------------------------- #
            self.insulator_lbl = QLabel("Insulator:")
            self.insulator = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.insulator_lbl, self.insulator)
            # -------------------------------------------------------------------------------------------------------- #
            self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)

        elif self.motor_type.currentText() == 'Motor Ribbon':
            self.parameters_groupBox_layout.removeRow(self.motor_name_lbl)
            self.parameters_groupBox_layout.removeRow(self.motor_length_lbl)
            self.parameters_groupBox_layout.removeRow(self.motor_number_lbl)
            self.parameters_groupBox_layout.removeRow(self.insulator_lbl)
            # -------------------------------------------------------------------------------------------------------- #
            self.stator_name_lbl = QLabel("Stator name:")
            self.stator_name = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.stator_name_lbl, self.stator_name)
            # -------------------------------------------------------------------------------------------------------- #
            self.slider_name_lbl = QLabel("Slider name:")
            self.slider_name = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.slider_name_lbl, self.slider_name)
            # -------------------------------------------------------------------------------------------------------- #
            self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)
    
    # ************************************************************************************************************ #

    def disable_all_widgets(self, layout, disable=1):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() is not None:
                item.widget().setDisabled(disable)
            elif item.layout() is not None:
                self.disable_all_widgets(item.layout(), disable)

    # ************************************************************************************************************ #

    def run_static(self):
        self.formatted_time = datetime.now().strftime('%H-%M-%S_%d-%m-%Y')  # Get the current date and time as a str
        self.zero_step_flag = 0
        self.out_of_range_volt_flag = 0
        self.zero_step_volt_flag = 0
        self.out_of_range_freq_flag = 0
        self.zero_step_freq_flag = 0
        self.experiment_text = self.experiment_type.currentText()
        # --------------------------------------------------------------------------------- #
        if self.experiment_text == 'Force vs. Position':
            voltage = float(self.power_supply_control.target_voltage_edit.text())
            if not (950<voltage<4500):
                self.out_of_range_volt_flag = 1
                self.finished.emit() # set the finished event
            else:
                self.force_vs_position()
                if not self.stop_event.is_set():
                    self.finished.emit() # set the finished event
        # --------------------------------------------------------------------------------- #
        elif self.experiment_text == 'Force vs. Voltage and Position': # Min. volt = 950 V, max. volt = 4500 V
            # Get the power supply parameters.
            start_volt = float(self.power_supply_control.start_volt_edit.text())        
            end_volt = float(self.power_supply_control.end_volt_edit.text())
            if not (950<=start_volt<=4500) or not (950<=end_volt<=4500):
                self.out_of_range_volt_flag = 1
                if not self.stop_event.is_set():
                    self.finished.emit() # set the finished event
            else:
                step_size = float(self.power_supply_control.step_volt_edit.text())
                # Calculate the number of steps.
                if step_size == 0 and end_volt != start_volt:
                    self.zero_step_volt_flag = 1
                    if not self.stop_event.is_set():
                        self.finished.emit() # set the finished event
                else:
                    if end_volt == start_volt:
                        steps_nb = 0
                    else:
                        steps_nb = np.abs(np.floor(np.round((end_volt - start_volt) / (step_size), 10)))
                    for step in range(int(steps_nb)+1):
                        voltage = start_volt+step*step_size
                        self.power_supply_control.target_voltage_edit.setText(str(voltage))
                        self.force_vs_position()
                    if not self.stop_event.is_set():
                        self.finished.emit() # set the finished event
        # --------------------------------------------------------------------------------- #
        elif self.experiment_text == 'Force vs. Frequency and Position': # Min. freq = 0 Hz, max. freq = 1000 Hz
            # Get the power supply parameters.
            voltage = float(self.power_supply_control.target_voltage_edit.text())
            if not (950<voltage<4500):
                self.out_of_range_volt_flag = 1
                if not self.stop_event.is_set():
                    self.finished.emit() # set the finished event
            else:
                start_freq = float(self.power_supply_control.start_freq_edit.text())       
                end_freq = float(self.power_supply_control.end_freq_edit.text())
                if not (0<=start_freq<=1000) or not (0<=end_freq<=1000):
                    self.out_of_range_freq_flag = 1
                    if not self.stop_event.is_set():
                        self.finished.emit() # set the finished event
                else:
                    step_size = float(self.power_supply_control.step_freq_edit.text())
                    # Calculate the number of steps.
                    if step_size == 0 and end_freq != start_freq:
                        self.zero_step_freq_flag = 1
                        if not self.stop_event.is_set():
                            self.finished.emit() # set the finished event
                    else:
                        if end_freq == start_freq:
                            steps_nb = 0
                        else:
                            steps_nb = np.abs(np.floor(np.round((end_freq - start_freq) / (step_size), 10)))
                        for step in range(int(steps_nb)+1):
                            frequency = start_freq+step*step_size
                            self.power_supply_control.freq_edit.setText(str(frequency))
                            self.force_vs_position()
                        if not self.stop_event.is_set():
                            self.finished.emit() # set the finished event

    # ************************************************************************************************************ #

    def force_vs_position(self):
        # Get the actuator parameters.
        current_pos = self.actuator.get_position()
        start_pos = float(self.actuator_control.start_pos_edit.text())
        end_pos = float(self.actuator_control.end_pos_edit.text())
        step_size = float(self.actuator_control.step_size_edit.text())
        speed = float(self.actuator_control.speed_edit.text())

        # Set speed to the actuator.
        if speed > self.actuator.max_speed:
            speed = self.actuator.max_speed
        self.actuator.set_speed(speed)
            
        # Calculate the time to wait for the actuator to reach the position.
        if self.actuator_control.home_chckbox.isChecked():
            init_moving_time = start_pos / speed
        else:
            init_moving_time = np.abs(current_pos - start_pos) / speed

        moving_time = np.abs(end_pos - start_pos) / speed

        # Calculate the number of steps.
        if step_size == 0 and end_pos != start_pos:
            self.zero_step_flag = 1
        else:
            if end_pos == start_pos:
                steps_nb = 0
            else:
                steps_nb = np.abs(np.floor(np.round((end_pos - start_pos) / (step_size / 1000), 10)))  # number of steps
                # print("\n[INFO] The number of steps is: ", steps_nb)
            # ---------------------------------------------------------------------------------------------------- #
            # Get the power supply parameters.
            modulation = self.power_supply_control.modulation_opt.isChecked()
            # ---------------------------------------------------------------------------------------------------- #
            # Algorithm for the "Force vs Position" experiment.
            for step in range(int(steps_nb)+1):
                # print("\n[INFO] The step number is: ", step)
                # ------------------------------------------------------------------------------------------------ #
                if self.stop_event.is_set():
                    break
                # ------------------------------------------------------------------------------------------------ #
                self.position = start_pos+step*(step_size/1000) # calculate the position
                # print("\n[INFO] The actuator is moving to the position: ", self.position)
                self.actuator.move(self.position) # move the actuator to the position
                if step == 0:
                    time.sleep(init_moving_time+2) # wait for the actuator to reach the starting position
                else:
                    time.sleep(moving_time+2) # wait for the actuator to reach the next position
                self.force_sensor.tare() # tare the force sensor
                time.sleep(0.1) # wait for the force sensor to tare
                if modulation == False:
                    states_txt = self.power_supply_control.control_sequence.currentText() # get the states
                    if states_txt == 'A-B-C':
                        states = ['A', 'B', 'C']
                    elif states_txt == 'D-E-F':
                        states = ['D', 'E', 'F']
                else:
                    states = ['A-D', 'B-E', 'C-F']
                # print("\n[INFO] The power supply states are: ", states)
                for state in states:
                    # -------------------------------------------------------------------------------- #
                    if self.stop_event.is_set():
                        break
                    # -------------------------------------------------------------------------------- #
                    self.state = state # (for later use in the program)
                    self.force_sensor.tare() # tare the force sensor
                    time.sleep(0.1) # wait for the force sensor to tare
                    self.power_supply_control.set_pressed(state) # set the power supply to the state
                    # print("\n[INFO] The power supply is set to the state: ", state)
                    time.sleep(0.5) 
                    # -------------------------------------------------------------------------------- #
                    self.start_recording.emit() # record the data
                    # print("\n[INFO] The data is being recorded")
                    time.sleep(2) # measure for 2 seconds
                    self.stop_recording.emit() # stop recording the data
                    # print("\n[INFO] The data is stopped recording")
                    # -------------------------------------------------------------------------------- #
                    self.power_supply_control.reset_command(state) # reset the power supply
                    # print("\n[INFO] The power supply is reset")
                    time.sleep(2) # wait for 1 second
                # ------------------------------------------------------------------------------------------------ #
                if self.stop_event.is_set():
                    break

    # ************************************************************************************************************ #

    def start_indiv_rcd(self):
        if self.auto_mode_toggle.isChecked() == False: # Manual mode
            self.formatted_time = datetime.now().strftime('%H-%M-%S_%d-%m-%Y')  # Get the current date and time as a string
        self.start_time = time.perf_counter()
        self.timer.start(self.plot_interval)

    def stop_indiv_rcd(self):
        self.timer.stop()

    def indiv_data_rcd(self):
        # Get the new data from the components.
        if self.power_supply_debug == 1:
            new_power_supply_data = self.power_supply.get_new_data()
        if self.force_sensor_debug == 1:
            new_force_sensor_data = self.force_sensor.get_new_data()
        if self.actuator_debug == 1:
            new_actuator_data = self.actuator.get_new_data()
            
        # Interpolate the data.
        if len(new_power_supply_data)>0 and len(new_force_sensor_data)>0 and len(new_actuator_data)>0:
            if self.interpolation_stop_time < self.start_time:
                interpolation_start_time = self.start_time
            else:
                interpolation_start_time = self.interpolation_stop_time + 1/self.sample_rate

            smallest_last_sample = min(new_power_supply_data[-1,0], new_force_sensor_data[-1,0])
            differential_time_latest_sample = smallest_last_sample - self.start_time
            interpolated_latest_sample_number = np.floor(differential_time_latest_sample/(1/self.sample_rate))
            self.interpolation_stop_time = self.start_time + interpolated_latest_sample_number*(1/self.sample_rate)

            interpolation_time = np.arange(interpolation_start_time, self.interpolation_stop_time, 1/self.sample_rate)
            interpolated_force_sensor_data = np.interp(interpolation_time, new_force_sensor_data[:, 0], new_force_sensor_data[:, 1])
            interpolated_actuator_pos = np.interp(interpolation_time, new_actuator_data[:, 0], new_actuator_data[:, 1])
            interpolated_actuator_speed = np.interp(interpolation_time, new_actuator_data[:, 0], new_actuator_data[:, 2])
            interpolated_power_supply_data = np.zeros((len(interpolation_time), 11))
            for i1 in range(2, 11):
                interpolated_power_supply_data[:, i1] = np.interp(interpolation_time, new_power_supply_data[:, 0], new_power_supply_data[:, i1])

            # aquired data
            abs_time_s = interpolation_time
            rel_time_s = abs_time_s - self.start_time
            force_mN = interpolated_force_sensor_data
            position_mm = interpolated_actuator_pos
            speed_mm_s = interpolated_actuator_speed
            hv_set_kV = interpolated_power_supply_data[:,2]
            hv_vm_kV = interpolated_power_supply_data[:,3]
            hv_err_V = interpolated_power_supply_data[:,4]
            # lv_set_V = interpolated_power_supply_data[:,5]
            # lv_vm_V = interpolated_power_supply_data[:,6]
            # lv_err_V = interpolated_power_supply_data[:,7]
            cm_w1_uA = interpolated_power_supply_data[:,8]
            cm_w2_uA = interpolated_power_supply_data[:,9]
            cm_w3_uA = interpolated_power_supply_data[:,10]

            # Create a folder to store the data files if it doesn't exist.
            if self.folder_path == "Default":
                folder_name = 'DataFiles'
            else:
                folder_name = self.folder_path
            os.makedirs(folder_name, exist_ok=True)

            main_subfolder = os.path.join(folder_name, f"StaticCharacterization")
            os.makedirs(main_subfolder, exist_ok=True)

            # **************************************************************************************************** #
            if self.auto_mode_toggle.isChecked() == False: # Manual mode
                if self.data_save_opt.isChecked():
                    subfolder = os.path.join(main_subfolder, f"Manual")
                    os.makedirs(subfolder, exist_ok=True)
                    # ------------------------------------------------------------------------------------------------ #
                    # Create a temporary file to store the data.
                    self.temp_file_name = os.path.join(subfolder, f"temp_{self.formatted_time}.csv")
                    # ------------------------------------------------------------------------------------------------ #
                    # Interface parameters.
                    self.state_index = self.power_supply_control.state_index
                    if self.state_index >= 6:
                        if self.power_supply_control.set_button.text() == 'Reset':
                            state = np.full(len(interpolation_time), self.power_supply_control.st_comboBox.currentText(), dtype='<U32')
                            freq_Hz = np.full(len(interpolation_time), self.freq_Hz, dtype='<f8')
                            duty_cycle = np.full(len(interpolation_time), self.duty_cycle, dtype='<f8')
                            ph1 = np.full(len(interpolation_time), self.ph1, dtype='<f8')
                            ph2 = np.full(len(interpolation_time), self.ph2, dtype='<f8')
                            ph3 = np.full(len(interpolation_time), self.ph3, dtype='<f8')
                        else:
                            state = np.full(len(interpolation_time), '-', dtype='<U32')
                            freq_Hz = np.full(len(interpolation_time), '-', dtype='<U32')
                            duty_cycle = np.full(len(interpolation_time), '-', dtype='<U32')
                            ph1 = np.full(len(interpolation_time), '-', dtype='<U32')
                            ph2 = np.full(len(interpolation_time), '-', dtype='<U32')
                            ph3 = np.full(len(interpolation_time), '-', dtype='<U32')
                    else:
                        if self.power_supply_control.set_button.text() == 'Reset':
                            state = np.full(len(interpolation_time), self.power_supply_control.st_comboBox.currentText(), dtype='<U32')
                        else:
                            state = np.full(len(interpolation_time), '-', dtype='<U32')
                    # ------------------------------------------------------------------------------------------------ #
                    dtype = [('state', '<U32'), ('abs_time_s', '<f8'), ('rel_time_s', '<f8'),
                            ('force_mN', '<f8'), ('position_mm', '<f8'), ('speed_mm_s', '<f8'),
                            ('hv_set_kV', '<f8'), ('hv_vm_kV', '<f8'), ('hv_err_V', '<f8'),
                            # ('lv_set_V', '<f8'), ('lv_vm_V', '<f8'), ('lv_err_V', '<f8'),
                            ('cm_w1_uA', '<f8'), ('cm_w2_uA', '<f8'), ('cm_w3_uA', '<f8')]
                    
                    if self.state_index >= 6:
                        if self.power_supply_control.set_button.text() == 'Reset': 
                            new_elements = [('freq_Hz', '<f8'), ('duty_cycle_%', '<f8'),
                                            ('ph1_deg', '<f8'), ('ph2_deg', '<f8'), ('ph3_deg', '<f8')]
                        else:
                            new_elements = [('freq_Hz', '<U32'), ('duty_cycle_%', '<U32'),
                                            ('ph1_deg', '<U32'), ('ph2_deg', '<U32'), ('ph3_deg', '<U32')]
                        dtype.extend(new_elements)
                    # ------------------------------------------------------------------------------------------------ #
                    save_data = np.zeros(abs_time_s.size, dtype=dtype)
                    save_data['state'] = state
                    save_data['abs_time_s'] = abs_time_s
                    save_data['rel_time_s'] = rel_time_s
                    save_data['force_mN'] = force_mN
                    save_data['position_mm'] = position_mm
                    save_data['speed_mm_s'] = speed_mm_s
                    save_data['hv_set_kV'] = hv_set_kV
                    save_data['hv_vm_kV'] = hv_vm_kV
                    save_data['hv_err_V'] = hv_err_V
                    # save_data['lv_set_V'] = lv_set_V
                    # save_data['lv_vm_V'] = lv_vm_V
                    # save_data['lv_err_V'] = lv_err_V
                    save_data['cm_w1_uA'] = cm_w1_uA
                    save_data['cm_w2_uA'] = cm_w2_uA
                    save_data['cm_w3_uA'] = cm_w3_uA
                    if self.state_index >= 6:
                        save_data['freq_Hz'] = freq_Hz
                        save_data['duty_cycle_%'] = duty_cycle
                        save_data['ph1_deg'] = ph1
                        save_data['ph2_deg'] = ph2
                        save_data['ph3_deg'] = ph3
                    # ------------------------------------------------------------------------------------------------ #
                    with open(self.temp_file_name, 'ab') as t:
                        fmt = '%s, %.8f, %.4f, ' # state, abs_time_s, rel_time_s
                        fmt += '% 4.6f, %4.3f, %.1f, ' # force_mN, position_mm, speed_mm_s
                        fmt += '%5.1f, %5.1f, % 5.1f, ' # hv_set_kV, hv_vm_kV, hv_err_V
                        # fmt += '% 3.2f, % 3.2f, % 3.2f, ' # lv_set_V, lv_vm_V, lv_err_V
                        fmt += '% 3.1f, % 3.1f, % 3.1f' # cm_w1_uA, cm_w2_uA, cm_w3_uA
                        if self.state_index >= 6:
                            if self.power_supply_control.set_button.text() == 'Reset': 
                                fmt += ', %4.0f, %2.0f, %3.0f, %3.0f, %3.0f' # freq_Hz, duty_cycle, ph1, ph2, ph3
                            else:
                                fmt += ', %s, %s, %s, %s, %s' # freq_Hz, duty_cycle, ph1, ph2, ph3
                        np.savetxt(t, save_data, fmt=fmt)
                    # ------------------------------------------------------------------------------------------------ #
                    # Now write the final file combining parameters and data from the temporary file.
                    file_name = os.path.join(subfolder, f"date_{self.formatted_time}.csv")
                    with open(file_name, 'w') as final_file:
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write('--------------------Experiment_Info------------------------\n\n'
                                        f'Datetime: {self.formatted_time}\n'
                                        f'Characterization: Static\n'
                                        f'Mode: Manual\n')
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write('\n-----------------------Motor_Info--------------------------\n\n')
                        if self.motor_type.currentText() == 'Motor Fiber':
                            final_file.write(f'Motor type: {self.motor_type.currentText()}\n'
                                            f'Motor name: {self.motor_name.text()}\n'
                                            f'Fiber length (mm): {self.motor_length.text()}\n'
                                            f'Number of fibers: {self.motor_number.text()}\n'
                                            f'Insulator: {self.insulator.text()}\n')
                        elif self.motor_type.currentText() == 'Motor Ribbon':
                            final_file.write(f'Motor type: {self.motor_type.currentText()}\n'
                                            f'Stator name: {self.stator_name.text()}\n'
                                            f'Slider name: {self.slider_name.text()}\n')
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write('\n---------------------Program_Info-------------------------\n\n'
                                        f'Sample rate (Hz): {self.sample_rate}\n')
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write('\n-------------------Explanatory_Note-----------------------\n\n'
                                        f'When the PS is set ON, the variables (state, freq, DC, phase shifts) '
                                        f'are recorded. If the PS is set OFF, the variables are recorded as "-".\n'
                                        f'Voltage aquired from the PS is recorded with a small delay raletivly to '
                                        f'the other variables. The delay is due to the PS response time.\n')              
                        # ----------------------------------------------------------------------------------------------------------------- #
                        final_file.write('\n----------------------Data_Info---------------------------\n\n')
                        final_file.write(f'state, abs. t (s), rel. t (s), '
                                        f'F (mN), p (mm), v (mm/s), '
                                        f'hv_set (kV), hv_vm (kV), hv_err (V), '
                                        #  f'lv_set (V), lv_vm (V), lv_err (V), '
                                        f'cm_w1 (uA), cm_w2 (uA), cm_w3 (uA)')
                        if self.state_index >= 6:
                            final_file.write(f', freq (Hz), DC (%), '
                                                f'ph1 (deg), ph2 (deg), ph3 (deg)\n\n')
                        else:
                            final_file.write('\n\n')
                        # ----------------------------------------------------------------------------------------------------------------- #
                        # Append the data from the temporary file to the final file.
                        with open(self.temp_file_name, 'r') as t:
                            data = t.read()
                            final_file.write(data)

            # **************************************************************************************************** #
            elif self.auto_mode_toggle.isChecked() == True: # Auto mode
                subfolder = os.path.join(main_subfolder, f"Auto")
                os.makedirs(subfolder, exist_ok=True)
                file_name = os.path.join(subfolder, f"date_{self.formatted_time}.csv")
                # ------------------------------------------------------------------------------------------------ #
                # Interface parameters.
                state = np.full(len(interpolation_time), self.state, dtype='<U32')
                if self.power_supply_control.modulation_opt.isChecked():
                    freq_Hz = np.full(len(interpolation_time), float(self.power_supply_control.freq_edit.text()), dtype='<f8')
                    duty_cycle = np.full(len(interpolation_time), float(self.power_supply_control.duty_cycle_edit.text()), dtype='<f8')
                    if self.state == 'A-D':
                        ph1 = np.full(len(interpolation_time), 0, dtype='<f8')
                        ph2 = np.full(len(interpolation_time), 180, dtype='<f8')
                        ph3 = np.full(len(interpolation_time), 0, dtype='<f8')
                    elif self.state == 'B-E':
                        ph1 = np.full(len(interpolation_time), 180, dtype='<f8')
                        ph2 = np.full(len(interpolation_time), 0, dtype='<f8')
                        ph3 = np.full(len(interpolation_time), 180, dtype='<f8')
                    elif self.state == 'C-F':
                        ph1 = np.full(len(interpolation_time), 180, dtype='<f8')
                        ph2 = np.full(len(interpolation_time), 180, dtype='<f8')
                        ph3 = np.full(len(interpolation_time), 0, dtype='<f8')
                # ------------------------------------------------------------------------------------------------ #
                dtype = [('state', '<U32'), ('abs_time_s', '<f8'), ('rel_time_s', '<f8'),
                        ('force_mN', '<f8'), ('position_mm', '<f8'), ('speed_mm_s', '<f8'),
                        ('hv_set_kV', '<f8'), ('hv_vm_kV', '<f8'), ('hv_err_V', '<f8'),
                        # ('lv_set_V', '<f8'), ('lv_vm_V', '<f8'), ('lv_err_V', '<f8'),
                        ('cm_w1_uA', '<f8'), ('cm_w2_uA', '<f8'), ('cm_w3_uA', '<f8')]
                
                if self.power_supply_control.modulation_opt.isChecked():
                    new_elements = [('freq_Hz', '<f8'), ('duty_cycle_%', '<f8'),
                                        ('ph1_deg', '<f8'), ('ph2_deg', '<f8'), ('ph3_deg', '<f8')]
                    dtype.extend(new_elements)
                # ------------------------------------------------------------------------------------------------ #
                save_data = np.zeros(abs_time_s.size, dtype=dtype)
                save_data['state'] = state
                save_data['abs_time_s'] = abs_time_s
                save_data['rel_time_s'] = rel_time_s
                save_data['force_mN'] = force_mN
                save_data['position_mm'] = position_mm
                save_data['speed_mm_s'] = speed_mm_s
                save_data['hv_set_kV'] = hv_set_kV
                save_data['hv_vm_kV'] = hv_vm_kV
                save_data['hv_err_V'] = hv_err_V
                # save_data['lv_set_V'] = lv_set_V
                # save_data['lv_vm_V'] = lv_vm_V
                # save_data['lv_err_V'] = lv_err_V
                save_data['cm_w1_uA'] = cm_w1_uA
                save_data['cm_w2_uA'] = cm_w2_uA
                save_data['cm_w3_uA'] = cm_w3_uA
                if self.power_supply_control.modulation_opt.isChecked():
                    save_data['freq_Hz'] = freq_Hz
                    save_data['duty_cycle_%'] = duty_cycle
                    save_data['ph1_deg'] = ph1
                    save_data['ph2_deg'] = ph2
                    save_data['ph3_deg'] = ph3
                # ------------------------------------------------------------------------------------------------ #
                if not os.path.isfile(file_name):
                    with open(file_name, 'w') as final_file:
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write('--------------------Experiment_Info------------------------\n\n'
                                         f'Datetime: {self.formatted_time}\n'
                                         f'Characterization: Static\n'
                                         f'Mode: Auto\n'
                                         f'Experiment: {self.experiment_text}\n')
                        # ------------------------------------------------------------------------------------------------ #
                        if self.power_supply_control.modulation_opt.isChecked():
                            final_file.write(f'Modulation: ON\n'
                                             f'Control sequence: {self.power_supply_control.control_seq_modul}\n'
                                             f'Modulation frequency (Hz): {self.power_supply_control.freq_edit.text()}\n')
                        else:
                            final_file.write(f'Modulation: OFF\n'
                                             f'Control sequence: {self.power_supply_control.control_sequence.currentText()}\n')
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write(f'Start position (mm): {self.actuator_control.start_pos_edit.text()}\n'
                                         f'End position (mm): {self.actuator_control.end_pos_edit.text()}\n'
                                         f'Step size (mm): {self.actuator_control.step_size_edit.text()}\n')
                        if not self.experiment_text == 'Force vs. Voltage and Position':
                            final_file.write(f'Target voltage (V): {self.power_supply_control.target_voltage_edit.text()}\n')
                            if self.experiment_text == 'Force vs. Frequency and Position':
                                final_file.write(f'Start mod. freq. (Hz): {self.power_supply_control.start_freq_edit.text()}\n'
                                                 f'End mod. freq. (Hz): {self.power_supply_control.end_freq_edit.text()}\n'
                                                 f'Step mod. freq. (Hz): {self.power_supply_control.step_freq_edit.text()}\n')
                        else:
                            final_file.write(f'Start voltage (V): {self.power_supply_control.start_volt_edit.text()}\n'
                                             f'End voltage (V): {self.power_supply_control.end_volt_edit.text()}\n'
                                             f'Step voltage (V): {self.power_supply_control.step_volt_edit.text()}\n')
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write('\n-----------------------Motor_Info--------------------------\n\n')
                        if self.motor_type.currentText() == 'Motor Fiber':
                            final_file.write(f'Motor type: {self.motor_type.currentText()}\n'
                                             f'Motor name: {self.motor_name.text()}\n'
                                             f'Fiber length (mm): {self.motor_length.text()}\n'
                                             f'Number of fibers: {self.motor_number.text()}\n'
                                             f'Insulator: {self.insulator.text()}\n')
                        elif self.motor_type.currentText() == 'Motor Ribbon':
                            final_file.write(f'Motor type: {self.motor_type.currentText()}\n'
                                             f'Stator name: {self.stator_name.text()}\n'
                                             f'Slider name: {self.slider_name.text()}\n')
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write('\n---------------------Program_Info-------------------------\n\n'
                                        f'Sample rate (Hz): {self.sample_rate}\n')
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write('\n----------------------Data_Info---------------------------\n\n')
                        final_file.write(f'state, abs. t (s), rel. t (s), '
                                         f'F (mN), p (mm), v (mm/s), '
                                         f'hv_set (kV), hv_vm (kV), hv_err (V), '
                                         #  f'lv_set (V), lv_vm (V), lv_err (V), '
                                         f'cm_w1 (uA), cm_w2 (uA), cm_w3 (uA)')
                        
                        if self.power_supply_control.modulation_opt.isChecked() == True:
                            final_file.write(f', freq (Hz), DC (%), '
                                             f'ph1 (deg), ph2 (deg), ph3 (deg)\n\n')
                        else:
                            final_file.write('\n\n')
                        # ------------------------------------------------------------------------------------------------ #
                with open(file_name, 'ab') as f:
                    fmt = '%s, %.8f, %.4f, ' # state, abs_time_s, rel_time_s
                    fmt += '% 4.6f, %4.3f, %.1f, ' # force_mN, position_mm, speed_mm_s
                    fmt += '%5.1f, %5.1f, % 5.1f, ' # hv_set_kV, hv_vm_kV, hv_err_V
                    # fmt += '% 3.2f, % 3.2f, % 3.2f, ' # lv_set_V, lv_vm_V, lv_err_V
                    fmt += '% 3.1f, % 3.1f, % 3.1f' # cm_w1_uA, cm_w2_uA, cm_w3_uA
                    if self.power_supply_control.modulation_opt.isChecked():
                        fmt += ', %3.0f, %2.0f, %3.0f, %3.0f, %3.0f' # freq_Hz, duty_cycle, ph1, ph2, ph3                
                    np.savetxt(f, save_data, fmt=fmt)
                    
    # ************************************************************************************************************ #
    def remove_temp_files(self):
        os.remove(self.temp_file_name)
    
    # ************************************************************************************************************ #
    def update_values(self):
        if self.state_index >= 6:
            self.freq_Hz = float(self.power_supply_control.freq_edit.text())
            self.duty_cycle = float(self.power_supply_control.duty_cycle_edit.text())
            if self.state_index == 6: # 'A-D'
                self.ph1 = 0
                self.ph2 = 180
                self.ph3 = 180
            elif self.state_index == 7: # 'B-E'
                self.ph1 = 180
                self.ph2 = 0
                self.ph3 = 180
            elif self.state_index == 8: # 'C-F'
                self.ph1 = 180
                self.ph2 = 180
                self.ph3 = 0
            elif self.state_index == 9: # 'Other'
                self.ph1 = float(self.power_supply_control.ch1_phase_shift_edit.text())
                self.ph2 = float(self.power_supply_control.ch2_phase_shift_edit.text())
                self.ph3 = float(self.power_supply_control.ch3_phase_shift_edit.text())
    
    # ************************************************************************************************************ #

    def show_help(self):
        self.help_dialog = HelpDialog()
        self.help_dialog.show_on_secondary_screen()
    
    ###############################################################################################################
    # ---------------------------------------- End of the Class ------------------------------------------------- #