"""
使用训练好的YOLO模型进行网络摄像头实时检测
适用于训练完成后的模型推理
"""

from pathlib import Path

import cv2
from ultralytics import YOLO


def webcam_detect(
    model_path: str = "runs/train/person_detection/weights/best.pt",
    conf: float = 0.25,
    iou: float = 0.45,
    show: bool = True,
    save: bool = False,
    device: str = "mps"  # macOS使用mps，Windows/Linux使用cuda或cpu
):
    """
    使用训练好的YOLO模型进行网络摄像头实时检测

    Args:
        model_path: 训练好的模型路径（默认使用best.pt）
        conf: 置信度阈值（0-1之间，越高越严格）
        iou: IOU阈值，用于非极大值抑制
        show: 是否显示检测窗口
        save: 是否保存检测结果视频
        device: 推理设备 ('mps', 'cuda', 'cpu')
    """
    # 检查模型是否存在
    model_file = Path(model_path)
    if not model_file.exists():
        print(f"错误: 模型文件不存在: {model_path}")
        print("请检查训练是否完成，或使用正确的模型路径")
        return

    # 加载训练好的模型
    print(f"正在加载模型: {model_path}")
    model = YOLO(model_path)
    print(f"模型加载成功!")
    print(f"设备: {device}")
    print(f"置信度阈值: {conf}")
    print(f"IOU阈值: {iou}")
    print("-" * 50)

    # 打印模型信息
    print(f"模型类别: {model.names}")
    print("-" * 50)

    # 使用摄像头进行检测
    print("正在打开摄像头...")
    print("按 'q' 键退出检测")
    print("-" * 50)

    # 执行实时检测
    # source=0 表示使用默认摄像头
    # stream=True 表示使用流式处理，适合实时视频
    results = model.predict(
        source=0,  # 0表示默认摄像头，也可以使用1, 2等选择其他摄像头
        conf=conf,
        iou=iou,
        show=show,
        save=save,
        stream=True,
        device=device,
        verbose=False  # 减少输出信息
    )

    # 逐帧处理结果
    frame_count = 0
    try:
        for result in results:
            frame_count += 1
            boxes = result.boxes

            if boxes is not None and len(boxes) > 0:
                # 打印检测信息
                print(f"帧 {frame_count}: 检测到 {len(boxes)} 个目标", end="\r")

                # 可以在这里添加其他处理逻辑
                # 例如：保存检测结果、发送警报等

            # 检测是否按下'q'键退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n用户退出检测")
                break

    except KeyboardInterrupt:
        print("\n检测被中断")
    finally:
        cv2.destroyAllWindows()
        print(f"\n检测完成! 共处理 {frame_count} 帧")


def webcam_detect_with_tracking(
    model_path: str = "runs/train/person_detection/weights/best.pt",
    conf: float = 0.25,
    iou: float = 0.45,
    device: str = "mps"
):
    """
    使用训练好的YOLO模型进行网络摄像头实时检测（带目标跟踪）

    Args:
        model_path: 训练好的模型路径
        conf: 置信度阈值
        iou: IOU阈值
        device: 推理设备
    """
    # 检查模型是否存在
    model_file = Path(model_path)
    if not model_file.exists():
        print(f"错误: 模型文件不存在: {model_path}")
        return

    # 加载模型
    print(f"正在加载模型: {model_path}")
    model = YOLO(model_path)
    print(f"模型加载成功!")
    print(f"模型类别: {model.names}")
    print("-" * 50)
    print("正在打开摄像头（带目标跟踪）...")
    print("按 'q' 键退出检测")
    print("-" * 50)

    # 使用track方法进行目标跟踪
    results = model.track(
        source=0,
        conf=conf,
        iou=iou,
        show=True,
        stream=True,
        device=device,
        persist=True,  # 持久化跟踪器
        verbose=False
    )

    # 逐帧处理
    frame_count = 0
    try:
        for result in results:
            frame_count += 1
            boxes = result.boxes

            if boxes is not None and len(boxes) > 0:
                print(f"帧 {frame_count}: 检测到 {len(boxes)} 个目标", end="\r")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n用户退出检测")
                break

    except KeyboardInterrupt:
        print("\n检测被中断")
    finally:
        cv2.destroyAllWindows()
        print(f"\n检测完成! 共处理 {frame_count} 帧")


def main():
    """主函数：提供多种使用示例"""
    import argparse

    parser = argparse.ArgumentParser(description="YOLO网络摄像头实时检测")
    parser.add_argument(
        "--model",
        type=str,
        default="runs/train/person_detection/weights/best.pt",
        help="模型路径"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="置信度阈值"
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.45,
        help="IOU阈值"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="mps",
        help="推理设备 (mps/cuda/cpu)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="是否保存检测结果视频"
    )
    parser.add_argument(
        "--track",
        action="store_true",
        help="是否启用目标跟踪"
    )

    args = parser.parse_args()

    if args.track:
        # 使用目标跟踪模式
        webcam_detect_with_tracking(
            model_path=args.model,
            conf=args.conf,
            iou=args.iou,
            device=args.device
        )
    else:
        # 普通检测模式
        webcam_detect(
            model_path=args.model,
            conf=args.conf,
            iou=args.iou,
            save=args.save,
            device=args.device
        )


if __name__ == "__main__":
    # 直接运行示例
    print("=" * 50)
    print("YOLO网络摄像头实时检测")
    print("=" * 50)

    # 方式1: 基本检测（推荐）
    webcam_detect(
        model_path="runs/train/person_detection/weights/best.pt",
        conf=0.5,  # 可以调整置信度阈值
        device="mps"  # macOS使用mps，Windows/Linux使用cuda或cpu
    )

    # 方式2: 带目标跟踪的检测
    # webcam_detect_with_tracking(
    #     model_path="runs/train/person_detection/weights/best.pt",
    #     conf=0.5,
    #     device="mps"
    # )
