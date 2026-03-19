#!/usr/bin/env python3
"""
YOLO 推流服务启动脚本
自动选择摄像头并启动推流服务
"""

import sys
import os
import time
import logging
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


def start_streaming(config):
    """启动推流服务"""
    # 导入推流模块
    try:
        from service.push_streamer_ffmpeg import FFmpegPushStreamer
        logger.info("使用 FFmpeg 推流模式")
    except ImportError as e:
        logger.error(f"无法导入推流模块: {e}")
        sys.exit(1)

    # 获取摄像头配置
    camera_device = config.get('CAMERA_DEVICE', '0')
    camera_type = config.get('CAMERA_TYPE', 'usb')

    if camera_type == 'rtsp':
        logger.info(f"使用网络摄像头: {camera_device}")
    else:
        logger.info(f"使用 USB 摄像头: {camera_device}")

    # 确定摄像头索引
    if camera_type == 'usb' and camera_device.startswith('/dev/video'):
        camera_index = int(camera_device.replace('/dev/video', ''))
    else:
        camera_index = 0

    # 创建推流器
    try:
        streamer = FFmpegPushStreamer(
            model_path=config.get('MODEL_PATH', 'models/person_detector.pt'),
            host=config.get('PUSH_HOST', '192.168.1.100'),
            port=int(config.get('PUSH_PORT', 5004)),
            video_width=int(config.get('VIDEO_WIDTH', 640)),
            video_height=int(config.get('VIDEO_HEIGHT', 480)),
            fps=int(config.get('FPS', 15)),
            bitrate=int(config.get('BITRATE', 500)),
            camera_device=camera_index,
            headless=True
        )
        logger.info("推流器创建成功")
    except Exception as e:
        logger.error(f"创建推流器失败: {e}")
        sys.exit(1)

    # 启动推流
    try:
        logger.info("开始推流...")
        logger.info(f"推流地址: {config.get('PUSH_HOST')}:{config.get('PUSH_PORT')}")

        # FFmpegPushStreamer.start_streaming() 不需要参数
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
