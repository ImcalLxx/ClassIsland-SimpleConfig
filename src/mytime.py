# file: mytime.py
# brief: 时间计算模块
# time: 2025.8.25
# TODOs:
#   暂无

from PyQt5.QtCore import QMutex, QMutexLocker, QThread
import datetime
from loguru       import logger
import orjson, json, time, math, os


class MyTime(QThread):
    """
    时间类, 计算周数, 偏移等
    """

    mutex: QMutex                                                       # 线程锁

    weekOffset1: int = 0                                                # 单双周偏移量
    weekOffset2: int = 0                                                # 3周课表轮换偏移

    weekCount1: int = 0                                                 # 修正后的单双周数(0=单周, 1=双周)
    weekCount2: int = 0                                                 # 修正后的单双周数

    curDateTime: datetime.datetime

    def __init__(self) -> None:
        super().__init__()
        self.mutex = QMutex()

        if not os.path.exists("./data/time.json"):
            logger.info("时间偏移量文件缺失, 现在创建")
            self.saveTimeOffset()

        self.loadTimeOffset()

        _wof1, _wof2 = self.__calcWeekCount()
        self.weekCount1 = (_wof1 + self.weekOffset1) % 2
        self.weekCount2 = (_wof2 + self.weekOffset2) % 3

        self.curDateTime = datetime.datetime.now()

        self.start()

    def saveTimeOffset(self) -> None:
        """
        保存时间偏移量等数据
        """

        logger.info("开始保存时间偏移量到路径 './data/time.json'")

        with open("./data/time.json", "wb") as timeOffSetFile:
            data = {
                "weekOffset1": self.weekOffset1,
                "weekOffset2": self.weekOffset2
            }

            timeOffSetFile.write(orjson.dumps(data))

        logger.success("保存时间偏移量成功")

    def loadTimeOffset(self) -> None:
        """
        加载时间偏移量数据
        """

        logger.info("开始从路径 './data/time.json' 读取时间偏移量数据")

        try:
            with open("./data/time.json", "r") as timeOffsetFile:
                data: dict = json.load(timeOffsetFile)
        except FileNotFoundError:
            logger.error("读取时间偏移量时路径 './data/time.json' 不存在")
            return

        self.weekOffset1 = data["weekOffset1"]
        self.weekOffset2 = data["weekOffset2"]

        logger.success("读取时间偏移量数据完成")

    def getWeekCount1(self) -> int:
        """
        获取单双周偏移量

        Returns:
            int: 单双周偏移量(修正值, 范围为[0, 1])
        """

        _wof1, _wof2 = self.__calcWeekCount()

        with QMutexLocker(self.mutex):                                  # 加锁
            self.weekCount1 = (_wof1 + self.weekOffset1) % 2
            return self.weekCount1
        
    def getWeekCount2(self) -> int:
        """
        获取三周课表偏移量

        Returns:
            int: 三周课表偏移量
        """

        _wof1, _wof2 = self.__calcWeekCount()

        with QMutexLocker(self.mutex):
            self.weekCount2 = (_wof2 + self.weekOffset2) % 3
            return self.weekCount2
        
    def __calcWeekCount(self) -> tuple[int, int]:
        """
        计算理论上(注意!!!理论上)的单双周和三周周数, 若要获取修正量请不要调用此函数!

        Returns:
              tuple[int, int]: 单双周周数, 三周周数
        """

        time_20250707: int = 1751817600                                 # 以2025/07/07 00:00:00为时间基准(此时为单周)
        timenow: int  = int(time.time())                                # 当前的时间戳
        secdiff: int = timenow - time_20250707

        SEC_PER_DAY: int = 86400
        daydiff  = math.floor(secdiff / SEC_PER_DAY)                     # 差的天数
        weekdiff = math.floor(daydiff / 7)

        return (weekdiff % 2, weekdiff % 3)
        
    def setWeekOffset1(self, val: int) -> None:
        """
        设置单双周偏移量

        Args:
            val (int): 新的单双周偏移量
        """

        _wof1, _wof2 = self.__calcWeekCount()

        with QMutexLocker(self.mutex):
            self.weekCount1 = (_wof1 + self.weekOffset1) % 2
            self.weekOffset1 = val % 2
            logger.debug(f"MyTime.setWeekOffset1 called! weekCount1: {self.weekCount1}, weekOffset1: {self.weekOffset1}")

    def setWeekOffset2(self, val: int) -> None:
        """
        设置三周轮换偏移量

        Args:
            val (int): 新的三周轮换偏移量
        """

        _wof1, _wof2 = self.__calcWeekCount()

        with QMutexLocker(self.mutex):
            self.weekCount2 = (_wof2 + self.weekOffset2) % 3
            self.weekOffset2 = val % 3

        logger.debug(f"MyTime.setWeekOffset2 called! weekCount2: {self.weekCount2}, weekOffset2: {self.weekOffset2}")

    def run(self) -> None:

        while True:
            _wof1, _wof2 = self.__calcWeekCount()
            self.weekCount1 = (_wof1 + self.weekOffset1) % 2
            self.weekCount2 = (_wof2 + self.weekOffset2) % 3
            self.curDateTime = datetime.datetime.now()

            time.sleep(300)