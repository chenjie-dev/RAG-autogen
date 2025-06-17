import time
import textwrap

def print_section(title: str, content: str, width: int = 80):
    """打印格式化的内容区块
    
    Args:
        title: 标题
        content: 内容
        width: 输出宽度
    """
    print("\n" + "=" * width)
    print(f" {title} ".center(width, "="))
    print("=" * width)
    
    # 使用textwrap处理长文本
    wrapped_content = textwrap.fill(content, width=width-4)
    print(wrapped_content)
    print("=" * width)

def typewriter_print(text: str, delay: float = 0.01):
    """打字机效果打印文本
    
    Args:
        text: 要打印的文本
        delay: 字符间延迟时间
    """
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)

def print_header(title: str, width: int = 80):
    """打印标题头
    
    Args:
        title: 标题文本
        width: 输出宽度
    """
    print("\n" + "=" * width)
    print(f" {title} ".center(width, "="))
    print("=" * width)

def print_footer(width: int = 80):
    """打印结束分隔线
    
    Args:
        width: 输出宽度
    """
    print("=" * width)

def print_info(message: str):
    """打印信息消息
    
    Args:
        message: 信息内容
    """
    print(f"[INFO] {message}")

def print_warning(message: str):
    """打印警告消息
    
    Args:
        message: 警告内容
    """
    print(f"[WARNING] {message}")

def print_error(message: str):
    """打印错误消息
    
    Args:
        message: 错误内容
    """
    print(f"[ERROR] {message}")

def print_success(message: str):
    """打印成功消息
    
    Args:
        message: 成功内容
    """
    print(f"[SUCCESS] {message}")

def print_progress(current: int, total: int, description: str = "处理中"):
    """打印进度条
    
    Args:
        current: 当前进度
        total: 总数
        description: 描述文本
    """
    percentage = (current / total) * 100
    bar_length = 30
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\r{description}: |{bar}| {percentage:.1f}% ({current}/{total})', end='', flush=True)
    if current == total:
        print()  # 换行 