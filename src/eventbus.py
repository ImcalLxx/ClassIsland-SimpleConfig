# file: eventbus.py
# brief: 事件总线模块
# time: 2025.8.6
# version: 0.1.0-Alpha-1
# TODOs:
#   暂无

from PyQt5.QtCore    import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication
from ciconfig_ui     import Ui_MainWindow
from class_manager   import ClassTable, TimeTable
from json_writer     import JsonManager
from typing          import NoReturn
from loguru          import logger
import sys


class EventBus(QObject):
    """
    事件总线
    """

    ui: Ui_MainWindow       # ui类, 绑定控件信号
    classTable:  ClassTable
    timeTable:   TimeTable
    jsonManager: JsonManager
    app: QApplication

    def __init__(self, app: QApplication, ui: Ui_MainWindow, classTable: ClassTable, timeTable: TimeTable, jsonManager: JsonManager,
                 parent = None) -> None:
        super().__init__(parent)

        self.ui = ui
        self.classTable  = classTable
        self.timeTable   = timeTable
        self.jsonManager = jsonManager
        self.app = app

    def onExit(self) -> None:
        """
        程序退出前执行的代码
        """

        self.classTable.saveClassTable()
        self.timeTable.saveTimeTable()
        self.EB_saveSettings_ST.emit()

        logger.info("程序退出")

        return

    def quit(self) -> NoReturn:
        """
        退出程序
        """

        try:
            sys.exit()
        except SystemExit:
            self.onExit()
        finally:
            sys.exit()

    # 以下为所有信号的声明, 命名规范为: 发出者类简写(全大写)_信号内容_接收者类(槽函数所在类)简写(全大写)
    # 例: UI_showMainWindow_GUI: pyqtSingal = pyqtSingal() ...
    # 发出者不确定或为EventBus时可省略(话说EventBus为什么会主动发出信号)
    UI_b_import_ct_clicked_EH: pyqtSignal = pyqtSignal()
    EH_parseClassTable_CT:     pyqtSignal = pyqtSignal(str, str)

    UI_b_import_tt_clicked_EH: pyqtSignal = pyqtSignal()
    EH_parseTimeTable_TT:      pyqtSignal = pyqtSignal(str, str)

    UI_b_export_ct_clicked_EH: pyqtSignal = pyqtSignal()
    EH_writeClassTable_CT:     pyqtSignal = pyqtSignal(str, str)

    UI_b_export_tt_clicked_EH: pyqtSignal = pyqtSignal()
    EH_writeTimeTable_TT:      pyqtSignal = pyqtSignal(str, str)

    UI_b_generate_json_clicked_EH: pyqtSignal = pyqtSignal()
    EH_getClassTableToday_CT:      pyqtSignal = pyqtSignal()
    EH_generateOverAllDict_JM:     pyqtSignal = pyqtSignal()
    EH_writeJsonFile_JM:           pyqtSignal = pyqtSignal(str)

    UI_b_exit_clicked_EH: pyqtSignal = pyqtSignal()
    EH_exit_Main:         pyqtSignal = pyqtSignal()

    UI_cb_offset1_currentIndexChanged_EH: pyqtSignal = pyqtSignal()
    EH_setWeekOffset1_TT:                 pyqtSignal = pyqtSignal()

    UI_cb_offset2_currentIndexChanged_EH: pyqtSignal = pyqtSignal()
    EH_setWeekOffset2_TT:                 pyqtSignal = pyqtSignal()

    UI_cb_ctinfo_currentIndexChanged_EH: pyqtSignal = pyqtSignal()
    EH_displaySAInfo_GUI:                pyqtSignal = pyqtSignal()
    EB_displaySAInfo_GUI:                pyqtSignal = pyqtSignal(object)
    GUI_setSAWidget:                     pyqtSignal = pyqtSignal(object)

    GUI_askForCallBackFunc_EB: pyqtSignal = pyqtSignal()
    EB_returnCallBackFunc_GUI: pyqtSignal = pyqtSignal(object)

    GUI_cb_offset1_setDefaultText_UI: pyqtSignal = pyqtSignal()
    GUI_cb_offset2_setDefaultText_UI: pyqtSignal = pyqtSignal()

    GUI_exit_Main: pyqtSignal = pyqtSignal()

    LG_showMainWindow_GUI: pyqtSignal = pyqtSignal()
    EB_showMainWindow_GUI: pyqtSignal = pyqtSignal(object)              # 此处object给Gui.SA_DisplayInfo传参

    LG_getClassTableToday_CT:  pyqtSignal = pyqtSignal()
    LG_generateOverAllDict_JM: pyqtSignal = pyqtSignal()
    LG_writeJsonFile_JM:       pyqtSignal = pyqtSignal()

    LG_displaySAInfo_GUI: pyqtSignal = pyqtSignal()

    ST_askForPathToCI_EH: pyqtSignal = pyqtSignal()
    EH_returnPathToCI_ST: pyqtSignal = pyqtSignal(str)
    
    EB_saveSettings_ST: pyqtSignal = pyqtSignal()
    
    def connectAllSingal(self) -> None:
        """
        连接信号
        """

        self.ui.b_import_ct.clicked.connect(self.UI_b_import_ct_clicked_EH)
        self.EH_parseClassTable_CT.connect(lambda filePath, mode: self.classTable.parseClassTable(filePath, mode))

        self.ui.b_import_tt.clicked.connect(self.UI_b_import_tt_clicked_EH)
        self.EH_parseTimeTable_TT.connect(lambda filePath, mode: self.timeTable.parseTimeTable(filePath, mode))

        self.ui.b_export_ct.clicked.connect(self.UI_b_export_ct_clicked_EH)
        self.EH_writeClassTable_CT.connect(lambda filePath, mode: self.classTable.writeClassTable(filePath, mode))

        self.ui.b_export_tt.clicked.connect(self.UI_b_export_tt_clicked_EH)
        self.EH_writeTimeTable_TT.connect(lambda filePath, mode: self.timeTable.writeTimeTable(filePath, mode))

        self.ui.b_generate_json.clicked.connect(self.UI_b_generate_json_clicked_EH)
        self.EH_getClassTableToday_CT.connect(lambda: self.classTable.getClassTableToday(self.timeTable))
        self.EH_generateOverAllDict_JM.connect(lambda: self.jsonManager.generateOverAllDict(self.classTable, self.timeTable))
        self.EH_writeJsonFile_JM.connect(lambda outPath: self.jsonManager.writeJsonFile(outPath))

        self.ui.b_exit.clicked.connect(self.UI_b_exit_clicked_EH)
        self.EH_exit_Main.connect(self.quit)

        self.ui.cb_offset1.currentIndexChanged.connect(self.UI_cb_offset1_currentIndexChanged_EH)
        self.EH_setWeekOffset1_TT.connect(lambda: self.timeTable.setWeekOffset1(self.ui.cb_offset1.currentIndex()))

        self.ui.cb_offset2.currentIndexChanged.connect(self.UI_cb_offset2_currentIndexChanged_EH)
        self.EH_setWeekOffset2_TT.connect(lambda: self.timeTable.setWeekOffset2(self.ui.cb_offset2.currentIndex()))

        self.ui.cb_ctinfo.currentIndexChanged.connect(self.UI_cb_ctinfo_currentIndexChanged_EH)
        def f1() -> None:
            if self.ui.cb_ctinfo.currentIndex() == 0:
                self.EB_displaySAInfo_GUI.emit(self.classTable)
            else:
                self.EB_displaySAInfo_GUI.emit(self.timeTable)
        # 此处信号传递: EH_displaySAInfo(EventHandler) -> EH_displaySAInfo_GUI(EventBus) -> EB_displaySAInfo_GUI(由GUI接受)
        self.EH_displaySAInfo_GUI.connect(f1)
        self.GUI_setSAWidget.connect(lambda contentWidget: self.ui.sa_ctinfo.setWidget(contentWidget))

        self.GUI_askForCallBackFunc_EB.connect(lambda: self.EB_returnCallBackFunc_GUI.emit(self.quit))

        self.GUI_exit_Main.connect(self.quit)

        self.GUI_cb_offset1_setDefaultText_UI.connect(lambda: self.ui.cb_offset1.setCurrentIndex(self.timeTable.weekOffset1))
        self.GUI_cb_offset2_setDefaultText_UI.connect(lambda: self.ui.cb_offset2.setCurrentIndex(self.timeTable.weekOffset2))

        def f2() -> None:   # 给Gui.SA_DisplayInfo传参
            if self.ui.cb_ctinfo.currentIndex() == 0:
                self.EB_showMainWindow_GUI.emit(self.classTable)
            else:
                self.EB_showMainWindow_GUI.emit(self.timeTable)
        self.LG_showMainWindow_GUI.connect(f2)

        self.LG_getClassTableToday_CT.connect(lambda: self.classTable.getClassTableToday(self.timeTable))
        self.LG_generateOverAllDict_JM.connect(lambda: self.jsonManager.generateOverAllDict(self.classTable, self.timeTable))
        self.LG_writeJsonFile_JM.connect(self.jsonManager.writeJsonFile)

        self.LG_displaySAInfo_GUI.connect(lambda: self.EB_displaySAInfo_GUI.emit(self.classTable))