#!/usr/bin/env python3
"""
德州扑克两人对战游戏主程序
"""

import sys
import os

def setup_windows_console():
    """
    配置 Windows 控制台以支持 UTF-8 和 ANSI 颜色
    需要在程序启动时尽早调用
    """
    if sys.platform != 'win32':
        return
    
    import ctypes
    from ctypes import wintypes
    
    # 设置控制台代码页为 UTF-8
    kernel32 = ctypes.windll.kernel32
    
    # 设置输入代码页为 UTF-8 (65001)
    kernel32.SetConsoleCP(65001)
    # 设置输出代码页为 UTF-8 (65001)
    kernel32.SetConsoleOutputCP(65001)
    
    # 启用 ANSI 虚拟终端处理
    # 获取标准输出句柄
    STD_OUTPUT_HANDLE = -11
    STD_ERROR_HANDLE = -12
    
    # 虚拟终端处理标志
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    
    for handle_id in [STD_OUTPUT_HANDLE, STD_ERROR_HANDLE]:
        handle = kernel32.GetStdHandle(handle_id)
        if handle == -1:
            continue
            
        # 获取当前控制台模式
        mode = wintypes.DWORD()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            # 启用虚拟终端处理
            new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(handle, new_mode)
    
    # 尝试设置环境变量（对某些旧版 Windows 有用）
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 尽早配置控制台（在导入其他模块之前）
setup_windows_console()

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
