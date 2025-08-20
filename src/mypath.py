import sys
import os
from pathlib import Path

def resPath(relative_path):

    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS    # type: ignore
        
        # 如果你的资源在 main.dist 子目录中
        dist_subdir = "main.dist"  # 根据实际情况调整
        potential_path = os.path.join(base_path, dist_subdir, relative_path)
        
        if os.path.exists(potential_path):
            return potential_path
        else:
            # 如果不在子目录，尝试根目录
            return os.path.join(base_path, relative_path)
    else:
        # 开发环境
        return os.path.join(relative_path)