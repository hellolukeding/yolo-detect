"""
无头模式推流脚本
适用于无显示器的硬件设备（如树莓派、Jetson Nano等）
"""

from service.push_streamer import PushStreamer
import signal
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# 全局变量，用于信号处理
streamer = None
running = True


def signal_handler(sig, frame):
    """处理中断信号"""
    global running
    print("\n\n收到中断信号，正在停止推流...")
    running = False


def run_headless_streaming(
    model_path: str = "runs/train/person_detection/weights/best.pt",
    host: str = "115.120.237.79",
    port: int = 5004,
    camera_id: int = 0,
    video_width: int = 640,
    video_height: int = 480,
    fps: int = 30,
    bitrate: int = 500,
    conf: float = 0.25,
    iou: float = 0.45,
    device: str = "cpu",  # 硬件设备通常使用cpu或cuda
    enable_tracking: bool = True
):
    """
    运行无头模式推流

    Args:
        model_path: YOLO模型路径
        host: 推流目标IP地址
        port: 推流目标端口
        camera_id: 摄像头ID
        video_width: 视频宽度
        video_height: 视频高度
        fps: 帧率
        bitrate: 比特率(kbps)
        conf: 置信度阈值
        iou: IOU阈值
        device: 推理设备 (cpu/cuda/mps)
        enable_tracking: 是否启用目标跟踪
    """
    global streamer

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║         无头模式 YOLO 推流服务                        ║
    ║                                                       ║
    ║  适用于无显示器的硬件设备                             ║
    ║  按 Ctrl+C 停止推流                                  ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    print(f"配置信息:")
    print(f"  - 模型路径: {model_path}")
    print(f"  - 推流目标: {host}:{port}")
    print(f"  - 摄像头ID: {camera_id}")
    print(f"  - 视频尺寸: {video_width}x{video_height}")
    print(f"  - 帧率: {fps} fps")
    print(f"  - 比特率: {bitrate} kbps")
    print(f"  - 推理设备: {device}")
    print(f"  - 目标跟踪: {'启用' if enable_tracking else '禁用'}")
    print()

    # 检查模型是否存在
    if not Path(model_path).exists():
        print(f"❌ 错误: 模型文件不存在: {model_path}")
        sys.exit(1)

    # 创建推流器（启用无头模式）
    streamer = PushStreamer(
        model_path=model_path,
        host=host,
        port=port,
        video_width=video_width,
        video_height=video_height,
        fps=fps,
        bitrate=bitrate,
        headless=True  # 🔑 启用无头模式
    )

    try:
        # 开始推流（不显示预览窗口）
        streamer.start_streaming(
            camera_id=camera_id,
            conf=conf,
            iou=iou,
            device=device,
            show_preview=False,  # 🔑 禁用预览
            enable_tracking=enable_tracking
        )
    except Exception as e:
        print(f"❌ 推流失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="无头模式 YOLO 推流服务",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # 模型参数
    parser.add_argument(
        "--model",
        type=str,
        default="runs/train/person_detection/weights/best.pt",
        help="YOLO模型路径"
    )

    # 网络参数
    parser.add_argument(
        "--host",
        type=str,
        default="115.120.237.79",
        help="推流目标IP地址"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5004,
        help="推流目标端口"
    )

    # 摄像头参数
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="摄像头ID"
    )

    # 视频参数
    parser.add_argument(
        "--width",
        type=int,
        default=640,
        help="视频宽度"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=480,
        help="视频高度"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="视频帧率"
    )
    parser.add_argument(
        "--bitrate",
        type=int,
        default=500,
        help="视频比特率(kbps)"
    )

    # 检测参数
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="置信度阈值 (0-1)"
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.45,
        help="IOU阈值 (0-1)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda", "mps"],
        help="推理设备"
    )
    parser.add_argument(
        "--no-tracking",
        action="store_true",
        help="禁用目标跟踪"
    )

    args = parser.parse_args()

    # 运行推流
    run_headless_streaming(
        model_path=args.model,
        host=args.host,
        port=args.port,
        camera_id=args.camera,
        video_width=args.width,
        video_height=args.height,
        fps=args.fps,
        bitrate=args.bitrate,
        conf=args.conf,
        iou=args.iou,
        device=args.device,
        enable_tracking=not args.no_tracking
    )


if __name__ == "__main__":
    main()
