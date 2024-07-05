#     pymupump - Python interface to Harvard Apparatus Microliter OEM Syringe Pump
#     Copyright (C) 2024  Raphael Kriegl

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

import functools
from time import sleep
import winsound
from PySide6.QtCore import QFile, QSettings, QSize
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMainWindow, QAbstractButton, QDialog, QDialogButtonBox, QGridLayout, QSizePolicy, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QAbstractSpinBox, QSpacerItem
import pymupump as pmp
import logging
from serial.tools.list_ports_windows import comports

from qthread_worker import Worker, CallbackWorker

from typing import TYPE_CHECKING, Callable

from ui_pump_settings import Ui_pump_settings


# Pump control https://www.hugo-sachs.de/media/manuals/Product%20Manuals/702220,%202225%20Microliter%20Manual.pdf
# TODO error handling when no pump available!
# TODO put settings in extra dialog?

class PumpControl(QMainWindow):
    """
    provides a grupbox with UI to control the pump 
    """
    def __init__(self, parent=None) -> None:
        super(PumpControl, self).__init__(parent)
        self.settings = QSettings()
        self.ui = self
        self._context_depth = 0
        self._first_show = True
        self.worker: Worker = Worker(None)
        self._pump = None
        self.flowrate = self.settings.value("pump_control/flowrate", type=float, defaultValue=120.0)
        #if self.flowrate is None: self.flowrate = 120.0
        self.diameter = self.settings.value("pump_control/syr_diam", type=float, defaultValue=4.61)
        #if self.diameter is None: self.diameter = 4.61
        self.slow_flowrate = self.settings.value("pump_control/slow_flowrate", type=float, defaultValue=3.0)
        #if self.slow_flowrate is None: self.flowrate = 0.05
        self.isSlowFLow = False
        self.is_connected = False
        self.initialize_port()
        self.setupUI()

    @property
    def is_infusing(self) -> bool:
        return self._pump._running
        
    def check_connection(func: Callable):
        """Wrapper checks if connection to pump is active and will not execute function if no connection present

        :param func: function
        :type func: Callable
        """
        def null(*args, **kwargs):
            pass

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if args[0].is_connected:
                return func(*args, **kwargs)
            else:
                logging.info("Pump Control: no connection, not executing command")
                return null(*args, **kwargs)
        return wrapper

    def initialize_port(self):
        logging.debug("PumpControl: Initialize pump - port")
        port = self.find_com_port()
        try:
            if self._pump and not self._pump.serialcon.closed: 
                self._pump.serialcon.close()
            sleep(0.5)
            chain = pmp.Chain(port)
            self._pump = pmp.Microliter(chain, name='Microliter')
            self.is_connected = True
        except Exception as ex:
            self._pump = None
            self.is_connected = False
            logging.warning('PumpControl: Error: ' + str(ex))

    @check_connection
    def set_pump_prefs(self, stop=True):
        logging.debug("PumpControl: Initialize pump - settings")
        try:
            if stop:
                self._pump.stop()
            self._pump.setdiameter(self.diameter)
            self._pump.setflowrate(self.flowrate)
        except pmp.PumpError as pe:
            logging.warning(f'PumpControl: Init Failed: {str(pe)}')

    def reconnect(self):
        logging.warning('PumpControl: Reconnecting ...')
        self.initialize_port()
        if self._pump:
            self.set_pump_prefs()
            self.ui.setEnabled(self.is_connected)
            logging.warning('PumpControl: Reconnect Successfull')
        else:
            logging.warning('PumpControl: Reconnect Failed')

    def showEvent(self, event):
        if self._first_show:
            self.set_pump_prefs()
            self.connect_signals()
            if not self.is_connected:
                self.ui.setEnabled(False)
            self._first_show = False

    def connect_signals(self):
        self.ui.dispenseBtn.clicked.connect(self.infuse)
        self.ui.collectBtn.clicked.connect(self.withdraw)
        self.ui.fillBtn.clicked.connect(self.fill)
        self.ui.emptyBtn.clicked.connect(self.empty)
        self.ui.stopPumpBtn.clicked.connect(self.stop)
        self.ui.slow_disp_btn.clicked.connect(self.slow_infuse)
        self.ui.slow_withd_btn.clicked.connect(self.slow_withdraw)

    @check_connection
    def set_target_volume(self, volume):
        self._pump.settargetvolume(volume)

    @check_connection
    def set_normal_flow(self):
        self._pump.setflowrate(self.flowrate)
        self.isSlowFLow = False

    @check_connection
    def set_slow_flow(self):
        self._pump.setflowrate(self.slow_flowrate)
        self.isSlowFLow = True

    def fill(self):
        """ Pump will fill the current syringe to max level

        **Caution!** only use if limitswitches are properly setup to avoid damage to syringe
        """
        logging.info("PumpControl: filling syringe")
        if self.worker.isRunning():
            logging.error("PumpControl: error! pump not ready")
            return
        self.worker = CallbackWorker(self.set_target_volume, 1000, slotOnFinished=self.do_withdraw)
        self.worker.start()

    def empty(self):
        """ Pump will empty syringe completely  

        **Caution!** only use if limitswitches are properly setup to avoid damage to syringe
        """
        logging.info("PumpControl: emptying syringe")
        if self.worker.isRunning():
            logging.error("PumpControl: error! pump not ready")
            return
        self.worker = CallbackWorker(self.set_target_volume, 1000, slotOnFinished=self.do_infuse)
        self.worker.start()

    def infuse(self, amount=None):
        """ Pump will move plunger down until specified volume is displaced """
        amount = amount or self.ui.amountSpinBox.value()
        logging.info(f"PumpControl: infusing {amount} ul")
        if self.worker.isRunning():
            logging.error("PumpControl: error! pump not ready")
            return
        self.worker = CallbackWorker(self.set_target_volume, amount, slotOnFinished=self.do_infuse)
        self.worker.start()

    def slow_infuse(self, amount=None):
        self.set_slow_flow()
        self.infuse(amount)

    def withdraw(self, amount):
        """ Pump will move plunge up until specified volume is gained """
        amount = amount or self.ui.amountSpinBox.value()
        logging.info(f"PumpControl: withdrawing {amount} ul")
        if self.worker.isRunning():
            logging.error("PumpControl: error! pump not ready")
            return
        self.worker = CallbackWorker(self.set_target_volume, amount, slotOnFinished=self.do_withdraw)
        self.worker.start()

    def slow_withdraw(self, amount=None):
        self.set_slow_flow()
        self.withdraw(amount)

    @check_connection
    def do_withdraw(self):
        if self.worker.isRunning():
            logging.error("PumpControl: error! pump not ready")
            return
        self._pump.withdraw()
        self.worker = CallbackWorker(self._pump.waituntiltarget, slotOnFinished=self.afterMovement)
        self.worker.start()

    @check_connection
    def do_infuse(self):
        if self.worker.isRunning():
            logging.error("PumpControl: error! pump not ready")
            return
        try:
            self._pump.infuse()
            self.worker = CallbackWorker(self._pump.waituntiltarget, slotOnFinished=self.afterMovement)
            self.worker.start()
        except Exception as ex:
            logging.error(f"pump_control: error: {ex}")

    def afterMovement(self):
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        if self.isSlowFLow:
            self.set_normal_flow()

    def settings_dialog(self):
        dlg = PumpSettingsDialog(self,self,(self.diameter,self.flowrate, self.slow_flowrate))

    def apply_settings(self, diameter, flowrate, slow_flowrate):
        """ read the values from the ui and apply them to the pump """
        self.diameter = diameter
        self.flowrate = flowrate
        self.slow_flowrate = slow_flowrate
        self.settings.setValue("pump_control/flowrate", flowrate)
        self.settings.setValue("pump_control/syr_diam", diameter)
        self.settings.setValue("pump_control/slow_flowrate", slow_flowrate)
        self.set_pump_prefs(stop=False)
        logging.info(f"PumpControl: set syringe diameter to {diameter} mm, flowrate to {flowrate} ul/m")

    @check_connection
    def stop(self):
        """ Immediately stop the pump """
        self._pump.stop()

    @staticmethod
    def find_com_port() -> str:
        """ find the comport the pump is connected to """
        lst = comports()
        for port in lst:
            if port.manufacturer == 'Prolific':
                return port.device
        # else:
        #     raise ConnectionError('No Pump found!')

    def setupUI(self):
        self.setWindowTitle("PyMuPump")
        
        self.resize(800, 600)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setSpacing(6)
        self.verticalLayout_6.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setSpacing(6)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setSpacing(6)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.amountSpinBox = QDoubleSpinBox(self)
        self.amountSpinBox.setObjectName(u"amountSpinBox")


        # self.amountSpinBox.setMinimumSize(QSize(30, 0))
        self.amountSpinBox.setFrame(True)
        self.amountSpinBox.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.amountSpinBox.setDecimals(1)
        self.amountSpinBox.setMaximum(1000.000000000000000)
        self.amountSpinBox.setValue(2.000000000000000)

        self.horizontalLayout_7.addWidget(self.amountSpinBox)

        self.unitLbl1 = QLabel(self)
        self.unitLbl1.setObjectName(u"unitLbl1")

        # self.horizontalLayout_7.addWidget(self.unitLbl1)

        # self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        # self.horizontalLayout_7.addItem(self.horizontalSpacer)


        self.verticalLayout_5.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.dispenseBtn = QPushButton(self)
        self.dispenseBtn.setObjectName(u"dispenseBtn")

        self.horizontalLayout_3.addWidget(self.dispenseBtn)

        self.slow_disp_btn = QPushButton(self)
        self.slow_disp_btn.setObjectName(u"slow_disp_btn")

        self.horizontalLayout_3.addWidget(self.slow_disp_btn)


        self.verticalLayout_5.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setSpacing(6)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.collectBtn = QPushButton(self)
        self.collectBtn.setObjectName(u"collectBtn")

        self.horizontalLayout_9.addWidget(self.collectBtn)

        self.slow_withd_btn = QPushButton(self)
        self.slow_withd_btn.setObjectName(u"slow_withd_btn")

        self.horizontalLayout_9.addWidget(self.slow_withd_btn)


        self.verticalLayout_5.addLayout(self.horizontalLayout_9)


        self.verticalLayout_6.addLayout(self.verticalLayout_5)
        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setSpacing(6)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.emptyBtn = QPushButton(self)
        self.emptyBtn.setObjectName(u"emptyBtn")

        self.gridLayout_3.addWidget(self.emptyBtn, 1, 0, 1, 1)

        self.stopPumpBtn = QPushButton(self)
        self.stopPumpBtn.setObjectName(u"stopPumpBtn")

        self.gridLayout_3.addWidget(self.stopPumpBtn, 0, 0, 1, 1)

        self.fillBtn = QPushButton(self)
        self.fillBtn.setObjectName(u"fillBtn")

        self.gridLayout_3.addWidget(self.fillBtn, 1, 1, 1, 1)


        self.verticalLayout_6.addLayout(self.gridLayout_3)

        self.setLayout(self.verticalLayout_6)

        self.show()

class PumpSettingsDialog(QDialog, Ui_pump_settings):

    def __init__(self, parent, pump_control:PumpControl, initial_values=(0,0,0)):
        super().__init__(parent)
        #self.load_ui()
        self.setupUi(self)
        self.diameter.setValue(initial_values[0])
        self.flowrate.setValue(initial_values[1])
        self.slow_flowrate.setValue(initial_values[2])
        self = pump_control
        self.buttonBox.accepted.connect(self.apply_values)
        self.buttonBox.rejected.connect(self.close)
        self.buttonBox.clicked.connect(self.click)
        self.pump_reconnect_btn.clicked.connect(self.reconnect)
        self.show()

    def load_ui(self):
        loader = QUiLoader()
        path = "qt_resources/pump_settings_dialog/pump_settings.ui"
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        loader.load(ui_file, self)
        ui_file.close()

    def apply_values(self):
        self.apply_settings(self.diameter.value(), self.flowrate.value(), self.slow_flowrate.value())
        self.close()

    def click(self, button: QAbstractButton):
        if self.buttonBox.buttonRole(button) == QDialogButtonBox.ResetRole:
            self.diameter.setValue(4.61)
            self.flowrate.setValue(120.0)
            self.slow_flowrate.setValue(3.0)
    
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = PumpControl()
    w.show()
    sys.exit(app.exec())