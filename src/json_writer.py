# file: json_writer.py
# brief: Json文件读写模块
# time: 2025.8.9
# version: 0.1.0-Alpha-2
# TODOs:
#   1. 读取json文件并比较和已有课表的区别
#   2. 对应读取和修改Default.json.bak, 防止ClassIsland不信任课表

import pickle   # TODO: 写保存模块, 避免使用pickle
import time, datetime, math, uuid, os, orjson
from class_manager import TimePeriod, TimeTable, SingleClass, ClassTable
from mytime import MyTime
from loguru import logger

# 全部课程的列表
ALL_CLASSES: list[str] = ["语文", "数学", "外语", "物理", "化学", "政治", "历史", "地理", "生物", "体育", 
                          "心理", "研究", "自习", "社团", "通用技术", "班会", "信息技术", "音乐"]

# TODO: 这里我为了图方便用3个常量表达了AttachedObjects, 但我感觉日后这玩意得出大问题
# 特定上课提示, 有一些只有这两项, 上课的还有第三项
# 第三项为放学提示, uuid为 8fbc3a26-6d20-44dd-b895-b9411e3ddc51
# 此为含有2项的AttachedObjects
ATTACHED_OBJECTS_2: dict = {
                        "58e5b69a-764a-472b-bcf7-003b6a8c7fdf": {
                        "IsAttachSettingsEnabled": False,
                        "ShowExtraInfoOnTimePoint": True,
                        "ExtraInfoType": 0,
                        "IsCountdownEnabled": True,
                        "CountdownSeconds": 60,
                        "IsActive": False
                    },
                        "08f0d9c3-c770-4093-a3d0-02f3d90c24bc": {
                        "IsClassOnNotificationEnabled": True,
                        "IsClassOnPreparingNotificationEnabled": True,
                        "IsClassOffNotificationEnabled": True,
                        "ClassPreparingDeltaTime": 60,
                        "ClassOnPreparingText": "准备上课，请回到座位并保持安静，做好上课准备。",
                        "IsAttachSettingsEnabled": False,
                        "IsActive": False
                    }
                }

# 特定上课提示, 有一些只有这两项, 课程开始时还有第三项(其实是第一项)
# 第三项为上课提示, uuid为 8fbc3a26-6d20-44dd-b895-b9411e3ddc51
# 此为含有3项且额外项为上课提示的AttachedObjects(注: B=Begin哦)
ATTACHED_OBJECTS_3B: dict = {
                        "8fbc3a26-6d20-44dd-b895-b9411e3ddc51": {
                        "IsClassOnNotificationEnabled": True,
                        "IsClassOnPreparingNotificationEnabled": True,
                        "IsClassOffNotificationEnabled": True,
                        "ClassPreparingDeltaTime": 60,
                        "ClassOnPreparingText": "准备上课，请回到座位并保持安静，做好上课准备。",
                        "OutdoorClassOnPreparingText": "下节课程为户外课程，请合理规划时间，做好上课准备。",
                        "ClassOnPreparingMaskText": "即将上课",
                        "OutdoorClassOnPreparingMaskText": "即将上课",
                        "ClassOnMaskText": "上课",
                        "ClassOffMaskText": "课间休息",
                        "ClassOffOverlayText": "",
                        "IsAttachSettingsEnabled": False,
                        "IsActive": False
                    },
                        "58e5b69a-764a-472b-bcf7-003b6a8c7fdf": {
                        "IsAttachSettingsEnabled": False,
                        "ShowExtraInfoOnTimePoint": True,
                        "ExtraInfoType": 0,
                        "IsCountdownEnabled": True,
                        "CountdownSeconds": 60,
                        "IsActive": False
                    },
                        "08f0d9c3-c770-4093-a3d0-02f3d90c24bc": {
                        "IsClassOnNotificationEnabled": True,
                        "IsClassOnPreparingNotificationEnabled": True,
                        "IsClassOffNotificationEnabled": True,
                        "ClassPreparingDeltaTime": 60,
                        "ClassOnPreparingText": "准备上课，请回到座位并保持安静，做好上课准备。",
                        "IsAttachSettingsEnabled": False,
                        "IsActive": False
                    }
}


# 特定上课提示, 有一些只有这两项, 课程结束的还有第三项(其实是第一项)
# 第三项为放学提示, uuid为 8fbc3a26-6d20-44dd-b895-b9411e3ddc51
# 此为含有3项且额外项为放学提示的的AttachedObjects(注: E=End)
ATTACHED_OBJECTS_3E: dict = {
                        "8fbc3a26-6d20-44dd-b895-b9411e3ddc51": {
                        "IsEnabled": True,
                        "NotificationMsg": "今天的课程已结束，请同学们有序离开。",
                        "IsAttachSettingsEnabled": False,
                        "IsActive": False
                    },
                        "58e5b69a-764a-472b-bcf7-003b6a8c7fdf": {
                        "IsAttachSettingsEnabled": False,
                        "ShowExtraInfoOnTimePoint": True,
                        "ExtraInfoType": 0,
                        "IsCountdownEnabled": True,
                        "CountdownSeconds": 60,
                        "IsActive": False
                    },
                        "08f0d9c3-c770-4093-a3d0-02f3d90c24bc": {
                        "IsClassOnNotificationEnabled": True,
                        "IsClassOnPreparingNotificationEnabled": True,
                        "IsClassOffNotificationEnabled": True,
                        "ClassPreparingDeltaTime": 60,
                        "ClassOnPreparingText": "准备上课，请回到座位并保持安静，做好上课准备。",
                        "IsAttachSettingsEnabled": False,
                        "IsActive": False
                    }
                }


def time2str_hm(time: list[int]) -> str:
    """
    时间转字符串(hh:mm)格式

    Args:
        time (list[int]): 时间列表, 长度为2

    Returns:
        str: 转换完的字符串
    """

    if len(time) != 2:
        logger.error("转换时间到字符串时遇到无法解析的时间格式!")
        return "00:00"
    
    else:
        hour: str = str(time[0]) if time[0] >= 10 else ("0" + str(time[0]))
        min: str  = str(time[1]) if time[1] >= 10 else ("0" + str(time[1]))
    
    return hour + ":" + min

def to2digits(input: int) -> str:
    """
    把数字转换为两位

    Args:
        input (int): 输入数字(范围: 0-99)

    Returns:
        转换完的字符串
    """

    if input >= 10 and input <= 99:
        return str(input)
    elif input >= 0 and input <= 9:
        return "0" + str(input)
    else:
        return "00"


class JsonManager:
    """
    Json配置文件读写模块
    """

    myTime: MyTime
    
    assignedUUID: dict[str, uuid.UUID] = {}                             # 为课程分配的uuid
    # UUID包括:
    # ALL_CLASSES中的所有课程 -> 每种课程一个UUID
    # 平日-单, 平日-双, 周六-单, 周六-双 -> 每个时间表对应一个UUID

    overAllDict: dict = {}                                              # 整个课表文件的字典

    error: bool = False

    def __init__(self, myTime: MyTime, uuidFilePath: str = "./data/uuid.cic") -> None:
        """
        初始化

        Args:
            uuidFilePath (str, optional): uuid文件的路径. Defaults to "./data/uuid.cic".
        """
        self.myTime = myTime
        
        # 读取课程uuid, 如果不存在就新分配
        if not os.path.exists(uuidFilePath):
            # 分配UUID
            logger.info("UUID文件不存在, 正在分配UUID")
            self.assignUUID()

            # 保存到文件中
            with open(uuidFilePath, "wb") as uf:
                pickle.dump(self.assignedUUID, uf)
        else:
            # 加载先前的uuid
            with open(uuidFilePath, "rb") as uf:
                self.assignedUUID = pickle.load(uf)
        
        self.checkRepairUUID()
            
        return
    
    def assignUUID(self) -> None:
        """
        分配UUID
        """
        # 1.为课程分配UUID
        for _class in ALL_CLASSES:
            self.assignedUUID[_class] = uuid.uuid4()
        # 2.为时间表分配UUID
        self.assignedUUID["平日-单"] = uuid.uuid4()
        self.assignedUUID["平日-双"] = uuid.uuid4()
        self.assignedUUID["周六-单"] = uuid.uuid4()
        self.assignedUUID["周六-双"] = uuid.uuid4()
        # 3.为课表分配uuid
        self.assignedUUID["今日课表"] = uuid.uuid4()
        # 4.为课表群分配uuid
        self.assignedUUID["默认"] = uuid.uuid4()

    def checkRepairUUID(self, uuidFilePath: str = "./data/uuid.cic") -> None:
        """
        检查UUID是否完整并尝试修复+保存

        Args:
            uuidFilePath (str, optional): uuid文件的路径. Defaults to "./data/uuid.cic".
        """

        tmp: int = 0        # 你会看懂这是干啥的

        # 1.检查课程UUID
        for _class in ALL_CLASSES:
            key: str = str(self.assignedUUID.get(_class, "NOT_FOUND"))
            if key == "NOT_FOUND":
                logger.warning(f"课程'{_class}'的UUID不存在, 正在分配UUID")
                self.assignedUUID[_class] = uuid.uuid4()
                tmp = 1
        # 2.检查时间表UUID
        keys: dict[str, str] = {
            "平日-单": str(self.assignedUUID.get("平日-单", "NOT_FOUND")),
            "平日-双": str(self.assignedUUID.get("平日-双", "NOT_FOUND")),
            "周六-单": str(self.assignedUUID.get("周六-单", "NOT_FOUND")),
            "周六-双": str(self.assignedUUID.get("周六-双", "NOT_FOUND"))
        }
        for key in keys:
            if keys.get(key) == "NOT_FOUND":
                logger.warning(f"时间表'{key}'的UUID不存在, 正在分配UUID")
                self.assignedUUID[key] = uuid.uuid4()
                tmp = 1
        # 3.检查课表uuid
        if str(self.assignedUUID.get("今日课表", "NOT_FOUND")) == "NOT_FOUND":
            logger.warning("'今日课表'的UUID不存在, 正在分配UUID")
            self.assignedUUID["今日课表"] = uuid.uuid4()
            tmp = 1
        # 4.检查课表群uuid
        if str(self.assignedUUID.get("默认", "NOT_FOUND")) == "NOT_FOUND":
            logger.warning("课表群'默认'的UUID不存在, 正在分配UUID")
            self.assignedUUID["默认"] = uuid.uuid4()
            tmp = 1

        # 保存到文件中
        with open(uuidFilePath, "wb") as uf:
            pickle.dump(self.assignedUUID, uf)

        if tmp == 1:
            logger.success(f"检查/修复UUID完成, 新的UUID文件将被写入到 '{uuidFilePath}'")
        else:
            logger.success(f"检查UUID完整性完成, 无缺失UUID")

        return
   
    def subject2Dict(self) -> dict:
        """
        将课程转换为字典(对应json文件中的Subjects的所有课程(整个字典))

        Returns:
            dict: 转换完成的字典("Subjects"后的整个字典)
        """
        
        retDict: dict = {}
        
        for _class in ALL_CLASSES:
            d: dict = {}                                                # 单节课的子字典
            
            # 写入子字典
            d["Name"] = _class
            d["Initial"] = _class[0]
            d["TeacherName"] = ""
            d["IsOutDoor"] = True if _class == "体育" else False
            d["AttachedObjects"] = ATTACHED_OBJECTS_2
            d["IsActive"] = False
            
            retDict[str(self.assignedUUID.get(_class))] = d             # 子字典写入总字典
            
        return retDict

    def timePeriod2Dict(self, timePeriod: TimePeriod, lastTpInDay: bool = False) -> dict:
        """
        时间段转换为列表

        Args:
            timePeriod (TimePeriod): 待转换的时间段
            lastTpInDay (bool, optional): 是否是一天最后一个时间段(用来控制是否显示放学提示)

        Returns:
            dict: 转换完的字典
        """

        retDict: dict = {}
        
        # 下方的日期无所谓, 我用的2025-01-01
        retDict["StartSecond"] = "2025-01-01T" + time2str_hm(timePeriod.start)  + ":00+08:00"
        retDict["EndSecond"]   = "2025-01-01T" + time2str_hm(timePeriod.finish) + ":00+08:00"
        retDict["TimeType"] = timePeriod.timeType
        retDict["IsHideDefault"] = False
        retDict["DefaultClassId"] = ""
        retDict["BreakName"] = ""
        retDict["ActionSet"] = None
        retDict["AttachedObjects"] = ATTACHED_OBJECTS_3E if lastTpInDay else ATTACHED_OBJECTS_3B
        retDict["IsActive"] = False

        return retDict

    def timeLayouts2Dict(self, timeTable: TimeTable) -> dict:
        """
        时间表输出到字典(对应TimeLayouts下的整个字典)

        Args:
            timeTable (TimeTable): 时间表

        Returns:
            dict: 输出的字典
        """

        # 本段json结构如下:
        # "TimeLayouts": {       <- 这是retDict
        #     (-uuid-): {        <- 这是subDicts[0], 对应平日-单
        #         "Name": ---
        #         "Layouts":[    <- 这是layoutList, 为一天的时间表
        #             {          <- 这是内部的单个字典, 为一个时间段
        #                 ......    <- 这些是靠timePeriod2Dict()完成处理的
        #             },
        #             {
        #                 ......
        #             },
        #             ......
        #         ]
        #     },
        #     (-uuid-): {        <- 这是subDicts[1], 对应平日-双
        #         ......         <- 以此类推
        #     }
        # }
        retDict: dict = {}
        subDicts: list[dict] = [{}, {}, {}, {}]                         # 子字典列表, 对应四个时间表

        if len(timeTable.normTimeList1) == 0:
            logger.warning("平日(周一-周五)-单周时间表为空")
        if len(timeTable.normTimeList2) == 0:
            logger.warning("平日(周一-周五)-双周时间表为空")
        if len(timeTable.satTimeList1) == 0:
            logger.warning("周六-单周时间表为空")
        if len(timeTable.satTimeList2) == 0:
            logger.warning("周六-双周时间表为空")

        # 处理timeTable中的normTimeList1
        subDicts[0]["Name"] = "平日-单"

        dayTimeTable1: list[dict] = []
        count: int = 0
        for tp in timeTable.normTimeList1:
            dayTimeTable1.append(self.timePeriod2Dict(timePeriod=tp, lastTpInDay=(count == len(timeTable.normTimeList1) - 1)))
            count += 1
        subDicts[0]["Layouts"] = dayTimeTable1

        # 处理timeTable中的normTimeList2
        subDicts[1]["Name"] = "平日-双"

        dayTimeTable2: list[dict] = []
        count = 0
        for tp in timeTable.normTimeList2:
            dayTimeTable2.append(self.timePeriod2Dict(timePeriod=tp, lastTpInDay=(count == len(timeTable.normTimeList2) - 1)))
            count += 1
        subDicts[1]["Layouts"] = dayTimeTable2

        # 处理timeTable中的satTimeList1
        subDicts[2]["Name"] = "周六-单"

        dayTimeTable3: list[dict] = []
        count = 0
        for tp in timeTable.satTimeList1:
            dayTimeTable3.append(self.timePeriod2Dict(timePeriod=tp, lastTpInDay=(count == len(timeTable.satTimeList1) - 1)))
            count += 1
        subDicts[2]["Layouts"] = dayTimeTable3

        # 处理timeTable中的satTimeList2
        subDicts[3]["Name"] = "周六-双"

        dayTimeTable4: list[dict] = []
        count = 0
        for tp in timeTable.satTimeList2:
            dayTimeTable4.append(self.timePeriod2Dict(timePeriod=tp, lastTpInDay=(count == len(timeTable.satTimeList2) - 1)))
            count += 1
        subDicts[3]["Layouts"] = dayTimeTable4

        retDict[str(self.assignedUUID.get("平日-单"))] = subDicts[0]
        retDict[str(self.assignedUUID.get("平日-双"))] = subDicts[1]
        retDict[str(self.assignedUUID.get("周六-单"))] = subDicts[2]
        retDict[str(self.assignedUUID.get("周六-双"))] = subDicts[3]

        return retDict
    
    def singleClass2Dict(self, singleClass: SingleClass) -> dict:
        """
        单节课转换为列表

        Args:
            singleClass (SingleClass): 待转换的单节课

        Returns:
            dict: 转换完的字典
        """

        retDict: dict = {}

        if singleClass.name == "":
            return retDict

        retDict["SubjectId"] = str(self.assignedUUID.get(singleClass.name))
        retDict["IsChangedClass"] = False
        retDict["IsEnabled"] = True
        retDict["AttachedObjects"] = {}
        retDict["IsActive"] = False

        return retDict

    def classPlan2Dict(self, classTable: ClassTable, myTime: MyTime) -> dict:
        """
        课程计划输出到字典(对应json文件中ClassPlans后的整个字典)

        Args:
            classTable (ClassTable): 课表
            timeTable (TimeTable): 时间表

        Returns:
            dict: ClassPlans后的整个字典
        """

        # 本段json结构如下
        # "ClassPlans" : {      <- 这是retDict
        #     (-uuid-): {       <- 这是subDict, 对应当天执行的课表
        #         "TimeLayoutId": "xxxxxx"
        #         "TimeRule": {  <- 这是timeRuleDict
        #                 ......
        #             }
        #         "Classes": [   <- 这是classesList, 对应classTable.classTableToday
        #
        #             ]
        #         "Name": "xxxxxx"
        #         ......
        #     }
        # }
        retDict: dict = {}
        subDict: dict = {}

        if len(classTable.classTableToday) == 0:
            logger.warning("今日课表为空, 暂停写入课表")
            return {}

        # 先把时间计算明白
        time_20250707: int = 1751817600                                 # 以2025/07/07 00:00:00为时间基准(此时为单周)
        timenow: int  = int(time.time())                                # 当前的时间戳
        curDateTime = datetime.datetime.now()
        secdiff: int = timenow - time_20250707

        SEC_PER_DAY: int = 86400
        daydiff = math.ceil(secdiff / SEC_PER_DAY)                      # 差的天数

        weekcount1 = ((daydiff % 2) + myTime.weekOffset1) % 2           # 单双周
        weekcount2 = ((daydiff % 3) + myTime.weekOffset2) % 3           # 3周轮换

        timeLayoutUUID: str = ""                                        # TimeLayout uuid

        if   weekcount1 == 0 and curDateTime.weekday() != 5:            # 单周, 非周六
            timeLayoutUUID = str(self.assignedUUID.get("平日-单"))
        elif weekcount1 == 0 and curDateTime.weekday() == 5:
            timeLayoutUUID = str(self.assignedUUID.get("周六-单"))
        elif weekcount1 == 1 and curDateTime.weekday() != 5:
            timeLayoutUUID = str(self.assignedUUID.get("平日-双"))
        elif weekcount1 == 1 and curDateTime.weekday() == 5:
            timeLayoutUUID = str(self.assignedUUID.get("周六-双"))
        else:                                                           # 理论上讲永远不会触发这个else, 但也是理论
            logger.critical("Man! What can I say! 如果你看到了这条报错, 那我只能说这已经无法用逻辑解释了(因为elif这个分支永远不会触发)")
            timeLayoutUUID = ""
        
        subDict["TimeLayoutId"] = timeLayoutUUID
        
        timeRuleDict: dict = {}
        # 周一-周六对应1-6, 周日=0
        timeRuleDict["WeekDay"] = curDateTime.weekday() + 1 if curDateTime.weekday() != 6 else 0
        timeRuleDict["WeekCountDiv"] = 0
        timeRuleDict["WeekCountDivTotal"] = 0
        timeRuleDict["IsActive"] = False

        subDict["TimeRule"] = timeRuleDict

        classesList: list = []
        for singleClass in classTable.classTableToday:
            classesList.append(self.singleClass2Dict(singleClass=singleClass))

        subDict["Classes"] = classesList
        subDict["Name"] = "今日课表"
        subDict["IsOverlay"] = False
        subDict["OverlaySourceId"] = None
        subDict["OverlaySetupTime"] = "20" + (curDateTime.strftime("%y-%m-%dT%H:%M:%S.000000+08:00"))
        subDict["IsEnabled"] = True
        subDict["AssociatedGroup"] = "00000000-0000-0000-0000-000000000000"
        subDict["AttachedObjects"] = ATTACHED_OBJECTS_3E
        subDict["IsActive"] = False

        retDict[str(self.assignedUUID.get("今日课表"))] = subDict

        return retDict

    def generateOverAllDict(self, classTable: ClassTable, timeTable: TimeTable) -> None:
        """
        最外层整个字典

        Returns:
            dict: 整个json文件的最外层字典
        """

        retDict: dict = {}

        curDateTime = datetime.datetime.now()
        if curDateTime.weekday() == 6:
            # TODO: 处理无课显示
            return

        retDict["Name"] = ""

        # 进行检查
        if self.classPlan2Dict(classTable, self.myTime) == {}:
            logger.error("写入课表配置文件终止")
            self.overAllDict = {}
            return

        retDict["TimeLayouts"] = self.timeLayouts2Dict(timeTable)
        retDict["ClassPlans"] = self.classPlan2Dict(classTable, self.myTime)
        retDict["Subjects"] = self.subject2Dict()
        retDict["IsOverlayClassPlanEnabled"] = False
        retDict["OverlayClassPlanId"] = None
        retDict["TempClassPlanId"] = None
        retDict["TempClassPlanSetupTime"] = "20" + (curDateTime.strftime("%y-%m-%dT%H:%M:%S.000000+08:00"))
        retDict["ClassPlanGroups"] = {
            "00000000-0000-0000-0000-000000000000": {
                "Name": "全局课表群",
                "IsGlobal": True,
                "IsActive": False
            },
            str(self.assignedUUID.get("默认")): {
                "Name": "默认",
                "IsGlobal": False,
                "IsActive": False
            }
        }
        retDict["SelectedClassPlanGroupId"] = "00000000-0000-0000-0000-000000000000"
        retDict["TempClassPlanGroupId"] = None
        retDict["TempClassPlanGroupExpireTime"] = "20" + (curDateTime.strftime("%y-%m-%dT%H:%M:%S.000000+08:00"))
        retDict["IsTempClassPlanGroupEnabled"] = False
        retDict["TempClassPlanGroupType"] = 1
        retDict["Id"] = "a56007c2-ce41-4676-88bc-cc77ca362c2c"
        retDict["OrderedSchedules"] = {}
        retDict["IsActive"] = False

        self.overAllDict = retDict

        return

    def writeJsonFile(self, filePath: str = "./output/Default.json") -> None:
        """
        写入Json配置文件

        Args:
            filePath (str, optional): 输出路径. Defaults to "./output/Default.json".
        """

        if self.overAllDict == {}:
            return
        
        logger.info(f"开始将课表配置文件写入到 '{filePath}'")

        with open(filePath, "wb") as jsonFile:
            jsonFile.write(orjson.dumps(self.overAllDict))

        logger.success("成功写入课表配置文件")

        return
    