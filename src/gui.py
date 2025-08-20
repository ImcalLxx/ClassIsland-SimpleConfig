# file: gui.py
# brief: UI模块
# time: 2025.8.19
# version: 0.1.0-Beta-1
# TODOs:
#   1. 其他功能进一步跟进(见demo.py)
#   2. 写一个task, 在用pyuic转换ui文件时纠错(这个不着急)

from PyQt5           import QtWidgets
from PyQt5.QtCore    import Qt, QObject, pyqtSignal, QSize
from PyQt5.QtWidgets import (QSystemTrayIcon, QMenu, QApplication, QMainWindow, QWidget, QApplication, QVBoxLayout, 
                             QLabel, QComboBox, QHBoxLayout)
from PyQt5.QtGui     import QIcon, QFont, QPixmap         # 用来选择文件的, 我懒得用PyQt了(
from class_manager   import ClassTable, TimeTable
from json_writer     import ALL_CLASSES, time2str_hm
from eventbus        import EventBus
from mytime          import MyTime
from typing          import Callable, Optional, NoReturn, Union
from mypath          import resPath
from loguru          import logger
import tkinter as tk
import sys, datetime, math, time

class QssLoader:
    """
    PyQt qss加载模块
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def loadGlobalQss(qssFilePath: str = resPath("res\\ciconfig_ui.qss")) -> str:
        """
        读取PyQt的qss文件

        Args:
            qssFilePath (str, optional): qss文件路径

        Returns:
            str: 读取到的qss文件
        """

        with open(qssFilePath, 'r', encoding='UTF-8') as file:
            return file.read()

class Gui(QObject):
    """
    图形UI类
    """

    myTime: MyTime
    eventBus: EventBus
    app: QApplication
    window: QMainWindow
    callBackFunc: Callable[[], None]
    _showMainWindow: bool = False

    # 以下为事件处理的信号
    # 需要与其他类通信的通过EventBus中继
    GUI_askForCallBackFunc_EB: pyqtSignal = pyqtSignal()

    GUI_cb_offset1_setDefaultText_UI: pyqtSignal = pyqtSignal()
    GUI_cb_offset2_setDefaultText_UI: pyqtSignal = pyqtSignal()

    GUI_exit_Main: pyqtSignal = pyqtSignal()

    GUI_setSAWidget_UI: pyqtSignal = pyqtSignal(object)

    # 滚动区域中选择框触发的公共信号, 所有滚动框触发都连接到此信号
    # int: 滚动框序号(即第N+1节课), str: 当前课程名称
    GUI_SAComboBox_currentIndexChanged_CT: pyqtSignal = pyqtSignal(int, str)

    def connectAllSingal(self) -> None:
        """
        绑定所有信号
        """

        self.GUI_askForCallBackFunc_EB.connect(self.eventBus.GUI_askForCallBackFunc_EB)
        def f1(f: Callable[[], None]): self.callBackFunc = f
        self.eventBus.EB_returnCallBackFunc_GUI.connect(f1)

        def f_debug(SA_contentToDisp):
            logger.debug(f"Singal GUI.EB_showMainWindow Triggered, contentToDisp: {type(SA_contentToDisp)}")
            self.showMainWindow(SA_contentToDisp)
        self.eventBus.EB_showMainWindow_GUI.connect(lambda SA_contentToDisp: f_debug(SA_contentToDisp))
        self.restoreAction.triggered.connect(self.eventBus.LG_showMainWindow_GUI)    # 借一下信号
        self.quitAction.triggered.connect(self.GUI_exit_Main)
        self.GUI_exit_Main.connect(self.eventBus.GUI_exit_Main)

        self.eventBus.EB_displaySAInfo_GUI.connect(lambda contentToDisp: self.SA_DisplayInfo(contentToDisp))

        self.GUI_setSAWidget_UI.connect(self.eventBus.GUI_setSAWidget)

        self.GUI_SAComboBox_currentIndexChanged_CT.connect(self.eventBus.GUI_SAComboBox_currentIndexChanged_CT)

        self.GUI_cb_offset1_setDefaultText_UI.connect(self.eventBus.GUI_cb_offset1_setDefaultText_UI)
        self.GUI_cb_offset2_setDefaultText_UI.connect(self.eventBus.GUI_cb_offset2_setDefaultText_UI)

    def createTrayIcon(self):
        """
        创建托盘图标
        """

        # 初始化托盘图标
        self.trayIcon = QSystemTrayIcon(self.window)
        self.trayIcon.setIcon(QIcon(resPath("res\\used_icons\\温迪_1.png")))  # 请确保有合适的图标路径

        # 使用QAction而不是QWidgetAction+QLabel
        self.restoreAction = QtWidgets.QAction(QIcon(resPath("res\\used_icons\\恢复屏幕.png")), "显示主界面 ", self.window)
        self.quitAction = QtWidgets.QAction(QIcon(resPath("res\\used_icons\\退出.png")), "退出", self.window)

        trayMenu = QMenu()
        trayMenu.addAction(self.restoreAction)
        trayMenu.addAction(self.quitAction)
        trayMenu.setStyleSheet(QssLoader.loadGlobalQss())
        
        self.trayIcon.setContextMenu(trayMenu)
        self.trayIcon.show()

    def SA_DisplayInfo(self, contentToDisp: Union[ClassTable, TimeTable]) -> None:
        """
        在滚动区域中显示信息

        Args:
            ui (Ui_MainWindow): ui实例
            contentToDisp (ClassTable | TimeTable): 要显示的内容
        """

        contentWidget = QWidget()
        self.contentLayout = QVBoxLayout(contentWidget)
        self.contentLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        if datetime.datetime.now().weekday() == 6:                      # 周日
            self.contentLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            label: QLabel = QLabel()
            font = QFont()
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font.setFamily("HarmonyOS Sans SC")
            font.setPointSize(13)
            label.setText(" 今天没有课程喵!")
            label.setFont(font)

            icon: QLabel = QLabel()
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setPixmap(QPixmap(resPath("res\\used_icons\\温迪_2.png")))
            icon.setScaledContents(True)
            icon.setText("")
            icon.setFixedSize(QSize(158, 135))
            
            self.contentLayout.addWidget(icon)
            self.contentLayout.addWidget(label)
            self.GUI_setSAWidget_UI.emit(contentWidget)
            return

        # 此处的逻辑如下:
        # 滚动区域可以显示课表或者时间表信息
        # 课表信息的格式为: (QLabel)"周一   第1节课"   (QComboBox)(选择框选课)
        # 时间表的格式为: (QLabel)"平日   第1节课"   (QLabel)"07:30-08:10"
        # 因此课表需要一个QLabel显示文本, 对应text, 时间表需要两个, 对应text和text2
        # 下面的函数是用来添加一行的组件的, 会根据SA_DisplayInfo传入的类型自动判断显示课表/时间表的布局方式
        def dp_AddRow(text: str, text2: Optional[str] = None, comboBoxDefaultText: Optional[str] = None, 
                      classIndex: Optional[int] = None):
            """
            添加行信息
            """
            enableComboBox: bool = True if isinstance(contentToDisp, ClassTable) else False     # 是否在右侧显示选择框

            rowWidget = QWidget()
            rowLayout = QHBoxLayout(rowWidget)
            rowLayout.setContentsMargins(18, 3, 35, 3)
            rowLayout.setSpacing(5)

            # 创建左侧的QLabel
            textOnLeft = QLabel(text)
            font = QFont()
            font.setFamily("HarmonyOS Sans SC")
            font.setPointSize(12)
            textOnLeft.setFont(font)
            rowLayout.addWidget(textOnLeft)

            # 创建右侧的选择框/文本框
            if enableComboBox:
                classSelect = QComboBox()

                # 添加个空格, 美观一些
                _ALL_CLASSES: list[str] = []
                for _class in ALL_CLASSES:
                    _ALL_CLASSES.append(" " + _class)

                # 此处不使用Qss进行全局设置
                classSelect.addItems(_ALL_CLASSES)
                classSelect.setFixedSize(115, 36)
                font = QFont()
                font.setFamily("HarmonyOS Sans SC")
                font.setPointSize(12)
                classSelect.setFont(font)
                if comboBoxDefaultText is not None and comboBoxDefaultText != "":
                    classSelect.setCurrentIndex(ALL_CLASSES.index(comboBoxDefaultText))
                def f():
                    logger.debug(f"ComboBox index changed! Index: {classIndex}, Now: {ALL_CLASSES[classSelect.currentIndex()]}")
                    self.GUI_SAComboBox_currentIndexChanged_CT.emit(
                        classIndex, ALL_CLASSES[classSelect.currentIndex()]
                    )
                classSelect.currentIndexChanged.connect(f)
                rowLayout.addWidget(classSelect, stretch=1)
            else:
                textOnRight = QLabel(text2)
                font = QFont()
                font.setFamily("HarmonyOS Sans SC")
                font.setPointSize(12)
                textOnRight.setFont(font)
                textOnRight.setAlignment(Qt.AlignmentFlag.AlignRight)
                rowLayout.addWidget(textOnRight)

            self.contentLayout.addWidget(rowWidget)

        LDAYINWEEK: list[str] = ["周一", "周二", "周三", "周四", "周五", "周六"]
        #* 我为了简洁, 把课表和时间表显示捏一个函数里了
        #* 但是写完我才发现这玩意可读性差的一批
        # TODO: 有空重构一下吧
        if isinstance(contentToDisp, ClassTable):                       # 显示课表
            # 遍历今日课表
            curDateTime = datetime.datetime.now()
            dayInWeek: int = curDateTime.weekday()
            text: str = LDAYINWEEK[dayInWeek]
            classIndex: int = 0

            for singleClass in contentToDisp.classTableToday:
                dp_AddRow(text + "   第" + str(classIndex + 1) + "节课", comboBoxDefaultText=singleClass.name, 
                          classIndex=classIndex)
                classIndex += 1
        else:                                                           # 显示时间表
            # 遍历时间表
            curDateTime = datetime.datetime.now()
            dayInWeek: int = curDateTime.weekday()
            time_20250707: int = 1751817600                             # 以2025/07/07 00:00:00为时间基准(此时为单周)
            timenow: int  = int(time.time())                            # 当前的时间戳
            curDateTime = datetime.datetime.now()
            secdiff: int = timenow - time_20250707
            SEC_PER_DAY: int = 86400
            daydiff = math.ceil(secdiff / SEC_PER_DAY)                  # 差的天数
            weekcount = ((daydiff % 2) + self.myTime.weekOffset1) % 2 # 单双周

            if dayInWeek != 5:                                          # 非周六
                text: str = "周一-周五"
                classIndex: int = 0

                if weekcount == 0:                                      # 单周
                    for timePeriod in contentToDisp.normTimeList1:
                        text2: str = time2str_hm(timePeriod.start) + " - " + time2str_hm(timePeriod.finish)
                        if timePeriod.timeType == 0:
                            dp_AddRow(text + "   第" + str(classIndex + 1) + "节课", text2)
                            classIndex += 1
                        elif timePeriod.timeType == 1:
                            dp_AddRow(text + "   课间", text2)
                        else:
                            dp_AddRow(text + "   分割线", time2str_hm(timePeriod.start))
                else:                                                   # 双周
                    for timePeriod in contentToDisp.normTimeList2:
                        text2: str = time2str_hm(timePeriod.start) + " - " + time2str_hm(timePeriod.finish)
                        if timePeriod.timeType == 0:
                            dp_AddRow(text + "   第" + str(classIndex + 1) + "节课", text2)
                            classIndex += 1
                        elif timePeriod.timeType == 1:
                            dp_AddRow(text + "   课间", text2)
                        else:
                            dp_AddRow(text + "   分割线", time2str_hm(timePeriod.start))

            else:                                                       # 周六
                text: str = "周六"
                classIndex: int = 0

                if weekcount == 0:                                      # 单周
                    for timePeriod in contentToDisp.satTimeList1:
                        text2: str = time2str_hm(timePeriod.start) + " - " + time2str_hm(timePeriod.finish)
                        if timePeriod.timeType == 0:
                            dp_AddRow(text + "   第" + str(classIndex + 1) + "节课", text2)
                            classIndex += 1
                        elif timePeriod.timeType == 1:
                            dp_AddRow(text + "   课间", text2)
                        else:
                            dp_AddRow(text + "   分割线", time2str_hm(timePeriod.start))
                else:                                                   # 双周
                    for timePeriod in contentToDisp.satTimeList2:
                        text2: str = time2str_hm(timePeriod.start) + " - " + time2str_hm(timePeriod.finish)
                        if timePeriod.timeType == 0:
                            dp_AddRow(text + "   第" + str(classIndex + 1) + "节课", text2)
                            classIndex += 1
                        elif timePeriod.timeType == 1:
                            dp_AddRow(text + "   课间", text2)
                        else:
                            dp_AddRow(text + "   分割线", time2str_hm(timePeriod.start))
                
        self.GUI_setSAWidget_UI.emit(contentWidget)

    def showMainWindow(self, contentToDisp: Union[ClassTable, TimeTable]) -> None:
        """
        显示主窗口
        """

        logger.debug(f"GUI.showMainWindow called, contentToDisp: {type(contentToDisp)}")
        self.window.show()
        self.SA_DisplayInfo(contentToDisp)

    def __init__(self, myTime: MyTime, eventBus: EventBus, app: QApplication, window: QMainWindow, parent = None) -> None:
        """
        Gui类初始化
        """
        
        super().__init__(parent)
        self.myTime = myTime
        self.eventBus = eventBus
        self.app = app
        self.window = window

        # 读取qss
        self.window.setStyleSheet(QssLoader.loadGlobalQss())

        # 初始化UI
        self.createTrayIcon()

        # 初始化Tkinter
        root = tk.Tk()
        root.withdraw()

    def init(self) -> None:
        """
        GUI初始化函数
        """

        logger.debug("开始初始化GUI")

        # 获取程序退出的回调函数
        self.GUI_askForCallBackFunc_EB.emit()

        # 初始化选择框默认文本
        self.GUI_cb_offset1_setDefaultText_UI.emit()
        self.GUI_cb_offset2_setDefaultText_UI.emit()

    # 我才知道Python3.10以下不能写成"callBackFunc: [[], None] | None"......
    def start(self) -> None:
        """
        启动UI界面
        """
        
        try:
            sys.exit(self.app.exec_())
        except SystemExit:
            if hasattr(self, "callBackFunc"):
                if self.callBackFunc is not None:
                # 调用用户自定义的回调函数
                    self.callBackFunc()
