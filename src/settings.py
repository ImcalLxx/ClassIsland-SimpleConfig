# file: settings.py
# brief: 设置模块
# time: 2025.8.19
# version: 0.1.0-Beta-1
# TODOs:
#   1. 检查设置文件完整性并补全

from PyQt5.QtCore    import QObject, pyqtSignal
from PyQt5.QtWidgets import QMainWindow
from eventbus        import EventBus
from typing          import Any
from loguru          import logger
import orjson, json, os

class Settings(QObject):
    """
    设置类
    """

    loadPriority: int = 0                                               # 加载优先级, 0=优先本程序, 1=优先ClassIsland
    pathToCI: str = ""                                                  # ClassIsland可执行文件路径
    showMainWindow: bool = False                                        # 启动时显示主界面
    eventBus: EventBus

    mainWindow: QMainWindow

    def __init__(self, settingsWindow: QMainWindow, eventBus: EventBus, parent = None) -> None:
        super().__init__(parent)
        self.eventBus = eventBus
        self.mainWindow = settingsWindow

    # 以下为事件处理的信号
    # 需要与其他类通信的通过EventBus中继
    ST_askForPathToCI_EH: pyqtSignal = pyqtSignal()

    ST_returnPathToCI_LG: pyqtSignal = pyqtSignal(str)

    ST_setComboBoxDefaultText_STUI: pyqtSignal = pyqtSignal(dict)

    ST_returnShowMainWindow_LG    : pyqtSignal = pyqtSignal(bool)

    def connectAllSingal(self) -> None:
        """
        连接所有信号
        """

        self.ST_askForPathToCI_EH.connect(self.eventBus.ST_askForPathToCI_EH)

        def f1(self: Settings, pathToCI: str): self.pathToCI = pathToCI
        self.eventBus.EH_returnPathToCI_ST.connect(lambda pathToCI: f1(self, pathToCI)) 

        self.eventBus.EB_saveSettings_ST.connect(self.saveSettings)

        self.ST_returnPathToCI_LG.connect(self.eventBus.ST_returnPathToCI_LG)
        self.eventBus.LG_getPathToCI_ST.connect(lambda: self.ST_returnPathToCI_LG.emit(self.pathToCI))

        self.ST_setComboBoxDefaultText_STUI.connect(self.eventBus.ST_setComboBoxDefaultText_STUI)
        def f2() -> None:
            # 设置选择框默认文本
            data: dict = {
                "pathToCI": self.pathToCI,
                "showMainWindow": self.showMainWindow
            }
            self.ST_setComboBoxDefaultText_STUI.emit(data)
            self.mainWindow.show()
        self.eventBus.UI_b_settings_clicked_ST.connect(f2)

        def f3(showMainWindow: bool): self.showMainWindow = showMainWindow
        self.eventBus.STUI_set_showMainWindow_ST.connect(lambda showMainWindow: f3(showMainWindow))

        self.eventBus.LG_getShowMainWindow_ST.connect(lambda: self.ST_returnShowMainWindow_LG.emit(self.showMainWindow))
        self.ST_returnShowMainWindow_LG.connect(self.eventBus.ST_returnShowMainWindow_LG)

    def saveSettings(self) -> None:
        """
        保存设置选项
        """

        logger.info("开始保存设置文件到路径 './data/settings.json'")

        data = {
            "loadPriority": self.loadPriority,
            "pathToCI": self.pathToCI,
            "showMainWindow": self.showMainWindow
        }

        with open("./data/settings.json", "wb") as settingsFile:
            settingsFile.write(orjson.dumps(data))

        logger.success("保存设置文件成功")

    def loadSettings(self) -> None:
        """
        加载设置选项
        """

        logger.info("开始从路径 './data/settings.json' 读取设置文件")

        try:
            with open("./data/settings.json", "r") as settingsFile:
                data: dict[str, Any] = json.load(settingsFile)
        except FileNotFoundError:
            logger.error("读取设置文件时路径 './data/settings.json' 不存在")
            return
        
        # TODO: 加入未找到键的报错处理
        self.loadPriority = data["loadPriority"]
        self.pathToCI = data["pathToCI"]
        self.showMainWindow = data["showMainWindow"]

    def init(self) -> None:
        """
        初始化, 检查设置文件完整性
        """

        if not os.path.exists("./data/settings.json"):
            logger.warning("设置文件缺失, 重新创建")
            self.saveSettings()
        
        self.loadSettings()

        if self.pathToCI == "":
            logger.warning("ClassIsland可执行文件路径为空, 现在询问用户")
            self.ST_askForPathToCI_EH.emit()

