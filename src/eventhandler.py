# file: eventhandler.py
# brief: 事件处理模块
# time: 2025.8.18
# version: 0.1.0-Alpha-3
# TODOs:
#   暂无

from PyQt5.QtCore    import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QWidget
from tkinter         import filedialog   
from eventbus        import EventBus
from loguru          import logger
from typing          import NoReturn
import sys


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

    EH_setWeekOffset1_MT: pyqtSignal = pyqtSignal()
    EH_setWeekOffset2_MT: pyqtSignal = pyqtSignal()

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
        self.EH_setWeekOffset1_MT.connect(self.eventBus.EH_setWeekOffset1_MT)

        self.eventBus.UI_cb_offset2_currentIndexChanged_EH.connect(self.cb_offset2_CurrentIndexChanged)
        self.EH_setWeekOffset2_MT.connect(self.eventBus.EH_setWeekOffset2_MT)

        self.eventBus.UI_cb_ctinfo_currentIndexChanged_EH.connect(self.cb_ctinfo_CurrentIndexChanged)
        self.EH_displaySAInfo_GUI.connect(self.eventBus.EH_displaySAInfo_GUI)

        self.eventBus.ST_askForPathToCI_EH.connect(self.askForPathToCI)
        self.EH_returnPathToCI_ST.connect(self.eventBus.EH_returnPathToCI_ST)

        self.eventBus.STUI_b_pathToCI_clicked_EH.connect(self.stui_b_pathToCI_OnClick)

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

        self.EH_setWeekOffset1_MT.emit()

    def cb_offset2_CurrentIndexChanged(self) -> None:
        """
        Offset2(三周课表偏移)选择框被触发
        """

        self.EH_setWeekOffset2_MT.emit()

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

    def stui_b_pathToCI_OnClick(self) -> None:
        """
        设置UI pathToCI按钮按处理函数
        """

        pathToCI = filedialog.askopenfilename(title="请选择ClassIsland可执行文件路径", filetypes=((("可执行文件","*.exe"),)),
                                                initialfile="ClassIsland.exe", initialdir=".")
        if pathToCI == "":
            logger.warning("选择ClassIsland可执行文件路径时失败, 可能为用户取消")
            return
        self.EH_returnPathToCI_ST.emit(pathToCI)                        # 借用上方信号回传文件路径
