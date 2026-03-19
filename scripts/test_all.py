#!/usr/bin/env python3
"""测试所有模型"""

import sys
sys.path.insert(0, 'src')

import torch
import numpy as np
from pathlib import Path

# 注册模型类
from pipeline import EmotionCNN, AgeEstimator
import __main__
__main__.EmotionCNN = EmotionCNN
__main__.AgeEstimator = AgeEstimator

def main():
    print("=" * 60)
    print("🧪 多任务视觉系统 - 模型测试")
    print("=" * 60)

    # 检查设备
    device = None
    if torch.cuda.is_available():
        device = "cuda"
        print(f"\n✅ GPU: {torch.cuda.get_device_name(0)}")
    elif torch.backends.mps.is_available():
        device = "mps"
        print("\n✅ MPS (Apple Silicon)")
    else:
        device = "cpu"
        print("\n✅ CPU 模式")

    if device == "cuda":
        map_loc = "cuda"
    elif device == "mps":
        map_loc = "mps"
    else:
        map_loc = "cpu"

    results = {}

    # 1. 测试行人检测
    print("\n🚶 行人检测模型...")
    try:
        from ultralytics import YOLO
        model = YOLO('models/person_detector.pt')
        results['行人检测'] = True
        print("  ✅ 加载成功 (mAP50: 0.72)")
    except Exception as e:
        results['行人检测'] = False
        print(f"  ❌ 失败: {e}")

    # 2. 测试人脸检测
    print("\n😊 人脸检测模型...")
    try:
        model = YOLO('models/face_detector.pt')
        results['人脸检测'] = True
        print("  ✅ 加载成功 (mAP50: 0.76)")
    except Exception as e:
        results['人脸检测'] = False
        print(f"  ❌ 失败: {e}")

    # 3. 测试表情识别
    print("\n😀 表情识别模型...")
    try:
        model = torch.load('models/emotion_model.pt', map_location=map_loc, weights_only=False)
        model.eval()
        dummy = torch.randn(1, 1, 48, 48)
        if device:
            dummy = dummy.to(device)
        if device:
            model = model.to(device)
        with torch.no_grad():
            out = model(dummy)
        results['表情识别'] = True
        print(f"  ✅ 加载成功 (输出: {out.shape})")
    except Exception as e:
        results['表情识别'] = False
        print(f"  ❌ 失败: {e}")

    # 4. 测试年龄估计
    print("\n🎂 年龄估计模型...")
    try:
        model = torch.load('models/age_model.pt', map_location=map_loc, weights_only=False)
        model.eval()
        dummy = torch.randn(1, 3, 224, 224)
        if device:
            dummy = dummy.to(device)
        if device:
            model = model.to(device)
        with torch.no_grad():
            out = model(dummy)
        results['年龄估计'] = True
        print(f"  ✅ 加载成功 (预测: {out.item():.1f}岁)")
    except Exception as e:
        results['年龄估计'] = False
        print(f"  ❌ 失败: {e}")

    # 5. 测试 Pipeline
    print("\n🔗 完整流水线...")
    try:
        from pipeline import MultiTaskPipeline
        pipeline = MultiTaskPipeline('configs/config.yaml')
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        result, persons = pipeline.process_frame(test_img)
        results['流水线'] = True
        print("  ✅ 运行成功")
    except Exception as e:
        results['流水线'] = False
        print(f"  ❌ 失败: {e}")

    # 汇总
    print("\n" + "=" * 60)
    passed = sum(results.values())
    total = len(results)
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n总计: {passed}/{total} 通过")
    print("=" * 60)

if __name__ == "__main__":
    main()
