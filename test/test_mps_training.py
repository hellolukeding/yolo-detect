"""
快速测试 MPS GPU 训练
只训练几个 epoch 来验证 GPU 是否正常工作
"""

from pathlib import Path

import torch
from ultralytics import YOLO


def main():
    """测试 MPS GPU 训练"""

    # 检测设备
    if torch.backends.mps.is_available():
        device = 'mps'
        device_name = 'Apple Silicon GPU (MPS)'
    else:
        device = 'cpu'
        device_name = 'CPU'

    print("=" * 60)
    print("MPS GPU 训练测试")
    print("=" * 60)
    print(f"设备: {device_name}")
    print(f"测试轮数: 3 epochs")
    print(f"批次大小: 8")
    print("=" * 60)

    model = YOLO('models/yolo11n.pt')

    # 快速测试训练
    results = model.train(
        data='configs/dataset.yaml',
        epochs=3,                # 只训练3轮用于测试
        imgsz=640,
        batch=8,                 # 小批次
        name='mps_test',
        device=device,           # 使用 MPS
        workers=4,
        exist_ok=True,
        verbose=True,
        cache=False,
    )

    print("\n✅ GPU 训练测试完成！")
    print(f"训练使用设备: {device}")


if __name__ == "__main__":
    main()
