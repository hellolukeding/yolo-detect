
import os
import sys

# 添加项目根目录到 Python 路径（必须在导入 service 之前）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from service.push_streamer_ffmpeg import FFmpegPushStreamer  # noqa: E402


def main():
    """主函数 - 使用 FFmpeg 推流"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║      YOLO FFmpeg 推流检测系统                         ║
    ║                                                       ║
    ║  使用 FFmpeg 替代 GStreamer，更容易部署               ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    # FFmpeg 推流配置（基于您的工作 GStreamer 命令）
    streamer = FFmpegPushStreamer(
        model_path="runs/train/person_detection/weights/best.pt",
        host="115.120.237.79",      # 推流目标服务器
        port=5004,                  # UDP RTP 端口
        video_width=640,            # 对应 GStreamer: width=640
        video_height=480,           # 对应 GStreamer: height=480
        fps=15,                     # 对应 GStreamer: framerate=15/1
        bitrate=400,                # 对应 GStreamer: bitrate=400 (kbps)
        camera_device=0,            # 摄像头设备 (Linux: '/dev/video4')
        headless=True               # 无头模式
    )

    # 开始推流
    streamer.start_streaming()


if __name__ == "__main__":
    main()
