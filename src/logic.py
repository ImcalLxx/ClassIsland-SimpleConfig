# file: logic.py
# brief: 逻辑处理模块
# time: 2025.8.6
# version: 0.1.0-Alpha-1
# TODOs:
#   暂无

from PyQt5.QtCore import pyqtSignal, QThread, QObject
from eventbus     import EventBus
from typing       import Any
from loguru       import logger
import time, orjson, json, os

class Settings(QObject):
    """
    设置类
    """

    loadPriority: int = 0                                               # 加载优先级, 0=优先本程序, 1=优先ClassIsland
    pathToCI: str = ""                                                  # ClassIsland可执行文件路径
    eventBus: EventBus

    def __init__(self, eventBus: EventBus, parent = None) -> None:
        super().__init__(parent)
        self.eventBus = eventBus

    # 以下为事件处理的信号
    # 需要与其他类通信的通过EventBus中继
    ST_askForPathToCI_EH: pyqtSignal = pyqtSignal()

    ST_returnPathToCI_LG: pyqtSignal = pyqtSignal(str)

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

    def saveSettings(self) -> None:
        """
        保存设置选项
        """

        logger.info("开始保存设置文件到路径 './data/settings.json'")

        data = {
            "loadPriority": self.loadPriority,
            "pathToCI": self.pathToCI
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


class Logic(QThread):
    """
    逻辑处理类
    """

    eventBus: EventBus
    startFirstTime: bool = False

    pathToCI: str = ""

    def __init__(self, eventBus: EventBus, parent = None) -> None:
        super().__init__(parent)
        self.eventBus = eventBus

    # 以下为事件处理的信号
    # 需要与其他类通信的通过EventBus中继
    LG_showMainWindow_GUI: pyqtSignal = pyqtSignal()

    LG_getClassTableToday_CT:  pyqtSignal = pyqtSignal()
    LG_generateOverAllDict_JM: pyqtSignal = pyqtSignal()
    LG_writeJsonFile_JM:       pyqtSignal = pyqtSignal(str)

    LG_displaySAInfo_GUI:      pyqtSignal = pyqtSignal()

    LG_getPathToCI_ST:         pyqtSignal = pyqtSignal()
    
    def connectAllSingal(self) -> None:
        """
        绑定所有信号
        """
        
        self.LG_showMainWindow_GUI.connect(self.eventBus.LG_showMainWindow_GUI)

        self.LG_getClassTableToday_CT.connect(self.eventBus.LG_getClassTableToday_CT)
        self.LG_generateOverAllDict_JM.connect(self.eventBus.LG_generateOverAllDict_JM)
        self.LG_writeJsonFile_JM.connect(self.eventBus.LG_writeJsonFile_JM)

        self.LG_displaySAInfo_GUI.connect(self.eventBus.LG_displaySAInfo_GUI)

        self.LG_getPathToCI_ST.connect(self.eventBus.LG_getPathToCI_ST)
        def f1(self: Logic, pathToCI: str):
            self.pathToCI = pathToCI
        self.eventBus.ST_returnPathToCI_LG.connect(lambda pathToCI: f1(self, pathToCI))

    def workMain(self) -> None:
        """
        主逻辑处理函数
        """

        # 如果第一次启动
        if self.startFirstTime == True:
            self.LG_showMainWindow_GUI.emit()                           # 发送弹窗信号
            self.LG_displaySAInfo_GUI.emit()

        else:
            # 静默生成课表
            logger.info("开始静默生成并写入今日课表")

            self.LG_getPathToCI_ST.emit()

            self.LG_getClassTableToday_CT.emit()
            self.LG_generateOverAllDict_JM.emit()

            if self.pathToCI != "":
                outPath: str = self.pathToCI[:-15]
                outPath += "Profiles/Default.json"
            else:
                outPath = "./output/Default.json"

            self.LG_writeJsonFile_JM.emit(outPath)

        # TODO: 改用QEventLoop
        while True:                                                     # 主事件处理
            start = time.perf_counter()

            # ---事件处理写在下面---


            # ----事件处理结束----

            finish = time.perf_counter()
            timeElasped = finish - start
            if timeElasped < 0.0167:
                time.sleep(0.0167 - timeElasped)                        # 计算休眠时间, 保持每秒60次刷新


    def run(self) -> None:
        """
        重写run方法
        """

        time.sleep(1)                                                   # 睡1秒, 等GUI初始化 (才不是我懒得写事件循环和信号呢(
        self.workMain()
        