        # self.static.auto_mode_toggle.stateChanged.connect(self.run_btn_wdgt_static)
        # self.dynamic.auto_mode_toggle.stateChanged.connect(self.run_btn_wdgt_dynamic)

        # self.characterization_type.currentChanged.connect(self.tab_changed)

        # self.run_btn_wdgt_static() # add the RUN button to the control panel

    # # Run button widget
    # def tab_changed(self):
    #     if self.characterization_type.currentIndex() == 0:
    #         self.run_btn_wdgt_static()
    #     elif self.characterization_type.currentIndex() == 1:
    #         self.run_btn_wdgt_dynamic()

    # # ************************************************************************************************************ #

    # def run_btn_wdgt_static(self):
    #     toggle_state = self.static.auto_mode_toggle.isChecked()
    #     if toggle_state == False and self.run_btn_wdgt_dynamic_flag == False and self.run_btn_wdgt_static_flag == False:
    #         # -------------------------------------------------------------------------------------------------------- #
    #         if self.emg_stop_btn is not None:
    #             self.emg_stop_btn.deleteLater()
    #         #--------------------------------------------------------------------------------------------------------- #
    #         self.run_button = QPushButton("RUN")
    #         if self.debug == 0: # if debug mode is OFF
    #             self.run_button.clicked.connect(self.run_button_clicked)
    #         self.run_button.setStyleSheet("background-color: green; "
    #                                         "color: white; "
    #                                         "font-weight: bold; "
    #                                         "font-size: 24px;"
    #                                         "position: center; ")
    #         self.control_panel_layout.addWidget(self.run_button)
    #         # -------------------------------------------------------------------------------------------------------- #
    #         self.run_btn_wdgt_static_flag = True
    #     # ------------------------------------------------------------------------------------------------------------ #
    #     elif toggle_state == False and self.run_btn_wdgt_dynamic_flag == True:
    #         pass
    #     # ------------------------------------------------------------------------------------------------------------ #
    #     elif toggle_state == True and self.run_btn_wdgt_dynamic_flag == False and self.run_btn_wdgt_static_flag == False:
    #         pass
    #     # ------------------------------------------------------------------------------------------------------------ #
    #     else:
    #         if self.run_button is not None:
    #             self.run_button.deleteLater()
    #         # -------------------------------------------------------------------------------------------------------- #
    #         self.run_button = QPushButton("RUN")
    #         if self.debug == 0: # if debug mode is OFF
    #             self.run_button.clicked.connect(self.run_button_clicked)
    #         self.run_button.setStyleSheet("background-color: green; "
    #                                         "color: white; "
    #                                         "font-weight: bold; "
    #                                         "font-size: 24px;"
    #                                         "position: center; ")
    #         self.control_panel_layout.addWidget(self.run_button)
    #         # -------------------------------------------------------------------------------------------------------- #
    #         self.emg_stop_btn = QPushButton("EMERGENCY STOP")
    #         if self.power_supply is not None:
    #             self.emg_stop_btn.clicked.connect(self.emg_stop_btn_clicked)
    #         self.emg_stop_btn.setStyleSheet("background-color: red; "
    #                                         "color: white; "
    #                                         "font-weight: bold; "
    #                                         "font-size: 24px; "
    #                                         "position: center; ")    
    #         self.control_panel_layout.addWidget(self.emg_stop_btn)
    #         # -------------------------------------------------------------------------------------------------------- #
    #         self.run_btn_wdgt_static_flag = False
    #         self.run_btn_wdgt_dynamic_flag = False
    # # ************************************************************************************************************ #

    # def run_btn_wdgt_dynamic(self):
    #     toggle_state = self.dynamic.auto_mode_toggle.isChecked()
    #     if toggle_state == False and self.run_btn_wdgt_static_flag == False and self.run_btn_wdgt_dynamic_flag == False:
    #         # -------------------------------------------------------------------------------------------------------- #
    #         if self.emg_stop_btn is not None:
    #             self.emg_stop_btn.deleteLater()
    #         # -------------------------------------------------------------------------------------------------------- #
    #         self.run_button = QPushButton("RUN")
    #         if self.debug == 0: # if debug mode is OFF
    #             self.run_button.clicked.connect(self.run_button_clicked)
    #         self.run_button.setStyleSheet("background-color: green; "
    #                                         "color: white; "
    #                                         "font-weight: bold; "
    #                                         "font-size: 24px;"
    #                                         "position: center; ")
    #         self.control_panel_layout.addWidget(self.run_button)
    #         # -------------------------------------------------------------------------------------------------------- #
    #         self.run_btn_wdgt_dynamic_flag = True
    #     # ------------------------------------------------------------------------------------------------------------ #
    #     elif toggle_state == False and self.run_btn_wdgt_static_flag == True:
    #         pass
    #     # ------------------------------------------------------------------------------------------------------------ #
    #     elif toggle_state == True and self.run_btn_wdgt_static_flag == False and self.run_btn_wdgt_dynamic_flag == False:
    #         pass
    #     # ------------------------------------------------------------------------------------------------------------ #
    #     else:
    #         if self.run_button is not None:
    #             self.run_button.deleteLater()
    #         # -------------------------------------------------------------------------------------------------------- #
    #         self.emg_stop_btn = QPushButton("EMERGENCY STOP")
    #         if self.power_supply is not None:
    #             self.emg_stop_btn.clicked.connect(self.emg_stop_btn_clicked)
    #         self.emg_stop_btn.setStyleSheet("background-color: red; "
    #                                         "color: white; "
    #                                         "font-weight: bold; "
    #                                         "font-size: 24px; "
    #                                         "position: center; ")    
    #         self.control_panel_layout.addWidget(self.emg_stop_btn)
    #         # -------------------------------------------------------------------------------------------------------- #
    #         self.run_btn_wdgt_static_flag = False
    #         self.run_btn_wdgt_dynamic_flag = False
    # # ************************************************************************************************************ #
    
    # def clear_layout(self, layout):
    #     if layout is not None:
    #         while layout.count():
    #             item = layout.takeAt(0)
    #             widget = item.widget()
    #             if widget is not None:
    #                 widget.deleteLater()
    #             else:
    #                 # Recursively clear nested layouts
    #                 self.clear_layout(item.layout())
    #         layout.deleteLater()