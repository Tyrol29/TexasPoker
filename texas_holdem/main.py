#!/usr/bin/env python3
"""
德州扑克两人对战游戏主程序
"""

import sys
import os

# 添加父目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from texas_holdem.ui.cli import CLI
except ImportError:
    # 备用方案：直接导入
    sys.path.insert(0, current_dir)
    from ui.cli import CLI

def main():
    """主函数"""
    try:
        cli = CLI()
        cli.main_menu()
    except KeyboardInterrupt:
        print("\n\n游戏被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()