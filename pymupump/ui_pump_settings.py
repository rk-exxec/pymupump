# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pump_settings.ui'
##
## Created by: Qt User Interface Compiler version 6.2.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QAbstractSpinBox, QApplication, QDialogButtonBox,
    QDoubleSpinBox, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_pump_settings(object):
    def setupUi(self, pump_settings):
        if not pump_settings.objectName():
            pump_settings.setObjectName(u"pump_settings")
        pump_settings.resize(311, 203)
        self.verticalLayout = QVBoxLayout(pump_settings)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_5 = QLabel(pump_settings)
        self.label_5.setObjectName(u"label_5")

        self.verticalLayout.addWidget(self.label_5)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(pump_settings)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMinimumSize(QSize(90, 10))

        self.horizontalLayout.addWidget(self.label)

        self.diameter = QDoubleSpinBox(pump_settings)
        self.diameter.setObjectName(u"diameter")
        self.diameter.setValue(4.610000000000000)

        self.horizontalLayout.addWidget(self.diameter)

        self.label_3 = QLabel(pump_settings)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(20, 0))

        self.horizontalLayout.addWidget(self.label_3)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_2 = QLabel(pump_settings)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMinimumSize(QSize(90, 0))

        self.horizontalLayout_2.addWidget(self.label_2)

        self.flowrate = QDoubleSpinBox(pump_settings)
        self.flowrate.setObjectName(u"flowrate")
        self.flowrate.setMaximum(1000.000000000000000)
        self.flowrate.setValue(120.000000000000000)

        self.horizontalLayout_2.addWidget(self.flowrate)

        self.label_4 = QLabel(pump_settings)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMinimumSize(QSize(20, 0))

        self.horizontalLayout_2.addWidget(self.label_4)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_6 = QLabel(pump_settings)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_3.addWidget(self.label_6)

        self.slow_flowrate = QDoubleSpinBox(pump_settings)
        self.slow_flowrate.setObjectName(u"slow_flowrate")
        self.slow_flowrate.setMinimum(0.010000000000000)
        self.slow_flowrate.setMaximum(100.000000000000000)
        self.slow_flowrate.setSingleStep(0.010000000000000)
        self.slow_flowrate.setStepType(QAbstractSpinBox.DefaultStepType)
        self.slow_flowrate.setValue(3.000000000000000)

        self.horizontalLayout_3.addWidget(self.slow_flowrate)

        self.label_7 = QLabel(pump_settings)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_3.addWidget(self.label_7)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.buttonBox = QDialogButtonBox(pump_settings)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close|QDialogButtonBox.RestoreDefaults|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.buttonBox)

        self.line = QFrame(pump_settings)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.label_8 = QLabel(pump_settings)
        self.label_8.setObjectName(u"label_8")

        self.verticalLayout.addWidget(self.label_8)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.pump_reconnect_btn = QPushButton(pump_settings)
        self.pump_reconnect_btn.setObjectName(u"pump_reconnect_btn")

        self.horizontalLayout_4.addWidget(self.pump_reconnect_btn)


        self.verticalLayout.addLayout(self.horizontalLayout_4)


        self.retranslateUi(pump_settings)

        QMetaObject.connectSlotsByName(pump_settings)
    # setupUi

    def retranslateUi(self, pump_settings):
        pump_settings.setWindowTitle(QCoreApplication.translate("pump_settings", u"pump_settings", None))
        self.label_5.setText(QCoreApplication.translate("pump_settings", u"Enter new Values:", None))
        self.label.setText(QCoreApplication.translate("pump_settings", u"Syringe Diameter:", None))
        self.label_3.setText(QCoreApplication.translate("pump_settings", u"mm", None))
        self.label_2.setText(QCoreApplication.translate("pump_settings", u"Flowrate:", None))
        self.label_4.setText(QCoreApplication.translate("pump_settings", u"ul/m", None))
        self.label_6.setText(QCoreApplication.translate("pump_settings", u"Slow Flowrate:", None))
        self.label_7.setText(QCoreApplication.translate("pump_settings", u"ul/m", None))
        self.label_8.setText(QCoreApplication.translate("pump_settings", u"Other:", None))
        self.pump_reconnect_btn.setText(QCoreApplication.translate("pump_settings", u"Reconnect", None))
    # retranslateUi

