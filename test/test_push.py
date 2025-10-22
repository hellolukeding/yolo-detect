import os
import sys

# 添加项目根目录到 Python 路径（必须在导入 service 之前）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from service.push_streamer import PushStreamer  # noqa: E402


def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║         YOLO 网络摄像头实时检测                        ║
    ║                                                       ║
    ║  功能：使用YOLO模型进行实时目标检测                   ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    # 使用 GStreamer UDP RTP H.264 推流到远程服务器
    # 参数基于工作的推流命令配置
    streamer = PushStreamer(
        model_path="runs/train/person_detection/weights/best.pt",
        host="115.120.237.79",      # 推流目标服务器
        port=5004,                  # UDP 端口
        video_width=640,            # 视频分辨率
        video_height=480,
        fps=30,                     # 帧率
        bitrate=2000,               # 比特率 2Mbps (提高质量)
        headless=True               # 无头模式（无显示器环境）
    )

    # 开始推流检测
    streamer.start_streaming(
        camera_id=0,
        conf=0.25,
        iou=0.45,
        device="cpu",
        show_preview=True,
        enable_tracking=True
    )


if __name__ == "__main__":
    main()
