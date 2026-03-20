#!/usr/bin/env python3
"""
YOLO 推流服务启动脚本
自动选择摄像头并启动推流服务
"""

import logging
import os
import sys
import time
from pathlib import Path

# 添加项目路径
PROJECT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

# 配置日志
LOG_DIR = Path(os.environ.get("PROJECT_DIR", PROJECT_DIR)) / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "streaming.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("YOLO-Streaming")


def load_config():
    """加载配置文件"""
    config_file = PROJECT_DIR / "deploy" / "config" / "service.conf"

    if not config_file.exists():
        logger.error(f"配置文件不存在: {config_file}")
        logger.info("请先运行: sudo bash /opt/yolo-detect/deploy/scripts/detect_camera.sh")
        sys.exit(1)

    config = {}
    with open(config_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip().strip('"')

    # 应用模型预设到 models.yaml
    model_preset = config.get('MODEL_PRESET', 'standard')
    models_config_file = PROJECT_DIR / "deploy" / "config" / "models.yaml"
    if models_config_file.exists():
        import yaml
        with open(models_config_file) as f:
            models_config = yaml.safe_load(f)
        models_config['active_preset'] = model_preset
        # 写回项目目录的 models.yaml
        project_models_file = PROJECT_DIR / "configs" / "models.yaml"
        with open(project_models_file, 'w') as f:
            yaml.dump(models_config, f)
        logger.info(f"模型预设: {model_preset}")

    return config


def resolve_camera_device(camera_type, camera_device):
    """解析摄像头配置，保留可直接传给 OpenCV 的设备值。"""
    normalized_type = (camera_type or "usb").strip().lower()
    normalized_device = str(camera_device or "0").strip()

    if normalized_type == "rtsp":
        return normalized_device

    if normalized_device.startswith("/dev/video"):
        return normalized_device

    if normalized_device.isdigit():
        return int(normalized_device)

    return normalized_device


def resolve_service_role(service_role):
    """解析部署角色。"""
    normalized_role = (service_role or "integrated").strip().lower()
    valid_roles = {"integrated", "edge", "server"}
    if normalized_role not in valid_roles:
        raise ValueError(f"不支持的 SERVICE_ROLE: {service_role}")
    return normalized_role


def build_runtime_settings(config):
    """构建运行时配置，统一角色差异。"""
    service_role = resolve_service_role(config.get("SERVICE_ROLE", "integrated"))
    camera_type = config.get("CAMERA_TYPE", "usb")
    camera_device = config.get("CAMERA_DEVICE", "0")

    return {
        "service_role": service_role,
        "camera_type": camera_type,
        "camera_device": resolve_camera_device(camera_type, camera_device),
        "push_host": config.get("PUSH_HOST", "127.0.0.1"),
        "push_port": int(config.get("PUSH_PORT", 5004)),
        "listen_host": config.get("LISTEN_HOST", "0.0.0.0"),
        "listen_port": int(config.get("LISTEN_PORT", config.get("PUSH_PORT", 5004))),
        "model_path": config.get("MODEL_PATH", "models/person_detector.pt"),
        "video_width": int(config.get("VIDEO_WIDTH", 640)),
        "video_height": int(config.get("VIDEO_HEIGHT", 480)),
        "fps": int(config.get("FPS", 15)),
        "bitrate": int(config.get("BITRATE", 500)),
        "confidence": float(config.get("CONFIDENCE", 0.5)),
        "iou": float(config.get("IOU", 0.45)),
        "device": config.get("DEVICE", "cpu"),
    }


def start_streaming(config):
    """按角色启动服务。"""
    settings = build_runtime_settings(config)
    logger.info(f"服务角色: {settings['service_role']}")

    if settings["service_role"] == "server":
        try:
            from service.remote_stream_analyzer import RemoteStreamAnalyzer
            logger.info("使用远端收流分析模式")
        except ImportError as e:
            logger.error(f"无法导入远端分析模块: {e}")
            sys.exit(1)

        analyzer = RemoteStreamAnalyzer(
            model_path=settings["model_path"],
            listen_host=settings["listen_host"],
            listen_port=settings["listen_port"],
            video_width=settings["video_width"],
            video_height=settings["video_height"],
            confidence=settings["confidence"],
            device=settings["device"],
        )
        logger.info("分析器创建成功")
        logger.info(f"监听地址: {settings['listen_host']}:{settings['listen_port']}")
        analyzer.start()
        return

    try:
        from service.push_streamer_ffmpeg import FFmpegPushStreamer
        logger.info("使用 FFmpeg 推流模式")
    except ImportError as e:
        logger.error(f"无法导入推流模块: {e}")
        sys.exit(1)

    if settings["camera_type"] == 'rtsp':
        logger.info(f"使用网络摄像头: {settings['camera_device']}")
    else:
        logger.info(f"使用 USB 摄像头: {settings['camera_device']}")
    logger.info(f"摄像头启动参数: {settings['camera_device']!r}")

    try:
        streamer = FFmpegPushStreamer(
            model_path=settings["model_path"],
            host=settings["push_host"],
            port=settings["push_port"],
            video_width=settings["video_width"],
            video_height=settings["video_height"],
            fps=settings["fps"],
            bitrate=settings["bitrate"],
            camera_device=settings["camera_device"],
            headless=True,
            enable_detection=settings["service_role"] != "edge",
            confidence=settings["confidence"],
            device=settings["device"],
        )
        logger.info("推流器创建成功")
    except Exception as e:
        logger.error(f"创建推流器失败: {e}")
        sys.exit(1)

    try:
        logger.info("开始推流...")
        logger.info(f"推流地址: {settings['push_host']}:{settings['push_port']}")
        streamer.start_streaming()
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭...")
    except Exception as e:
        logger.error(f"推流过程出错: {e}", exc_info=True)
        raise


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("YOLO 推流服务启动")
    logger.info("=" * 50)

    # 加载配置
    config = load_config()
    logger.info(f"配置加载成功")

    # 重试机制
    max_retries = 3
    retry_delay = 10

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"启动尝试 {attempt}/{max_retries}")
            start_streaming(config)
            break
        except Exception as e:
            logger.error(f"启动失败: {e}")
            if attempt < max_retries:
                logger.info(f"{retry_delay}秒后重试...")
                time.sleep(retry_delay)
            else:
                logger.error("达到最大重试次数，退出")
                sys.exit(1)


if __name__ == "__main__":
    main()
