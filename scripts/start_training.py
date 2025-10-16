"""
YOLO Person Detection Training Script
支持 Mac GPU (MPS) 加速训练
"""

import argparse
from pathlib import Path

import torch
from ultralytics import YOLO


def detect_device():
    """
    自动检测可用的训练设备

    Returns:
        tuple: (device_name, device_info)
    """
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return 'mps', 'Apple Silicon GPU (MPS) - 🚀 GPU 加速训练'
    elif torch.cuda.is_available():
        return 'cuda', f'NVIDIA GPU ({torch.cuda.get_device_name(0)}) - 🚀 GPU 加速训练'
    else:
        return 'cpu', 'CPU - ⚠️ 训练速度较慢，建议使用 GPU'


def print_training_info(args, device, device_info):
    """打印训练配置信息"""
    print("\n" + "=" * 70)
    print("🎯 YOLO Person Detection - 训练配置")
    print("=" * 70)
    print(f"📊 数据集配置: {args.data}")
    print(f"🤖 预训练模型: {args.model}")
    print(f"💻 训练设备: {device} ({device_info})")
    print(f"🔄 训练轮数: {args.epochs}")
    print(f"📦 批次大小: {args.batch}")
    print(f"🖼️  图片尺寸: {args.imgsz}")
    print(f"⏳ 早停耐心值: {args.patience}")
    print(f"💾 项目目录: {args.project}")
    print(f"📝 实验名称: {args.name}")
    print(f"👷 工作线程: {args.workers}")
    print("=" * 70 + "\n")


def train_yolo(args):
    """
    启动 YOLO 训练

    Args:
        args: 命令行参数
    """
    # 检测设备
    device, device_info = detect_device()

    # 如果用户指定了设备，使用用户指定的设备
    if args.device:
        device = args.device
        device_info = f"用户指定: {device}"

    # 打印训练信息
    print_training_info(args, device, device_info)

    # 检查文件是否存在
    if not Path(args.data).exists():
        print(f"❌ 错误: 数据集配置文件不存在: {args.data}")
        return

    if not Path(args.model).exists():
        print(f"❌ 错误: 模型文件不存在: {args.model}")
        return

    try:
        # 加载模型
        print(f"📥 加载预训练模型: {args.model}")
        model = YOLO(args.model)

        # 开始训练
        print("🚀 开始训练...\n")
        results = model.train(
            data=args.data,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            name=args.name,
            project=args.project,
            device=device,
            patience=args.patience,
            save=True,
            workers=args.workers,
            exist_ok=True,
            cache=False,
            # MPS 优化参数
            amp=True if device == 'mps' else True,  # 自动混合精度
            # 其他训练参数
            optimizer='auto',
            lr0=args.lr0,
            lrf=args.lrf,
            momentum=args.momentum,
            weight_decay=args.weight_decay,
            warmup_epochs=args.warmup_epochs,
            cos_lr=args.cos_lr,
            # 数据增强
            hsv_h=args.hsv_h,
            hsv_s=args.hsv_s,
            hsv_v=args.hsv_v,
            degrees=args.degrees,
            translate=args.translate,
            scale=args.scale,
            shear=args.shear,
            perspective=args.perspective,
            flipud=args.flipud,
            fliplr=args.fliplr,
            mosaic=args.mosaic,
            mixup=args.mixup,
            # 验证
            val=True,
            plots=True,
        )

        # 训练完成
        print("\n" + "=" * 70)
        print("✅ 训练完成！")
        print("=" * 70)
        print(f"📁 结果保存在: {args.project}/{args.name}/")
        print(f"🏆 最佳模型: {args.project}/{args.name}/weights/best.pt")
        print(f"📄 最后模型: {args.project}/{args.name}/weights/last.pt")
        print("=" * 70 + "\n")

        return results

    except KeyboardInterrupt:
        print("\n⚠️  训练被用户中断")
    except Exception as e:
        print(f"\n❌ 训练过程中发生错误: {str(e)}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description='YOLO Person Detection Training Script (支持 Mac GPU 加速)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # 基本参数
    parser.add_argument('--data', type=str, default='configs/dataset.yaml',
                        help='数据集配置文件路径')
    parser.add_argument('--model', type=str, default='models/yolo11n.pt',
                        help='预训练模型路径 (yolo11n.pt/yolo11s.pt/yolo11m.pt)')
    parser.add_argument('--epochs', type=int, default=100,
                        help='训练轮数')
    parser.add_argument('--batch', type=int, default=16,
                        help='批次大小')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='图片尺寸')
    parser.add_argument('--device', type=str, default=None,
                        help='训练设备 (cpu/mps/cuda)，默认自动检测')

    # 项目参数
    parser.add_argument('--project', type=str, default='runs/train',
                        help='项目保存目录')
    parser.add_argument('--name', type=str, default='person_detection',
                        help='实验名称')
    parser.add_argument('--workers', type=int, default=8,
                        help='数据加载线程数')
    parser.add_argument('--patience', type=int, default=50,
                        help='早停耐心值')

    # 优化器参数
    parser.add_argument('--lr0', type=float, default=0.01,
                        help='初始学习率')
    parser.add_argument('--lrf', type=float, default=0.01,
                        help='最终学习率 (lr0 * lrf)')
    parser.add_argument('--momentum', type=float, default=0.937,
                        help='SGD 动量/Adam beta1')
    parser.add_argument('--weight_decay', type=float, default=0.0005,
                        help='优化器权重衰减')
    parser.add_argument('--warmup_epochs', type=float, default=3.0,
                        help='预热轮数')
    parser.add_argument('--cos_lr', action='store_true',
                        help='使用余弦学习率调度')

    # 数据增强参数
    parser.add_argument('--hsv_h', type=float, default=0.015,
                        help='HSV 色调增强')
    parser.add_argument('--hsv_s', type=float, default=0.7,
                        help='HSV 饱和度增强')
    parser.add_argument('--hsv_v', type=float, default=0.4,
                        help='HSV 明度增强')
    parser.add_argument('--degrees', type=float, default=0.0,
                        help='旋转角度 (+/- deg)')
    parser.add_argument('--translate', type=float, default=0.1,
                        help='平移 (+/- fraction)')
    parser.add_argument('--scale', type=float, default=0.5,
                        help='缩放增益 (+/- gain)')
    parser.add_argument('--shear', type=float, default=0.0,
                        help='剪切 (+/- deg)')
    parser.add_argument('--perspective', type=float, default=0.0,
                        help='透视变换 (+/- fraction)')
    parser.add_argument('--flipud', type=float, default=0.0,
                        help='上下翻转概率')
    parser.add_argument('--fliplr', type=float, default=0.5,
                        help='左右翻转概率')
    parser.add_argument('--mosaic', type=float, default=1.0,
                        help='Mosaic 数据增强概率')
    parser.add_argument('--mixup', type=float, default=0.0,
                        help='Mixup 数据增强概率')

    args = parser.parse_args()

    # 开始训练
    train_yolo(args)


if __name__ == '__main__':
    main()
