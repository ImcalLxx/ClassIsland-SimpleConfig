import sys
import os
from pathlib import Path

def resPath(relative_path):

    try:
        # _MEIPASS 是打包后程序解压到的临时目录
        base_path = sys._MEIPASS    # type: ignore
    except AttributeError:
        # 开发时，使用当前文件所在目录的父目录作为基础路径
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)