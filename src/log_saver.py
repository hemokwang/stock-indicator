"""
Log Saver Module for Stock Analysis CLI Tool
Provides functionality to capture console output and save analysis logs.
"""

import sys
import io
import os
from datetime import datetime
import threading
import subprocess
import platform

# 尝试导入tkinter，如果失败则设置为None
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    tk = None
    filedialog = None
    messagebox = None
    TKINTER_AVAILABLE = False


class TeeOutput:
    """
    同时输出到屏幕和捕获到内存的类
    """
    def __init__(self, original_stream, capture_stream):
        self.original_stream = original_stream
        self.capture_stream = capture_stream
    
    def write(self, text):
        # 同时写入原始输出和捕获流
        self.original_stream.write(text)
        self.capture_stream.write(text)
        return len(text)
    
    def flush(self):
        self.original_stream.flush()
        self.capture_stream.flush()


class LogCapture:
    """
    Context manager to capture stdout/stderr while still displaying output.
    """
    def __init__(self):
        self.captured_output = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def __enter__(self):
        # 创建Tee输出，同时显示和捕获
        sys.stdout = TeeOutput(self.original_stdout, self.captured_output)
        sys.stderr = TeeOutput(self.original_stderr, self.captured_output)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def get_output(self):
        return self.captured_output.getvalue()


def get_keyboard_input():
    """
    按ESC键退出，任意键保存的键盘输入函数
    """
    try:
        if platform.system() == "Windows":
            import msvcrt
            print("按ESC键退出程序，按任意其他键保存分析记录...")
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\x1b':  # ESC key
                        return 'esc'
                    else:
                        return 'other'
        else:
            # Linux/Mac implementation
            import select
            import termios
            import tty
            
            print("按ESC键退出程序，按任意其他键保存分析记录...")
            
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setraw(sys.stdin.fileno())
                
                # Wait for input without timeout
                key = sys.stdin.read(1)
                if ord(key) == 27:  # ESC key
                    return 'esc'
                else:
                    return 'other'
                    
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                
    except ImportError:
        # Fallback for systems without required modules
        print("输入'q'退出程序，按回车键保存分析记录...")
        user_input = input().strip().lower()
        return 'esc' if user_input == 'q' else 'other'
    except Exception as e:
        print(f"键盘输入检测错误: {e}")
        print("输入'q'退出程序，按回车键保存分析记录...")
        user_input = input().strip().lower()
        return 'esc' if user_input == 'q' else 'other'


def choose_save_path():
    """
    选择保存路径，优先使用文件对话框，不可用时使用命令行输入
    """
    if not TKINTER_AVAILABLE:
        # tkinter不可用，直接使用命令行输入
        print("图形界面不可用，将使用命令行输入保存路径。")
        return choose_save_path_cli()
    
    try:
        # 尝试使用tkinter文件对话框
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        root.attributes('-topmost', True)  # 确保对话框在最前面
        
        # 设置默认文件名和目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"stock_analysis_log_{timestamp}.md"
        default_dir = get_default_save_directory()
        
        # 显示文件保存对话框
        file_path = filedialog.asksaveasfilename(
            title="选择保存位置",
            defaultextension=".md",
            initialname=default_filename,
            initialdir=default_dir,
            filetypes=[
                ("Markdown files", "*.md"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        root.destroy()
        return file_path
        
    except Exception as e:
        print(f"文件对话框错误: {e}")
        # 备用方案：使用命令行输入
        return choose_save_path_cli()


def get_default_save_directory():
    """
    获取默认保存目录
    """
    # 创建默认保存文件夹
    home_dir = os.path.expanduser("~")
    default_dir = os.path.join(home_dir, "stock_analysis_logs")
    
    # 确保目录存在
    os.makedirs(default_dir, exist_ok=True)
    
    return default_dir


def choose_save_path_cli():
    """
    命令行方式选择保存路径，使用默认文件夹
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"stock_analysis_log_{timestamp}.md"
    default_dir = get_default_save_directory()
    default_full_path = os.path.join(default_dir, default_filename)
    
    print(f"\n请输入保存文件的路径:")
    print(f"默认保存位置: {default_full_path}")
    print(f"直接按回车使用默认位置，或输入自定义路径")
    
    user_input = input("保存路径: ").strip()
    
    if not user_input:
        # 使用默认路径
        return default_full_path
    
    # 检查用户输入的路径
    if not user_input.endswith(('.md', '.txt')):
        # 如果用户只输入了目录，添加默认文件名
        if os.path.isdir(user_input) or user_input.endswith('/'):
            return os.path.join(user_input, default_filename)
        else:
            # 添加.md扩展名
            return user_input + '.md'
    
    return user_input


def format_log_as_markdown(log_content: str, stock_code: str = ""):
    """
    将日志内容格式化为Markdown格式
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 开始构建Markdown内容
    md_content = f"""# 股票分析记录

**分析时间:** {timestamp}  
**股票代码:** {stock_code}  
**生成工具:** Stock Analysis CLI Tool  

---

## 分析结果

```
{log_content}
```

---

## 免责声明

本分析报告由软件基于技术指标自动生成，仅供参考，不构成投资建议。投资有风险，决策需谨慎，请在做出任何投资决定前进行自己的研究和分析。

**报告生成时间:** {timestamp}
"""
    
    return md_content


def save_log_to_file(log_content: str, file_path: str, stock_code: str = ""):
    """
    将日志内容保存到指定文件
    """
    try:
        # 确保目录存在
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # 格式化为Markdown
        md_content = format_log_as_markdown(log_content, stock_code)
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"✅ 分析记录已保存至: {file_path}")
        
        # 尝试在文件管理器中显示文件
        try_open_file_location(file_path)
        
        return True
        
    except Exception as e:
        print(f"❌ 保存文件时出错: {e}")
        return False


def try_open_file_location(file_path: str):
    """
    尝试在文件管理器中打开文件位置，或提供路径信息
    """
    try:
        system = platform.system()
        directory = os.path.dirname(file_path)
        
        if system == "Windows":
            subprocess.run(['explorer', '/select,', file_path], check=False)
        elif system == "Darwin":  # macOS
            subprocess.run(['open', '-R', file_path], check=False)
        elif system == "Linux":
            # 检查是否在WSL环境中
            try:
                with open('/proc/version', 'r') as f:
                    version_info = f.read()
                if 'microsoft' in version_info.lower() or 'wsl' in version_info.lower():
                    # WSL环境，提供路径信息而不是尝试打开
                    print(f"📁 文件保存在: {file_path}")
                    print(f"📂 所在目录: {directory}")
                    return
            except:
                pass
            
            # 在Linux上，尝试不同的文件管理器
            try:
                result = subprocess.run(['nautilus', '--select', file_path], 
                                     capture_output=True, timeout=2)
                if result.returncode != 0:
                    raise FileNotFoundError
            except (FileNotFoundError, subprocess.TimeoutExpired):
                try:
                    result = subprocess.run(['dolphin', '--select', file_path], 
                                         capture_output=True, timeout=2)
                    if result.returncode != 0:
                        raise FileNotFoundError
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    try:
                        # 最后尝试xdg-open，但捕获输出避免错误消息
                        result = subprocess.run(['xdg-open', directory], 
                                             capture_output=True, timeout=2)
                        if result.returncode != 0:
                            raise FileNotFoundError
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        # 如果所有方法都失败，显示路径信息
                        print(f"📁 文件保存在: {file_path}")
                        print(f"📂 所在目录: {directory}")
    except Exception:
        # 最后的备用方案
        directory = os.path.dirname(file_path)
        print(f"📁 文件保存在: {file_path}")
        print(f"📂 所在目录: {directory}")


def handle_save_prompt(log_content: str, stock_code: str = ""):
    """
    处理保存提示和用户输入
    """
    try:
        # 获取用户输入
        user_choice = get_keyboard_input()
        
        if user_choice == 'esc':
            print("\n程序已退出。")
            return False
        else:
            print("\n正在选择保存位置...")
            
            # 选择保存路径
            file_path = choose_save_path()
            
            if file_path:
                # 保存文件
                success = save_log_to_file(log_content, file_path, stock_code)
                if success:
                    print("感谢使用股票分析工具！")
                    return True
                else:
                    print("保存失败，程序将退出。")
                    return False
            else:
                print("未选择保存位置，程序将退出。")
                return False
                
    except KeyboardInterrupt:
        print("\n\n用户中断，程序已退出。")
        return False
    except Exception as e:
        print(f"\n处理用户输入时出错: {e}")
        print("程序将退出。")
        return False


# 测试函数
if __name__ == "__main__":
    # 测试日志捕获
    with LogCapture() as capture:
        print("这是一个测试日志")
        print("包含多行内容")
        print("用于测试捕获功能")
    
    log_content = capture.get_output()
    print("捕获的日志内容:")
    print(log_content)
    
    # 测试保存功能
    handle_save_prompt(log_content, "000001")