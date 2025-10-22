"""
测试推流服务
演示如何使用 PushStreamer 进行实时检测和推流
"""

from service.push_streamer import PushStreamer
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_basic_streaming():
    """测试基本推流功能"""
    print("=" * 60)
    print("测试1: 基本推流功能")
    print("=" * 60)

    streamer = PushStreamer(
        model_path="runs/train/person_detection/weights/best.pt",
        host="115.120.237.79",
        port=5004,
        video_width=640,
        video_height=480,
        fps=30,
        bitrate=500
    )

    streamer.start_streaming(
        camera_id=0,
        conf=0.25,
        iou=0.45,
        device="mps",
        show_preview=True,
        enable_tracking=True
    )


def test_high_quality_streaming():
    """测试高质量推流"""
    print("=" * 60)
    print("测试2: 高质量推流 (1280x720, 60fps)")
    print("=" * 60)

    streamer = PushStreamer(
        model_path="runs/train/person_detection/weights/best.pt",
        host="192.168.1.100",
        port=8554,
        video_width=1280,
        video_height=720,
        fps=60,
        bitrate=2000
    )

    streamer.start_streaming(
        camera_id=0,
        conf=0.5,
        iou=0.3,
        device="mps",
        show_preview=True,
        enable_tracking=True
    )


def test_detection_only():
    """测试仅检测功能（不推流）"""
    print("=" * 60)
    print("测试3: 仅检测（使用向后兼容方法）")
    print("=" * 60)

    streamer = PushStreamer(
        model_path="runs/train/person_detection/weights/best.pt"
    )

    streamer.webcam_detect_with_tracking(
        conf=0.25,
        iou=0.45,
        device="mps"
    )


def test_low_latency_streaming():
    """测试低延迟推流"""
    print("=" * 60)
    print("测试4: 低延迟推流配置")
    print("=" * 60)

    streamer = PushStreamer(
        model_path="models/yolo11n.pt",  # 使用更小的模型
        host="115.120.237.79",
        port=5004,
        video_width=640,
        video_height=480,
        fps=30,
        bitrate=400  # 降低比特率
    )

    streamer.start_streaming(
        camera_id=0,
        conf=0.3,
        iou=0.45,
        device="mps",
        show_preview=False,  # 关闭预览以减少延迟
        enable_tracking=False  # 关闭跟踪以提高速度
    )


def test_multiple_cameras():
    """测试多摄像头切换"""
    print("=" * 60)
    print("测试5: 多摄像头测试")
    print("=" * 60)

    camera_ids = [0, 1]  # 尝试前两个摄像头

    for cam_id in camera_ids:
        print(f"\n尝试使用摄像头 {cam_id}...")

        streamer = PushStreamer(
            model_path="runs/train/person_detection/weights/best.pt",
            host="115.120.237.79",
            port=5004 + cam_id  # 不同摄像头使用不同端口
        )

        try:
            streamer.start_streaming(
                camera_id=cam_id,
                conf=0.25,
                iou=0.45,
                device="mps",
                show_preview=True,
                enable_tracking=True
            )
        except Exception as e:
            print(f"摄像头 {cam_id} 启动失败: {e}")
            continue


def interactive_menu():
    """交互式菜单"""
    while True:
        print("\n" + "=" * 60)
        print("推流服务测试菜单")
        print("=" * 60)
        print("1. 基本推流功能")
        print("2. 高质量推流 (1280x720, 60fps)")
        print("3. 仅检测（不推流）")
        print("4. 低延迟推流")
        print("5. 多摄像头测试")
        print("0. 退出")
        print("=" * 60)

        choice = input("\n请选择测试项 (0-5): ").strip()

        if choice == "1":
            test_basic_streaming()
        elif choice == "2":
            test_high_quality_streaming()
        elif choice == "3":
            test_detection_only()
        elif choice == "4":
            test_low_latency_streaming()
        elif choice == "5":
            test_multiple_cameras()
        elif choice == "0":
            print("退出测试程序")
            break
        else:
            print("无效选择，请重试")


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║         YOLO 推流服务测试程序                         ║
    ║                                                       ║
    ║  功能：测试实时检测和视频推流                         ║
    ║  作者：YOLO Detection Team                           ║
    ║                                                       ║
    ║  注意事项：                                           ║
    ║  1. 确保已安装 GStreamer                             ║
    ║  2. 确保摄像头权限已授予                             ║
    ║  3. 确保模型文件存在                                 ║
    ║  4. 按 'q' 键退出推流                                ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    # 检查模型是否存在
    model_path = project_root / "runs/train/person_detection/weights/best.pt"
    if not model_path.exists():
        print(f"⚠️  警告: 默认模型文件不存在: {model_path}")
        print("请先训练模型或使用其他模型路径")
        print()

    # 启动交互式菜单
    interactive_menu()
