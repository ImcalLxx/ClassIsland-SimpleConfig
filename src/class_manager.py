# file: class_manager.py
# brief: 课表及时间表管理模块
# time: 2025.8.19
# version: 0.1.0-Beta-1
# TODOs:
#   1. parseClassTable, writeClassTable, parseTimetable, writeTimeTable的xlsx模式支持
#   2. TimeTable缺少writeTimeTable
#   3. TimeTable加入特殊标识符区分间操, 午饭, 晚自习等

import pickle   # TODO: 写保存模块, 避免使用pickle
import time, datetime, math, os, orjson, json
from   enum   import IntEnum
from   typing import Literal
from   mytime import MyTime
from   loguru import logger

class SingleClass:
    """
    单节课课表类
    """

    class SpecID(IntEnum):
        extraSelfStudy = 0              # 晚自习/周六最后一节自习
        midBreak       = 1              # 午休
        evenBreak      = 2              # 晚饭休息
        exercise       = 3              # 间操

    name: str
    nameInitial: str
    teacherName: str
    isOutdoor: bool = False
    specID: int = 0                                                     # 特殊标识符

    def __init__(self, name: str, teacherName: str = "", isOutdoor: bool = False) -> None:
        """
        单节课课表初始化

        Args:
            name (str): 课程名称
            teacherName (str, optional): 任课老师姓名. Defaults to "".
            isOutdoor (bool, optional): 是否为户外课程. Defaults to False.
        """

        self.name = name

        # 模糊识别
        if self.name == "英语":
            self.name = "外语"
        if self.name == "信息":
            self.name = "信息技术"

        if name != "":
            self.nameInitial = name[0]
        else:
            self.nameInitial = ""
        self.teacherName = teacherName
        self.isOutdoor = isOutdoor


class TimePeriod:
    """
    表示一段时间的类, 内部存放开始时间和终止时间, 并描述了时间段类型
    """
    
    start:  list[int] = [0, 0]                                  # 开始时间: [时, 分]
    finish: list[int] = [0, 0]                                  # 终止时间: [时, 分]
    timeType: int = 0                                           # 时间段类型, 0=上课, 1=课间, 2=分割线
    
    def __init__(self, start: list[int], finish: list[int], timetype = 0) -> None:
        """
        时间段初始化

        Args:
            start (list[int]): 开始时间
            finish (list[int]): 终止时间
            timetype (int, optional): 时间段类型, 0=上课, 1=课间, 2=分割线. Defaults to 0.
        """

        # 检查输入数据
        if len(start) != 2 or len(finish) != 2:
            logger.error("初始化时间段时遇到无法解析的时间格式")
            return
        if timetype not in [0, 1, 2]:
            logger.error(f"初始化时间段时遇到不支持的时间段类型, 支持的值为0, 1, 2, 但输入值为 {timetype}!")
            return

        self.start  = start
        self.finish = finish
        self.timeType = timetype


class ClassTable:
    """
    课表管理类, 可以从文件读取课表并保存课表
    """

    myTime: MyTime

    classTable1: list[list[SingleClass]] = []                   # 周一到周五课表, 外层下标=周几, 内层下标=第几节课
    classTable2: list[list[SingleClass]] = []                   # 周六课表, 外层下标=第几周, 内层下标=第几节课
    classTable3: list[list[SingleClass]] = [[], [], []]         # 晚课课表, 外层下标=第几周, 内层下标=周几晚课
    classTableToday: list[SingleClass] = []                     # 今天实际应该执行的课表

    def __init__(self, myTime: MyTime):
        self.myTime = myTime

    def modifyDayClass(self, dayInWeek: int, dailyClass: list[SingleClass], allowAppend: bool = True) -> None:
        """
        修改每日课表

        Args:
            day_in_week (int): 修改一周的哪一天的课表(0-6, 0=周一, 以此类推)
            dailyClass (list[SingleClass]): 传入的单日的课表
            allowAppend (bool, optional): 是否允许在周课表列表长度不够时向后添加. Defaults to True.
        """

        if dayInWeek >= len(self.classTable1):
            if not allowAppend:
                return
            else:
                # 长度不够就向后添加空列表
                for _ in range(0, dayInWeek - len(self.classTable1) + 1):
                    self.classTable1.append([])
        
        self.classTable1[dayInWeek] = dailyClass
        return
    
    def modifySingleClass(self, dayInWeek: int, classIndex: int, singleClass: SingleClass, allowAppend: bool = False) -> None:
        """
        修改某一天的某节单课

        Args:
            dayInWeek (int): 要修改的课在周几(0-6, 0=周一, 以此类推)
            classIndex (int): 要修改的课是第几节课(0为第一节)
            singleClass (SingleClass): 传入的单节课课表
            allowAppend (bool, optional): 是否允许在日课表(非周课表)长度不够时向后添加. Defaults to False.
        """
        
        if dayInWeek >= len(self.classTable1):
            return
        
        if classIndex >= len(self.classTable1[dayInWeek]):
            # 逻辑同上, 不够时向后添加空课
            if not allowAppend:
                return
            else:
                for _ in range(0, classIndex - len(self.classTable1[dayInWeek]) + 1):
                    emptyClass: SingleClass = SingleClass(name="")
                    self.classTable1[dayInWeek].append(emptyClass)
        
        self.classTable1[dayInWeek][classIndex] = singleClass
        return
    
    def modifySatDayClass(self, weekCount: int, satClass: list[SingleClass], allowAppend: bool = True) -> None:
        """
        修改周六的日课表

        Args:
            weekCount (int): 修改第几周的周六课表(从0开始)
            satClass (list[SingleClass]): 周六当天的课表
            allowAppend (bool, optional): 是否允许在周六课表列表长度不够时向后添加. Defaults to True.
        """
        
        if weekCount >= len(self.classTable2):
            if not allowAppend:
                return
            else:
                for _ in range(0, weekCount - len(self.classTable2) + 1):
                    self.classTable2.append([])
                    
        self.classTable2[weekCount] = satClass
        return
    
    def modifyEvenClass(self, weekCount: int, weekEvenClass: list[SingleClass], allowAppend: bool = True) -> None:
        """
        修改整周的晚课课表

        Args:
            weekCount (int): 第几周的晚课
            weekEvenClass (list[SingleClass]):一周的晚课
            allowAppend (bool, optional): 是否允许在晚课课表列表长度不够时向后添加. Defaults to True.
        """
        
        if weekCount >= len(self.classTable3):
            if not allowAppend:
                return
            else:
                for _ in range(0, weekCount - len(self.classTable3) + 1):
                    self.classTable3.append([])
                    
        self.classTable3[weekCount] = weekEvenClass
        return
                
    def modifyEvenDayClass(self, weekCount: int, dayInWeek: int, dayEvenClass: SingleClass, allowAppend: bool = False) -> None:
        """
        修改某一周某一天的晚课
        
        Args:
            weekCount (int): 修改的晚课在第几周
            dayInWeek (int): 修改的是周几的晚课
            dayEvenClass (SingleClass): 传入那天的晚课
            allowAppend (bool, optional): 是否允许在一周(内层列表大小)的晚课列表长度不够时向后添加. Defaults to False.
        """
        
        if weekCount >= len(self.classTable3):
            return
        
        if dayInWeek >= len(self.classTable3[weekCount]):
            # 逻辑同上, 不够时向后添加空课
            if not allowAppend:
                return
            else:
                for _ in range(0, dayInWeek - len(self.classTable3[weekCount]) + 1):
                    emptyClass: SingleClass = SingleClass(name="")
                    self.classTable3[weekCount].append(emptyClass)
        
        self.classTable3[weekCount][dayInWeek] = dayEvenClass
        return
    
    def parseClassTable(self, filePath: str = "./classes.txt", mode: str = "txt") -> None:
        """
        读取和解析课表

        Args:
            filePath (str, optional): 课表文件地址. Defaults to "./classes.txt".
            mode (str, optional): 从什么文件读取, 支持txt和xlsx两种模式. Defaults to "txt".
        """

        logger.info(f"开始从路径 '{filePath}' 导入/解析课表")

        if not os.path.exists(filePath):
            logger.error(f"导入/解析课表时路径 '{filePath}' 不存在")
            return

        # txt模式
        if mode.lower() == "txt" or mode.lower() == ".txt":
            with open(filePath, "r", encoding="utf-8") as ctf:          # ctf: ClassTableFile, 存放课表信息的文件, 只读模式
                lines: list[str] = ctf.readlines()
                count: int     = 0                                      # 行号计数
                normCount: int = 0                                      # 平日课表计数
                satCount:  int = 0                                      # 周六课表计数
                evenCount: int = 0                                      # 晚课课表计数

                # 遍历每行内容
                for line in lines:
                    p1 = line.find(":")                                 # 找第一个":"的位置
                    prefix = line[0 : p1]                               # 前导字符串("周五", "晚课1"等)

                    if prefix == "":
                        logger.warning(f"导入/解析课表时课表时遇到了空行, Line Number: {count + 1}")
                        continue

                    # 平日课表
                    if "周六" not in prefix and "晚课" not in prefix:
                        dailyClass: list[SingleClass] = []              # 每天课表(一行就是一天的课)

                        tmp: str = line[p1 + 1 : len(line) - 1]         # 截掉开头无用字符和末尾换行符
                        classes: list[str] = tmp.split(",")             # 按逗号划分
                        # 遍历一行中的每一节课
                        for _class in classes:
                            _class.strip()                              # 去除前导空格
                            singleClass: SingleClass = SingleClass(name=_class, isOutdoor=(True if _class == "体育" else False))
                            dailyClass.append(singleClass)              # 添加到日课表
                        self.modifyDayClass(dayInWeek=normCount, dailyClass=dailyClass)         # 写入每日课表
                        normCount += 1
                        
                    # 周六课表
                    elif "周六" in prefix and "晚课" not in prefix: 
                        satClass: list[SingleClass] = []                # 周六课表
                        
                        tmp: str = line[p1 + 1 : len(line) - 1]         # 截掉开头无用字符
                        classes: list[str] = tmp.split(",")             # 按逗号划分
                        # 遍历一行中的每一节课
                        for _class in classes:
                            _class.strip()                              # 去除前导空格
                            singleClass: SingleClass = SingleClass(name=_class, isOutdoor=False)
                            satClass.append(singleClass)                # 添加到周六课表
                        self.modifySatDayClass(weekCount=(satCount), satClass=satClass)    # 写入周六课表
                        satCount += 1
                        
                    # 11-13行, 读晚课课表
                    elif "周六" not in prefix and "晚课" in prefix:
                        weekEvenClass: list[SingleClass] = []           # 晚课课表(一行是一周的晚课)
                        
                        tmp: str = line[p1 + 1 : len(line) - 1]         # 截掉开头无用字符
                        classes: list[str] = tmp.split(",")             # 按逗号划分
                        # 遍历一行中的每一节课
                        for _class in classes:
                            _class.strip()                              # 去除前导空格
                            singleClass: SingleClass = SingleClass(name=_class, isOutdoor=False)
                            weekEvenClass.append(singleClass)           # 添加到一周的晚课课表
                        self.modifyEvenClass(weekCount=evenCount, weekEvenClass=weekEvenClass)   # 写入晚课课表
                        evenCount += 1

                    else:
                        logger.warning(f"解析课表时解析到格式不正确的行! Line Number: {count + 1}")
                    
                    count += 1
        # xlsx模式
        elif mode.lower() == "xlsx" or mode.lower() == "xls" or mode.lower() == ".xlsx" or mode.lower() == ".xls":
            pass
            # TODO: parseClassTable xlsx模式
        # 都不是
        else:
            logger.error("导入/解析课表时遇到不支持的模式")
            return

        logger.success("导入/解析课表成功")

        return
                
    def writeClassTable(self, outPath: str = "./classes.txt", mode: str = "txt") -> None:
        """
        将(修改过后的)课程数据写入课表文件

        Args:
            outPath (str, optional): 输出文件路径. Defaults to "./classes.txt".
            mode (str, optional): 输出模式, 支持txt和xlsx两种模式. Defaults to "txt".
        """

        logger.info(f"开始输出课表文件到路径 '{outPath}'")

        # txt模式
        if mode.lower() == "txt" or mode.lower() == ".txt":
            tmp: dict = {
                            0 : "周一",
                            1 : "周二",
                            2 : "周三",
                            3 : "周四",
                            4 : "周五",
                            5 : "周六",
                            6 : "周日"
                        }                                               # 后面输出周几用(我为什么不用列表??)
            with open(outPath, 'w+', encoding="utf-8") as ctf:          # 打开文件, 写入覆盖模式 
                # 分别遍历三个课表
                for dayInWeek in range(0, len(self.classTable1)):
                    line: str = ""
                    for classIndex in range(0, len(self.classTable1[dayInWeek])):
                        # 输出开头的周几
                        if classIndex == 0:
                            line += tmp.get(dayInWeek, "") + ":"        # 格式: "周一:"
                        if classIndex != len(self.classTable1[dayInWeek]) - 1:
                            line += self.classTable1[dayInWeek][classIndex].name + ","
                        else:
                            line += self.classTable1[dayInWeek][classIndex].name + "\n"
                            ctf.write(line)                             # 写入文件
                
                ctf.write("\n")                                         # 写入空行分割

                for weekCount in range(0, len(self.classTable2)):
                    line: str = ""
                    for classIndex in range(0, len(self.classTable2[weekCount])):
                        # 输出开头的周几
                        if classIndex == 0:
                            line += "周六" + str(weekCount + 1) + ":"     # 格式: "周六1:"
                        if classIndex != len(self.classTable2[weekCount]) - 1:
                            line += self.classTable2[weekCount][classIndex].name + ","
                        else:
                            line += self.classTable2[weekCount][classIndex].name + "\n"
                            ctf.write(line)                             # 写入文件
                            
                ctf.write("\n")                                         # 写入空行分割

                for weekCount in range(0, len(self.classTable3)):
                    line: str = ""
                    for dayInWeek in range(0, len(self.classTable3[weekCount])):
                        # 输出开头的周几
                        if dayInWeek == 0:
                            line += "晚课" + str(weekCount + 1) + ":"     # 格式: "晚课1:"
                        if dayInWeek != len(self.classTable3[weekCount]) - 1:
                            line += self.classTable3[weekCount][dayInWeek].name + ","
                        else:
                            line += self.classTable3[weekCount][dayInWeek].name + "\n"
                            ctf.write(line)                             # 写入文件
        # xlsx模式
        elif mode.lower() == "xlsx" or mode.lower() == "xls" or mode.lower() == ".xlsx" or mode.lower() == ".xls":
            pass
            # TODO: writeClassTable xlsx模式
        # 都不是
        else:
            logger.error("输出课表时遇到未支持的格式")
            return

        logger.success(f"写入课表成功")

        return

    def saveClassTable(self, outPath: str = "./data/classtable.json") -> None:
        """
        保存课表到json文件

        Args:
            outPath (str, optional): 存放课表数据的路径. Defaults to "./data/classTable.json".
        """

        logger.info(f"开始保存课表到路径 '{outPath}'")

        data = {
            "data":[
                [[self.classTable1[i][j].name for j in range(len(self.classTable1[i]))] for i in range(len(self.classTable1))],
                [[self.classTable2[i][j].name for j in range(len(self.classTable2[i]))] for i in range(len(self.classTable2))],
                [[self.classTable3[i][j].name for j in range(len(self.classTable3[i]))] for i in range(len(self.classTable3))]
            ]
        }

        with open(outPath, "wb") as ct:
            ct.write(orjson.dumps(data))

        logger.success("保存课表完成")
        
        return

    def loadClassTable(self, filePath = "./data/classtable.json") -> None:
        """
        读取课表数据

        Args:
            filePath (str, optional): 存放课表数据的路径. Defaults to "./data/classTable.json".
        """

        logger.info(f"开始从路径 '{filePath}' 读取课表")

        try:
            with open(filePath, "r", encoding="utf-8") as ct:
                data: dict = json.load(ct)
        except FileNotFoundError:
            logger.error(f"加载课表时路径 '{filePath}' 不存在")
            return
        
        l: list[list[list[str]]] = data["data"]

        for i in range(len(l[0])):
            dayClass: list[SingleClass] = []
            for j in range(len(l[0][i])):
                singleClass: SingleClass = SingleClass(l[0][i][j])
                dayClass.append(singleClass)
            self.classTable1.append(dayClass)
        for i in range(len(l[1])):
            satDayClass: list[SingleClass] = []
            for j in range(len(l[1][i])):
                singleClass: SingleClass = SingleClass(l[1][i][j])
                satDayClass.append(singleClass)
            self.modifySatDayClass(i, satDayClass)
        for i in range(len(l[2])):
            for j in range(len(l[2][i])):
                singleClass: SingleClass = SingleClass(l[2][i][j])
                self.modifyEvenDayClass(i, j, singleClass, True)

        logger.success("加载课表完成")

        return
                
    def getClassTableToday(self) -> None:
        """
        获取今天的课表

        Args:
            timeTable (TimeTable): 时间表实例
        """

        time_20250707: int = 1751817600                                 # 以2025/07/07 00:00:00为时间基准(此时为单周)
        timenow: int  = int(time.time())                                # 当前的时间戳
        curDateTime = datetime.datetime.now()
        secdiff: int = timenow - time_20250707

        SEC_PER_DAY: int = 86400
        daydiff = math.ceil(secdiff / SEC_PER_DAY)                      # 差的天数
        
        weekcount = self.myTime.weekCount2                              # 3周轮换

        if curDateTime.weekday() == 6:
            logger.info("今天没有课程, 停止生成今日课表")
            return

        # 计算今日课表
        # 先计算白天课表
        self.classTableToday = []
        success: bool = True                                            # 是否成功生成课表
        if curDateTime.weekday() != 5:                                  # 如果不是周六
            if curDateTime.weekday() >= len(self.classTable1):
                logger.error(f"classTable1 未含有指定课表(索引超界), 请先导入课表")
                success = False
                return
            else:
                self.classTableToday.extend(self.classTable1[curDateTime.weekday()])
            # 计算晚课
            if weekcount >= len(self.classTable3):
                logger.error("classTable3 未含有指定课表(索引超界), 请先导入课表")
                success = False
                return
            else:
                self.classTableToday.append(self.classTable3[weekcount][curDateTime.weekday()])
        else:
            if weekcount >= len(self.classTable2):
                logger.error("classTable2 未含有指定课表(索引超界), 请先导入课表")
                success = False
                return
            else:
                self.classTableToday.extend(self.classTable2[weekcount])
        if success:
            # 加一节自习(平日为二晚, 周六则为下午自习)
            extendClass: SingleClass = SingleClass(name="自习")
            self.classTableToday.append(extendClass)

        if success:
            logger.success("成功生成今日课表")
        else:
            logger.error("生成今日课表时出现问题, 返回空课表")
            self.classTableToday = []

        return
        
    
class TimeTable:
    """
    时间表管理类
    """
    
    normTimeList1: list[TimePeriod] = []                                # 平日(周一-周五)时间表, 单周
    normTimeList2: list[TimePeriod] = []                                # 平日(周一-周五)时间表, 双周
    satTimeList1:  list[TimePeriod] = []                                # 周六时间表, 单周
    satTimeList2:  list[TimePeriod] = []                                # 周六时间表, 双周
    
    def __init__(self) -> None:
        pass

    def hm_str2time(self, time: str) -> list[int]:
        """
        hh:mm格式字符串转时间

        Args:
            time (str): "hh:mm"格式的时间字符串

        Returns:
            list[int]:包含两个元素的列表, 第一位为时, 第二位为分
        """

        if time == "":
            return [0, 0]

        # 第一位非数字就改为0
        if not time[0].isdigit():
            lstr: list = list(time)
            lstr[0] = "0"
            time = "".join(lstr)

        h: str = time[0:2].strip()
        m: str = time[3:5].strip()

        retList: list[int] = [0, 0]

        retList[0] = int(h)
        retList[1] = int(m)

        return retList

    
        """
        设置weekOffset2
        """
        
        self.weekOffset2 = val

    def modifyTimeTable(self, timeTableToMod: str, timePeriodCount: int, timePeriod: TimePeriod, allowAppend = True) -> None:
        """
        修改和添加时间表中的时间段

        Args:
            timeTableToMod (str): 要修改哪个时间表, 可选的值有"NTL1", "NTL2", "STL1", "STL2"(不区分大小写), 为上方四个列表的缩写
            timePeriodCount (int): 修改第几段时间(注意: 非第几节课, 从0开始)
            timePeriod (TimePeriod): 传入的时间表
            allowAppend (bool, optional): 是否允许在不够长时向后添加. Defaults to True.
        """

        # 我怎么之前写classtable没想到可以用一个字符串来指定修改哪个时间表...
        if timeTableToMod.lower() == "ntl1":
            if timePeriodCount >= len(self.normTimeList1):
                # 原理同Classtable中的修改函数, 以下略去注释
                if not allowAppend:
                    return
                else:
                    for _ in range(0, timePeriodCount - len(self.normTimeList1) + 1):
                        empTimePeriod: TimePeriod = TimePeriod(start=[0, 0], finish=[0, 0])
                        self.normTimeList1.append(empTimePeriod)
            self.normTimeList1[timePeriodCount] = timePeriod
        elif timeTableToMod.lower() == "ntl2":
            if timePeriodCount >= len(self.normTimeList2):
                if not allowAppend:
                    return
                else:
                    for _ in range(0, timePeriodCount - len(self.normTimeList2) + 1):
                        empTimePeriod: TimePeriod = TimePeriod(start=[0, 0], finish=[0, 0])
                        self.normTimeList2.append(empTimePeriod)
            self.normTimeList2[timePeriodCount] = timePeriod
        elif timeTableToMod.lower() == "stl1":
            if timePeriodCount >= len(self.satTimeList1):
                if not allowAppend:
                    return
                else:
                    for _ in range(0, timePeriodCount - len(self.satTimeList1) + 1):
                        empTimePeriod: TimePeriod = TimePeriod(start=[0, 0], finish=[0, 0])
                        self.satTimeList1.append(empTimePeriod)
            self.satTimeList1[timePeriodCount] = timePeriod
        elif timeTableToMod.lower() == "stl2":
            if timePeriodCount >= len(self.satTimeList2):
                if not allowAppend:
                    return
                else:
                    for _ in range(0, timePeriodCount - len(self.satTimeList2) + 1):
                        empTimePeriod: TimePeriod = TimePeriod(start=[0, 0], finish=[0, 0])
                        self.satTimeList2.append(empTimePeriod)
            self.satTimeList2[timePeriodCount] = timePeriod
        else:
            logger.error("修改时间表时传入了未知的时间表名称")

        return

    def parseTimeTable(self, filePath: str = "./timetable.txt", mode: str = "txt") -> None:
        """
        读取和解析时间表

        Args:
            filePath (str, optional): 时间表文件路径. Defaults to "./timetable.txt".
            mode (str, optional): 从什么文件读取, 支持txt和xlsx两种模式. Defaults to "txt".
        """

        logger.info(f"开始从路径 '{filePath}' 导入/解析时间表")

        if not os.path.exists(filePath):
            logger.error(f"导入/解析时间表时路径 '{filePath}' 不存在")

        # txt模式
        if mode.lower() == "txt" or mode.lower() == ".txt":
            with open(filePath, "r", encoding="utf-8") as ttf:          # TimeTableFile, 时间表文件
                lines: list[str] = ttf.readlines()
                count: int = 0                                          # 这是遍历计数器, 数这是第几行了
                timePeriodCount: int = 0                                # 这是时间段计数器, 作用应该挺明显的
                stat: int = 0                                           # 读到哪了, 0=平日, 1=周六
                # 遍历
                for line in lines:
                    if "周六" in line:                                   # 读到周六时间表, 改变标识, 跳过分割行
                        count += 1
                        stat = 1
                        timePeriodCount = 0                             # 写入新时间表, 时间段计数归零
                        continue
                    
                    # p1是position1的意思, 下面p2同理
                    p1: int = line.find(":") if line.find(":") != -1 else line.find(",")    # 找第一个 : 或者 , 的位置

                    if p1 == -1:                                        # 没有分隔符就跳过
                        logger.warning(f"导入/解析时间表时遇到了空行或者格式错误的行! Line number: {count + 1}")
                        count += 1
                        continue

                    prefix: str = line[0 : p1]                          # 获取每行前缀
                    # 获取时间段类型
                    timeType: int = 0
                    if "课间" in prefix or "休" in prefix or "操" in prefix:                 # 不会有哪个傻子在正课前面加这几个字吧?
                        timeType = 1
                    elif "分割" in prefix:
                        timeType = 2

                    p2: int = line.find("-") if line.find("-") != -1 else line.find("~")    # 找分隔符 - 或者 ~ 的位置

                    if p2 == -1:                                        # 没找到就跳过
                        logger.warning(f"解析时间表时解析到格式错误的行! Line number: {count + 1}")
                        count += 1
                        continue

                    t1 = line[p2 - 5 : p2]
                    t2 = line[p2 + 1 : p2 + 6]

                    if stat == 0:                                       # 平日时间表
                        # 不是哥们为什么我最开始tp1和tp2用一个变量不行啊? Python不是只有按值传参吗?????
                        tp1: TimePeriod = TimePeriod(start=self.hm_str2time(t1), finish=self.hm_str2time(t2), timetype=timeType)
                        self.modifyTimeTable(timeTableToMod="NTL1", timePeriodCount=timePeriodCount, timePeriod=tp1)

                        if len(line) > p1 + 13:                         # 长度大于p1 + 13说明这是一个含双重时间点的行, 等会, 不会有人
                                                                        # 时间写一位吧???? 算了不管了, 自生自灭吧
                            if line.find("/") > p2:                     # 判断双重时间分隔符的位置, 在p2后说明是终止时间点有两个
                                # 此处为读取第二波吃饭的时间, 格式为"第五节课:11:15-11:55/12:05
                                #                                                  ^^^^^ <-要读取的时间
                                # 你问我为什么不用 if "第五节课" in line这种简单的方法? 万一以后育明上午不是五节课了怎么办(
                                t3 = line[p2 + 7 : p2 + 12]
                                tp2: TimePeriod = TimePeriod(start=self.hm_str2time(t1), finish=self.hm_str2time(t3), 
                                                             timetype=timeType)
                                self.modifyTimeTable(timeTableToMod="NTL2", timePeriodCount=timePeriodCount, timePeriod=tp2)
                            else:                                       # 起始时间点有两个
                                # 读取午休开始时间, 格式为"午休:11:55/12:05-13:35"
                                #                          ^^^^^ <-这里要读取的时间
                                # ! 此处注意: 上方的tp永远是离"-"最近的时间, 因此上方的tp在这里是双周时间!!!
                                self.modifyTimeTable(timeTableToMod="NTL2", timePeriodCount=timePeriodCount, timePeriod=tp1)
                                t3 = line[p2 - 11 : p2 - 6]
                                tp2: TimePeriod = TimePeriod(start=self.hm_str2time(t3), finish=self.hm_str2time(t2), 
                                                             timetype=timeType)         # 此处为start
                                self.modifyTimeTable(timeTableToMod="NTL1", timePeriodCount=timePeriodCount, timePeriod=tp2)
                        else:
                            # 否则为正常行, 正常写入即可
                            self.modifyTimeTable(timeTableToMod="NTL2", timePeriodCount=timePeriodCount, timePeriod=tp1)
                    elif stat == 1:                                     # 周六时间表, 原理同上
                        tp1: TimePeriod = TimePeriod(start=self.hm_str2time(t1), finish=self.hm_str2time(t2), timetype=timeType)
                        self.modifyTimeTable(timeTableToMod="STL1", timePeriodCount=timePeriodCount, timePeriod=tp1)

                        if len(line) > p1 + 13:
                            if line.find("/") > p2:
                                t3 = line[p2 + 7 : p2 + 12]
                                tp2: TimePeriod = TimePeriod(start=self.hm_str2time(t1), finish=self.hm_str2time(t3))
                                self.modifyTimeTable(timeTableToMod="STL2", timePeriodCount=timePeriodCount, timePeriod=tp2)
                            else:
                                self.modifyTimeTable(timeTableToMod="STL2", timePeriodCount=timePeriodCount, timePeriod=tp1)
                                t3 = line[p2 - 11 : p2 - 6]
                                tp2: TimePeriod = TimePeriod(start=self.hm_str2time(t3), finish=self.hm_str2time(t2), 
                                                             timetype=timeType)
                                self.modifyTimeTable(timeTableToMod="STL1", timePeriodCount=timePeriodCount, timePeriod=tp2)
                        else:
                            self.modifyTimeTable(timeTableToMod="STL2", timePeriodCount=timePeriodCount, timePeriod=tp1)
                    timePeriodCount += 1
                    count += 1
        elif mode.lower() == "xlsx" or mode.lower() == ".xlsx":
            pass
        # TODO: parseTimeTable xlsx模式
        else:
            logger.error("导入/解析时间表时遇到不支持的模式")
            return

        logger.success("导入/解析时间表成功")

    def writeTimeTable(self, outPath: str = "./timetable.txt", mode: str = "txt") -> None:
        """
        将(修改过后的)时间表数据写入时间表文件

        Args:
            filePath (str, optional): 输出文件路径. Defaults to "./timetable.txt".
            mode (str, optional): 输出模式, 支持txt和xlsx两种模式. Defaults to "txt".
        """

        logger.info(f"开始输出时间表到路径 '{outPath}'")

        if mode.lower() == "txt" or mode.lower() == ".txt":
            with open(outPath, "w+", encoding="utf-8") as ttf:
                ttf.write("平日课表:\n")

                if len(self.normTimeList1) != len(self.normTimeList2):
                    logger.error("出现未知错误, 单/双周平日课表长度不一致, 取其最小值作为课表长度写入")

                classIndex: int = 0
                # 平日课表
                for count in range(0, min(len(self.normTimeList1), len(self.normTimeList2))):
                    line: str = ""

                    if self.normTimeList1[count].timeType != self.normTimeList2[count].timeType:
                        logger.error(f"出现未知错误, 单/双周平日课表索引为{count}的时间段类型不一致, 跳过此时间段")
                        continue
                    
                    # 写入前缀("第x节课/课间/分割线:")
                    if self.normTimeList1[count].timeType == 0:
                        line += f"第{classIndex + 1}节课:"
                        classIndex += 1
                    elif self.normTimeList1[count].timeType == 1:
                        line += "课间:"
                    elif self.normTimeList1[count].timeType == 2:
                        line += "分割线:"
                    else:                                                       # 理论上讲, 这个分支不会触发, 但是还是写上吧
                        logger.error(f"出现未知错误, 平日课表索引为{count}的时间段类型无法识别, 默认写入课程")
                        line += f"第{classIndex + 1}节课:"
                        classIndex += 1
                    
                    # 起始时间
                    # 双重时间点
                    if self.normTimeList1[count].start != self.normTimeList2[count].start:
                        # 不是为什么分行写输出会乱??
                        line += f"{self.normTimeList1[count].start[0]:02d}:{self.normTimeList1[count].start[1]:02d}/\
                            {self.normTimeList2[count].start[0]:02d}:{self.normTimeList2[count].start[1]:02d}"
                    else:                                                       # 正常时间点
                        line += f"{self.normTimeList1[count].start[0]:02d}:{self.normTimeList1[count].start[1]:02d}"

                    line += "-"
                    
                    # 结束时间
                    if self.normTimeList1[count].finish != self.normTimeList2[count].finish:
                        line += f"{self.normTimeList1[count].finish[0]:02d}:{self.normTimeList1[count].finish[1]:02d}/\
                            {self.normTimeList2[count].finish[0]:02d}:{self.normTimeList2[count].finish[1]:02d}"
                    else:
                        line += f"{self.normTimeList1[count].finish[0]:02d}:{self.normTimeList1[count].finish[1]:02d}"

                    line += "\n"
                    ttf.write(line.replace(" ", ""))        # 不写入空格

                    count += 1

                ttf.write("\n周六课表:\n")

                if len(self.satTimeList1) != len(self.satTimeList2):
                    logger.error("出现未知错误, 单/双周周六课表长度不一致, 取其最小值作为课表长度写入")

                # 周六课表
                classIndex = 0
                for count in range(0, min(len(self.satTimeList1), len(self.satTimeList2))):
                    line: str = ""

                    if self.satTimeList1[count].timeType != self.satTimeList2[count].timeType:
                        logger.error(f"出现未知错误, 单/双周周六课表索引为{count}的时间段类型不一致, 跳过此时间段")
                        continue

                    # 写入前缀("第x节课/课间/分割线:")
                    if self.satTimeList1[count].timeType == 0:
                        line += f"第{classIndex + 1}节课:"
                        classIndex += 1
                    elif self.satTimeList1[count].timeType == 1:
                        line += "课间:"
                    elif self.satTimeList1[count].timeType == 2:
                        line += "分割线:"
                    else:                                                       # 理论上讲, 这个分支不会触发, 但是还是写上吧
                        logger.error(f"出现未知错误, 周六课表索引为{count}的时间段类型无法识别, 默认写入课程")
                        line += f"第{classIndex + 1}节课:"
                        classIndex += 1
                    
                    # 起始时间
                    # 双重时间点
                    if self.satTimeList1[count].start != self.satTimeList2[count].start:
                        line += f"{self.satTimeList1[count].start[0]:02d}:{self.satTimeList1[count].start[1]:02d}/\
                            {self.satTimeList2[count].start[0]:02d}:{self.satTimeList2[count].start[1]:02d}"
                    else:                                                       # 正常时间点
                        line += f"{self.satTimeList1[count].start[0]:02d}:{self.satTimeList1[count].start[1]:02d}"

                    line += "-"
                    
                    # 结束时间
                    if self.satTimeList1[count].finish != self.satTimeList2[count].finish:
                        line += f"{self.satTimeList1[count].finish[0]:02d}:{self.satTimeList1[count].finish[1]:02d}/\
                            {self.satTimeList2[count].finish[0]:02d}:{self.satTimeList2[count].finish[1]:02d}"
                    else:
                        line += f"{self.satTimeList1[count].finish[0]:02d}:{self.satTimeList1[count].finish[1]:02d}"

                    line += "\n"
                    ttf.write(line.replace(" ", ""))        # 不写入空格

                    count += 1


        elif mode.lower() == "xlsx" or mode.lower() == ".xlsx":
            pass
        # TODO: writeTimeTable xlsx模式
        else:
            logger.error("写入时间表时遇到不支持的模式")
            return

        logger.success("写入时间表成功")

    def saveTimeTable(self, outPath = "./data/timetable.cic") -> None:
        """
        用pickle保存时间表

        Args:
            outPath (str, optional): 存放时间表数据的路径. Defaults to "./data/timetable.cic".
        """

        logger.info(f"开始保存时间表到路径 '{outPath}'")

        with open(outPath, "wb") as tt:
            pickle.dump(self, tt)

        logger.success("保存时间表成功")

        return

    def loadTimeTable(self, filePath = "./data/timetable.cic") -> None:
        """
        用pickle读取课表数据

        Args:
            filePath (str, optional): 存放课表数据的路径. Defaults to "./data/timetable.cic".
        """
        
        logger.info(f"开始从路径 '{filePath}' 加载时间表")

        try:
            with open(filePath, "rb") as tt:
                _timetable: TimeTable = pickle.load(tt)
        except FileNotFoundError:
            logger.error(f"加载时间表时路径 '{filePath}' 不存在")
            return
        
        self.normTimeList1 = _timetable.normTimeList1
        self.normTimeList2 = _timetable.normTimeList2
        self.satTimeList1 = _timetable.satTimeList1
        self.satTimeList2 = _timetable.satTimeList2

        logger.success("加载时间表成功")

        return
    
    def getTotalClassCount(self, timeTable: Literal["NTL1", "NTL2", "STL1", "STL2"]) -> int:
        if timeTable == "NTL1" or timeTable == "NTL2":
            count: int = 0
            for tp in self.normTimeList1:
                if tp.timeType == 0:
                    count += 1
            return count
        else:
            count: int = 0
            for tp in self.normTimeList2:
                if tp.timeType == 0:
                    count += 1
            return count
        