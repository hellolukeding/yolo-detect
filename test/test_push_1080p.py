#!/usr/bin/env python3
"""
YOLO FFmpeg 推流测试 - 1080p 版本
"""

import os
import sys

# 添加项目根目录到 Python 路径（必须在导入 service 之前）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from service.push_streamer_ffmpeg import FFmpegPushStreamer  # noqa: E402


def main():
    """主函数 - 使用 FFmpeg 推流 1080p"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║      YOLO FFmpeg 推流检测系统 (1080p)                ║
    ║                                                       ║
    ║  1920x1080 @ 15fps, 2000kbps                         ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    # FFmpeg 推流配置 - 1080p Full HD
    streamer = FFmpegPushStreamer(
        model_path="runs/train/person_detection/weights/best.pt",
        host="115.120.237.79",      # 推流目标服务器
        port=5004,                  # UDP RTP 端口
        video_width=1920,           # 1080p 宽度 (16:9)
        video_height=1080,          # 1080p 高度
        fps=15,                     # 帧率 15fps
        bitrate=2000,               # 2Mbps (1080p 推荐 2-4Mbps)
        camera_device=0,            # 摄像头设备 (Linux: '/dev/video4')
        headless=True               # 无头模式
    )

    # 开始推流
    streamer.start_streaming()


if __name__ == "__main__":
    main()
