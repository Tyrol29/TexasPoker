#!/usr/bin/env python3
"""
打包德州扑克游戏为独立可执行文件
"""

import os
import sys
import shutil
import subprocess

def main():
    """主打包函数"""
    print("=" * 60)
    print("Texas Hold'em Poker - EXE Builder")
    print("=" * 60)
    
    # 清理旧的构建文件
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理 {dir_name}/ 目录...")
            try:
                shutil.rmtree(dir_name)
            except PermissionError:
                print(f"  警告: 无法清理 {dir_name}/，可能正在被使用")
                # 如果 dist 存在但无法删除，尝试重命名旧 exe
                if dir_name == 'dist':
                    exe_path = os.path.join(dir_name, '德州扑克.exe')
                    if os.path.exists(exe_path):
                        backup_path = exe_path + '.old'
                        try:
                            os.replace(exe_path, backup_path)
                            print(f"  已重命名旧 exe 为 {backup_path}")
                        except:
                            pass
    
    # 清理旧的spec文件
    for f in os.listdir('.'):
        if f.endswith('.spec'):
            print(f"删除旧的 {f}...")
            os.remove(f)
    
    print("\n开始打包...")
    
    # PyInstaller 参数
    # --onefile: 打包成单个exe文件
    # --windowed: 不使用控制台窗口（如果有GUI）
    # --add-data: 添加数据文件
    # --name: 输出文件名
    # --hidden-import: 隐式导入的模块
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',           # 单文件模式
        '--console',           # 控制台应用（因为我们是CLI游戏）
        '--name', '德州扑克',   # 输出文件名
        '--clean',             # 清理临时文件
        # 包含所有子模块
        '--hidden-import', 'texas_holdem.core.card',
        '--hidden-import', 'texas_holdem.core.deck',
        '--hidden-import', 'texas_holdem.core.hand',
        '--hidden-import', 'texas_holdem.core.player',
        '--hidden-import', 'texas_holdem.core.table',
        '--hidden-import', 'texas_holdem.core.evaluator',
        '--hidden-import', 'texas_holdem.game.game_state',
        '--hidden-import', 'texas_holdem.game.betting',
        '--hidden-import', 'texas_holdem.game.game_engine',
        '--hidden-import', 'texas_holdem.ui.cli',
        '--hidden-import', 'texas_holdem.utils.constants',
        # 入口文件
        'texas_holdem/main.py'
    ]
    
    print(f"执行命令: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print("\n❌ 打包失败!")
        return 1
    
    print("\n" + "=" * 60)
    print("[OK] 打包成功!")
    print("=" * 60)
    
    exe_path = os.path.join('dist', '德州扑克.exe')
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\n[文件] 可执行文件: {exe_path}")
        print(f"[大小] 文件大小: {size_mb:.2f} MB")
        print(f"\n[使用说明]")
        print(f"   1. 将 {exe_path} 复制到目标电脑")
        print(f"   2. 双击运行即可，无需安装Python")
        print(f"\n[注意] 此exe文件需要在Windows系统上运行")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
