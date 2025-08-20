# 当前demo已经实现了基础功能
# 包括基础显示, 自动生成配置文件, 单双周偏移调节等
# TODO: 当前未实现的功能: 
#   暂无

from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore    import Qt, QCoreApplication
from mytime          import MyTime
from eventbus        import EventBus
from eventhandler    import EventHandler
from gui             import Gui
from ciconfig_ui     import Ui_MainWindow
from class_manager   import ClassTable, TimeTable
from json_writer     import JsonManager
from logic           import Logic
from settings        import Settings
from settings_ui     import Settings_Ui
from loguru          import logger
import os, sys

def initLogger() -> None:
    """
    日志初始化
    """

    # 初始化日志
    logger.add("./data/log/program_log.log", rotation="1 days", compression="zip")
    logger.info("\n")

    return

def checkDir() -> None:
    """
    检查目录是否缺失
    """

    if not os.path.exists("./data"):
        logger.warning("目录 './data' 缺失, 重新创建")
        os.mkdir("./data")

    if not os.path.exists("./data/log"):
        logger.warning("目录 './data/log' 缺失, 重新创建")
        os.mkdir("./data/log")

    if not os.path.exists("./output"):
        logger.warning("目录 './output' 缺失, 重新创建")
        os.mkdir("./output")


    logger.success("检查程序目录完成, 没有目录缺失")
    return

def checkFirstTime() -> bool:
    """
    检查程序是否第一次启动
    """

    if os.path.exists("./data/.start_count"):
        startFirstTime = False
        classTable.loadClassTable()
        timeTable.loadTimeTable()
    else:
        logger.info("程序初次启动, 创建启动计数文件 './data/.start_count'")
        startFirstTime = True
        # 新建一个文件用于启动计数
        with open("./data/.start_count", "w+", encoding="utf-8") as f_startupCount:
            f_startupCount.write("欢迎使用CIConfig! 感谢你使用此软件!")
        
    return startFirstTime

if __name__ == '__main__':
    """
    Main Entry
    """

    # 执行一些前置操作
    initLogger()
    checkDir()

    myTime = MyTime()
    classTable: ClassTable = ClassTable(myTime)
    timeTable: TimeTable = TimeTable()
    jsonManager: JsonManager = JsonManager(myTime)

    # 查看是否为第一次启动
    startFirstTime: bool = checkFirstTime()

    try:
        classTable.getClassTableToday()
    except Exception:
        pass

    # 设置应用属性
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)

    # 初始化Qt主应用/主窗口
    app: QApplication = QApplication(sys.argv)
    window: QMainWindow = QMainWindow()
    settingsWindow: QMainWindow = QMainWindow()
    # 初始化控件
    ui: Ui_MainWindow = Ui_MainWindow()
    ui.setupUi(window)
    settingsUi: Settings_Ui = Settings_Ui()
    settingsUi.setupUi(settingsWindow)

    # 初始化事件总线
    eventBus: EventBus = EventBus(app, ui, settingsUi, myTime, classTable, timeTable, jsonManager)
    eventBus.connectAllSingal()

    # 初始化事件处理
    eventHandler: EventHandler = EventHandler(eventBus)
    eventHandler.connectAllSingal()

    # 初始化GUI
    gui: Gui = Gui(myTime, eventBus, app, window)
    gui.connectAllSingal()

    # 初始化逻辑处理
    logic: Logic = Logic(eventBus)
    logic.startFirstTime = startFirstTime
    logic.connectAllSingal()

    # 初始化设置类
    settings: Settings = Settings(settingsWindow, eventBus)
    settings.connectAllSingal()
    settings.init()                                                     # 加载设置

    # 初始化GUI
    gui.init()

    # 启动逻辑处理/GUI
    logic.start()
    gui.start()
