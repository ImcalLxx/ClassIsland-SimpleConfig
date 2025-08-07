# file: gui.py
# brief: UI模块
# time: 2025.8.6
# version: 0.1.0-Alpha-1
# TODOs:
#   1. UI基本框架
#   2. 其他功能进一步跟进(见demo.py)
#   3. 写一个task, 在用pyuic转换ui文件时纠错(这个不着急)

from PyQt5           import QtWidgets
from PyQt5.QtCore    import Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import (QSystemTrayIcon, QMenu, QApplication, QMainWindow, QWidget, QApplication, QVBoxLayout, 
                             QLabel, QComboBox, QHBoxLayout, QMessageBox)
from PyQt5.QtGui     import QIcon, QFont
from tkinter         import filedialog              # 用来选择文件的, 我懒得用PyQt了(
from class_manager   import ClassTable, TimeTable
from json_writer     import ALL_CLASSES, time2str_hm
from eventbus        import EventBus
from typing          import Callable, Optional, NoReturn, Union
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
    def loadGlobalQss(qssFilePath: str = "./res/ciconfig_ui.qss") -> str:
        """
        读取PyQt的qss文件

        Args:
            qssFilePath (str, optional): qss文件路径

        Returns:
            str: 读取到的qss文件
        """

        with open(qssFilePath, 'r', encoding='UTF-8') as file:
            return file.read()

class EventHandler(QObject):
    """
    事件处理类
    """

    eventBus: EventBus

    def __init__(self, eventBus: EventBus, parent = None) -> None:
        super().__init__(parent)
        self.eventBus = eventBus


    # 以下为事件处理的信号
    # 需要与其他类通信的通过EventBus中继
    # 此处的信号连接顺序: (EventHandler)self.EH_sigXXX_XXX.connect(self.eventBus.EH_sigXXX_XXX)
    #                      (EventBus)self.EH_sigXXX_XXX.connect(self.XXX.doSomething)
    EH_parseClassTable_CT: pyqtSignal = pyqtSignal(str, str)
    EH_parseTimeTable_TT:  pyqtSignal = pyqtSignal(str, str)

    EH_writeClassTable_CT: pyqtSignal = pyqtSignal(str, str)
    EH_writeTimeTable_TT:  pyqtSignal = pyqtSignal(str, str)

    EH_getClassTableToday_CT:  pyqtSignal = pyqtSignal()
    EH_generateOverAllDict_JM: pyqtSignal = pyqtSignal()
    EH_writeJsonFile_JM:       pyqtSignal = pyqtSignal(str)

    EH_exit_Main:         pyqtSignal = pyqtSignal()

    EH_setWeekOffset1_TT: pyqtSignal = pyqtSignal()
    EH_setWeekOffset2_TT: pyqtSignal = pyqtSignal()

    EH_displaySAInfo_GUI: pyqtSignal = pyqtSignal()

    EH_returnPathToCI_ST: pyqtSignal = pyqtSignal(str)

    # 绑定EventBus中接收者为EventHandler(需要本类处理的信号)/绑定本类发出的信号
    def connectAllSingal(self):
        """
        绑定所有信号
        """

        self.eventBus.UI_b_import_ct_clicked_EH.connect(self.b_import_ct_Onclick)
        self.EH_parseClassTable_CT.connect(self.eventBus.EH_parseClassTable_CT)

        self.eventBus.UI_b_import_tt_clicked_EH.connect(self.b_import_tt_OnClick)
        self.EH_parseTimeTable_TT.connect(self.eventBus.EH_parseTimeTable_TT)

        self.eventBus.UI_b_export_ct_clicked_EH.connect(self.b_export_ct_OnClick)
        self.EH_writeClassTable_CT.connect(self.eventBus.EH_writeClassTable_CT)

        self.eventBus.UI_b_export_tt_clicked_EH.connect(self.b_export_tt_OnClick)
        self.EH_writeTimeTable_TT.connect(self.eventBus.EH_writeTimeTable_TT)

        self.eventBus.UI_b_generate_json_clicked_EH.connect(self.b_generate_json_OnClick)
        self.EH_getClassTableToday_CT.connect(self.eventBus.EH_getClassTableToday_CT)
        self.EH_generateOverAllDict_JM.connect(self.eventBus.EH_generateOverAllDict_JM)
        self.EH_writeJsonFile_JM.connect(self.eventBus.EH_writeJsonFile_JM)

        self.eventBus.UI_b_exit_clicked_EH.connect(self.b_exit_OnClick)
        self.EH_exit_Main.connect(self.eventBus.EH_exit_Main)

        self.eventBus.UI_cb_offset1_currentIndexChanged_EH.connect(self.cb_offset1_CurrentIndexChanged)
        self.EH_setWeekOffset1_TT.connect(self.eventBus.EH_setWeekOffset1_TT)

        self.eventBus.UI_cb_offset2_currentIndexChanged_EH.connect(self.cb_offset2_CurrentIndexChanged)
        self.EH_setWeekOffset2_TT.connect(self.eventBus.EH_setWeekOffset2_TT)

        self.eventBus.UI_cb_ctinfo_currentIndexChanged_EH.connect(self.cb_ctinfo_CurrentIndexChanged)
        self.EH_displaySAInfo_GUI.connect(self.eventBus.EH_displaySAInfo_GUI)

        self.eventBus.ST_askForPathToCI_EH.connect(self.askForPathToCI)
        self.EH_returnPathToCI_ST.connect(self.eventBus.EH_returnPathToCI_ST)

    # 信号处理槽函数, 命名规范为: 控件名_操作(大驼峰)/信号名_操作(大驼峰)
    def b_import_ct_Onclick(self):
        """
        按钮b_import_ct被按下的处理函数
        """

        # 通过对话框获取文件地址并解析文件
        filePath = filedialog.askopenfilename(title="选择课表文件", filetypes=((("文本文件","*.txt"),("Excel表格","*.xlsx"))))
        if filePath == "":
            logger.warning("选择课表路径时失败, 可能为用户取消")
            return
        mode: str = filePath[-4:]
        self.EH_parseClassTable_CT.emit(filePath, mode)                 # 通过pyqt信号调用classTable中的parseClassTable

    def b_export_ct_OnClick(self) -> None:
        """
        按钮b_export_ct被按下的处理函数
        """

        filePath = filedialog.asksaveasfilename(title="选择导出路径", filetypes=((("文本文件","*.txt"),("Excel表格","*.xlsx"))))
        if filePath == "":
            logger.warning("选择课表导出路径时失败, 可能为用户取消")
            return
        mode: str = filePath[-4:]
        if ".txt" not in mode and "xlsx" not in mode and ".xls" not in mode:
            # TODO: 提示选择模式, 为了方便, 暂时默认txt
            mode = "txt"
        if "." not in mode:                                             # 没后缀名
            filePath += ".txt"
        else:
            # TODO: 懒得处理
            pass
        self.EH_writeClassTable_CT.emit(filePath, mode)

    def b_export_tt_OnClick(self) -> None:
        """
        按钮b_export_tt被按下的处理函数
        """

        filePath = filedialog.asksaveasfilename(title="选择导出路径", filetypes=((("文本文件","*.txt"),("Excel表格","*.xlsx"))))
        if filePath == "":
            logger.warning("选择时间表导出路径时失败, 可能为用户取消")
            return
        mode: str = filePath[-4:]
        if ".txt" not in mode and "xlsx" not in mode and ".xls" not in mode:
            # TODO: 提示选择模式, 为了方便, 暂时默认txt
            mode = "txt"
            filePath += ".txt"
        self.EH_writeTimeTable_TT.emit(filePath, mode)

    def b_import_tt_OnClick(self) -> None:
        """
        按钮b_import_tt被按下的处理函数
        """

        filePath = filedialog.askopenfilename(title="选择时间表文件", filetypes=((("文本文件","*.txt"),("Excel表格","*.xlsx"))))
        if filePath == "":
            logger.warning("选择时间表路径时失败, 可能为用户取消")
            return
        mode: str = filePath[-3:]
        self.EH_parseTimeTable_TT.emit(filePath, mode)

    def b_generate_json_OnClick(self) -> None:
        """
        按钮b_generate_json被按下的处理函数
        """

        self.EH_getClassTableToday_CT.emit()                            # 向ClassTable发送信号生成今日课表
        self.EH_generateOverAllDict_JM.emit()                           # 向JsonManager发送信号生成配置文件

        outPath = filedialog.asksaveasfilename(title="导出Json文件", filetypes=(("Json配置文件", "*.json"), ))
        if outPath == "":
            logger.error("选择课表配置文件输出路径时失败, 可能为用户取消")
            return
        else:
            if outPath[-5:] != ".json":
                outPath += ".json"
        
        self.EH_writeJsonFile_JM.emit(outPath)                          # 向JsonManager发送信号写入Json文件

    def b_exit_OnClick(self) -> NoReturn:
        """
        按钮b_exit被按下的处理函数
        """

        try:
            sys.exit(0)
        except SystemExit:
            # 执行退出回调函数
            self.EH_exit_Main.emit()
        finally:
            sys.exit(0)         # 为了让类型推导知道这是个NoReturn函数, 实际上执行不到这里

    def cb_offset1_CurrentIndexChanged(self) -> None:
        """
        Offset1(单双周偏移)选择框被触发
        """

        self.EH_setWeekOffset1_TT.emit()

    def cb_offset2_CurrentIndexChanged(self) -> None:
        """
        Offset2(三周课表偏移)选择框被触发
        """

        self.EH_setWeekOffset2_TT.emit()

    def cb_ctinfo_CurrentIndexChanged(self) -> None:
        """
        课表/时间表选择框触发函数

        Args:
            ui (Ui_MainWindow): UI实例
            gui (Gui): Gui实例
        """

        self.EH_displaySAInfo_GUI.emit()

    def askForPathToCI(self) -> None:
        """
        弹窗询问ClassIsland可执行文件路径
        """

        widget = QWidget()
        reply = QMessageBox.information(widget, "提示", "请选择ClassIsland可执行文件路径", QMessageBox.Yes | QMessageBox.No, 
                                             QMessageBox.Yes)
        
        if reply == 0x4000:
            pathToCI = filedialog.askopenfilename(title="请选择ClassIsland可执行文件路径", filetypes=((("可执行文件","*.exe"),)),
                                                initialfile="ClassIsland.exe", initialdir=".")
            if pathToCI == "":
                logger.warning("选择ClassIsland可执行文件路径时失败, 可能为用户取消")
                return
            self.EH_returnPathToCI_ST.emit(pathToCI)
        else:
            logger.info("选择ClassIsland可执行文件路径时用户取消")

class Gui(QObject):
    """
    图形UI类
    """

    eventBus: EventBus
    app: QApplication
    window: QMainWindow
    callBackFunc: Callable[[], None]

    # 以下为事件处理的信号
    # 需要与其他类通信的通过EventBus中继
    GUI_askForCallBackFunc_EB: pyqtSignal = pyqtSignal()

    GUI_cb_offset1_setDefaultText_UI: pyqtSignal = pyqtSignal()
    GUI_cb_offset2_setDefaultText_UI: pyqtSignal = pyqtSignal()

    GUI_exit_Main: pyqtSignal = pyqtSignal()

    GUI_setSAWidget_UI: pyqtSignal = pyqtSignal(object)

    def connectAllSingal(self) -> None:
        """
        绑定所有信号
        """

        self.GUI_askForCallBackFunc_EB.connect(self.eventBus.GUI_askForCallBackFunc_EB)
        def fr(f: Callable[[], None]): self.callBackFunc = f
        self.eventBus.EB_returnCallBackFunc_GUI.connect(fr)

        self.eventBus.EB_showMainWindow_GUI.connect(lambda SA_contentToDisp: self.showMainWindow(SA_contentToDisp))
        self.restoreAction.triggered.connect(self.eventBus.LG_showMainWindow_GUI)    # 借一下信号
        self.quitAction.triggered.connect(self.GUI_exit_Main)
        self.GUI_exit_Main.connect(self.eventBus.GUI_exit_Main)

        self.eventBus.EB_displaySAInfo_GUI.connect(lambda contentToDisp: self.SA_DisplayInfo(contentToDisp))

        self.GUI_setSAWidget_UI.connect(self.eventBus.GUI_setSAWidget)

    def createTrayIcon(self):
        """
        创建托盘图标
        """

        # 初始化托盘图标
        self.trayIcon = QSystemTrayIcon(self.window)
        self.trayIcon.setIcon(QIcon("res/used_icons/温迪_1.png"))  # 请确保有合适的图标路径

        # 使用QAction而不是QWidgetAction+QLabel
        self.restoreAction = QtWidgets.QAction(QIcon("res/used_icons/恢复屏幕.png"), "显示主界面 ", self.window)
        self.quitAction = QtWidgets.QAction(QIcon("res/used_icons/退出.png"), "退出", self.window)

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

        # 此处的逻辑如下:
        # 滚动区域可以显示课表或者时间表信息
        # 课表信息的格式为: (QLabel)"周一   第1节课"   (QComboBox)(选择框选课)
        # 时间表的格式为: (QLabel)"平日   第1节课"   (QLabel)"07:30-08:10"
        # 因此课表需要一个QLabel显示文本, 对应text, 时间表需要两个, 对应text和text2
        # 下面的函数是用来添加一行的组件的, 会根据SA_DisplayInfo传入的类型自动判断显示课表/时间表的布局方式
        def dp_AddRow(text: str, text2: Optional[str] = None, comboBoxDefaultText: Optional[str] = None):
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
        # TODO: 用空重构一下吧
        # 还有, VSCode的Python语言解析好像快要被玩坏了呢~
        if isinstance(contentToDisp, ClassTable):                       # 显示课表
            # 遍历今日课表
            curDateTime = datetime.datetime.now()
            dayInWeek: int = curDateTime.weekday()
            text: str = LDAYINWEEK[dayInWeek]
            classIndex: int = 0

            for singleClass in contentToDisp.classTableToday:
                dp_AddRow(text + "   第" + str(classIndex + 1) + "节课", comboBoxDefaultText=singleClass.name)
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
            weekcount = ((daydiff % 2) + contentToDisp.weekOffset1) % 2 # 单双周

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

        self.window.show()
        self.SA_DisplayInfo(contentToDisp)

    def __init__(self, eventBus: EventBus, app: QApplication, window: QMainWindow, parent = None) -> None:
        """
        Gui类初始化
        """
        
        super().__init__(parent)
        self.eventBus = eventBus
        self.app = app
        self.window = window

        # 获取程序退出的回调函数
        self.GUI_askForCallBackFunc_EB.emit()

        # 读取qss
        self.window.setStyleSheet(QssLoader.loadGlobalQss())

        # 初始化UI
        self.createTrayIcon()

        # 初始化选择框默认文本
        self.GUI_cb_offset1_setDefaultText_UI.emit()
        self.GUI_cb_offset2_setDefaultText_UI.emit()

        # 初始化Tkinter
        root = tk.Tk()
        root.withdraw()

    # 我才知道Python3.10以下不能写成"callBackFunc: [[], None] | None"......
    def start(self) -> None:
        """
        启动UI界面
        """

        # 启动时最小化到托盘
        self.window.hide()
        
        try:
            sys.exit(self.app.exec_())
        except SystemExit:
            if hasattr(self, "callBackFunc"):
                if self.callBackFunc is not None:
                # 调用用户自定义的回调函数
                    self.callBackFunc()
