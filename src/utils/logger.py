import logging
import os
from datetime import datetime

class Logger:
    """统一的日志管理器"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """设置日志配置"""
        if self._logger is not None:
            return
            
        # 创建logger
        self._logger = logging.getLogger('rag_system')
        self._logger.setLevel(logging.DEBUG)
        
        # 避免重复添加handler
        if self._logger.handlers:
            return
        
        # 创建logs目录
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # 文件处理器
        log_file = os.path.join(logs_dir, f'rag_system_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
    
    @property
    def logger(self):
        """获取logger实例"""
        return self._logger
    
    def debug(self, message):
        """调试日志"""
        self.logger.debug(message)
    
    def info(self, message):
        """信息日志"""
        self.logger.info(message)
    
    def warning(self, message):
        """警告日志"""
        self.logger.warning(message)
    
    def error(self, message):
        """错误日志"""
        self.logger.error(message)
    
    def critical(self, message):
        """严重错误日志"""
        self.logger.critical(message)

# 全局日志实例
logger = Logger() 