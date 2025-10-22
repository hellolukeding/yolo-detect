"""
日志工具模块
基于 loguru 封装，提供统一的日志记录功能
"""

import sys
from pathlib import Path

from loguru import logger

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
# 日志目录
LOG_DIR = ROOT_DIR / "logs"

# 确保日志目录存在
LOG_DIR.mkdir(exist_ok=True)


def setup_logger(
    log_level: str = "INFO",
    log_to_file: bool = True,
    rotation: str = "10 MB",
    retention: str = "30 days",
    compression: str = "zip",
    format_string: str = None,
    prefix: str = "YOLO-Detect"
):
    """
    配置并返回 logger 实例

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: 是否将日志输出到文件
        rotation: 日志文件轮转策略 (如 "10 MB", "1 week", "00:00")
        retention: 日志文件保留时间 (如 "30 days", "1 month")
        compression: 压缩格式 (如 "zip", "tar.gz")
        format_string: 自定义日志格式
        prefix: 日志前缀

    Returns:
        logger: 配置好的 logger 实例
    """
    # 移除默认的 handler
    logger.remove()

    # 默认日志格式
    if format_string is None:
        format_string = (
            f"<blue>[{prefix}]</blue> | "
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    # 添加控制台输出
    logger.add(
        sys.stderr,
        format=format_string,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # 添加文件输出
    if log_to_file:
        # 通用日志文件（所有级别）
        logger.add(
            LOG_DIR / "app_{time:YYYY-MM-DD}.log",
            format=format_string,
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            backtrace=True,
            diagnose=True
        )

        # 错误日志文件（仅 ERROR 及以上级别）
        logger.add(
            LOG_DIR / "error_{time:YYYY-MM-DD}.log",
            format=format_string,
            level="ERROR",
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            backtrace=True,
            diagnose=True
        )

    return logger


# 创建默认 logger 实例
default_logger = setup_logger()


def get_logger(name: str = None, log_level: str = "INFO"):
    """
    获取指定名称的 logger

    Args:
        name: logger 名称（通常使用模块名）
        log_level: 日志级别

    Returns:
        logger: logger 实例
    """
    if name:
        return logger.bind(name=name)
    return default_logger


# 便捷方法
def debug(message: str, *args, **kwargs):
    """记录 DEBUG 级别日志"""
    default_logger.debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """记录 INFO 级别日志"""
    default_logger.info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """记录 WARNING 级别日志"""
    default_logger.warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """记录 ERROR 级别日志"""
    default_logger.error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """记录 CRITICAL 级别日志"""
    default_logger.critical(message, *args, **kwargs)


def exception(message: str, *args, **kwargs):
    """记录异常信息（包含堆栈跟踪）"""
    default_logger.exception(message, *args, **kwargs)


# 导出
__all__ = [
    'logger',
    'setup_logger',
    'get_logger',
    'default_logger',
    'debug',
    'info',
    'warning',
    'error',
    'critical',
    'exception',
    'LOG_DIR'
]
