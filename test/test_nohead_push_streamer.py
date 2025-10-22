

from service.push_streamer import PushStreamer
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║         YOLO 网络摄像头实时检测                        ║
    ║                                                       ║
    ║  功能：使用YOLO模型进行实时目标检测，无显示器                   ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    streamer = PushStreamer(
        model_path="runs/train/person_detection/weights/best.pt",
        host="115.120.237.79",
        port=5004,
        video_width=640,
        video_height=480,
        fps=30,
        bitrate=500,
        headless=True
    )

    # 开始推流检测
    streamer.start_streaming(
        camera_id=0,
        conf=0.25,
        iou=0.45,
        device="mps",
        show_preview=True,
        enable_tracking=True
    )


if __name__ == "__main__":
    main()
