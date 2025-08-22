# file: logic.py
# brief: 逻辑处理模块
# time: 2025.8.19
# version: 0.1.0-Beta-1
# TODOs:
#   暂无

from PyQt5.QtCore import pyqtSignal, QThread
from eventbus     import EventBus
from loguru       import logger
import time


class Logic(QThread):
    """
    逻辑处理类
    """

    eventBus: EventBus
    startFirstTime: bool = False
    showMainWindow: bool = False

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

    LG_getShowMainWindow_ST:   pyqtSignal = pyqtSignal()
    
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
        def f1(pathToCI: str): self.pathToCI = pathToCI
        self.eventBus.ST_returnPathToCI_LG.connect(lambda pathToCI: f1(pathToCI))

        self.LG_getShowMainWindow_ST.connect(self.eventBus.LG_getShowMainWindow_ST)

        def f2(showMainWindow: bool): self.showMainWindow = showMainWindow
        self.eventBus.ST_returnShowMainWindow_LG.connect(lambda showMainWindow: f2(showMainWindow))

    def workMain(self) -> None:
        """
        主逻辑处理函数
        """

        if self.showMainWindow == True or self.startFirstTime == True:
            self.LG_showMainWindow_GUI.emit()

        else:
            # 静默生成课表
            logger.info("开始静默生成并写入今日课表")

            self.LG_getPathToCI_ST.emit()

            self.LG_getClassTableToday_CT.emit()
            self.LG_generateOverAllDict_JM.emit()

            time.sleep(0.2)

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

        time.sleep(0.2)                                                   # 睡0.2秒, 等GUI初始化 (才不是我懒得写事件循环和信号呢(
        self.LG_getShowMainWindow_ST.emit()
        time.sleep(0.1)
        self.workMain()
        