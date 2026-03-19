#!/usr/bin/env python3
"""使用完整多任务流水线进行摄像头实时检测"""

import sys
sys.path.insert(0, 'src')

import cv2
import numpy as np
from pathlib import Path

from pipeline import MultiTaskPipeline


def test_camera_multitask(
    config_path: str = "configs/config.yaml",
    camera_id: int = 0,
    max_frames: int = 100
):
    """
    使用完整多任务流水线进行摄像头实时检测

    Args:
        config_path: 配置文件路径
        camera_id: 摄像头ID
        max_frames: 最大帧数
    """
    print("=" * 60)
    print("🎬 多任务视觉系统 - 摄像头实时检测")
    print("=" * 60)

    # 初始化流水线
    print("\n🔄 初始化流水线...")
    pipeline = MultiTaskPipeline(config_path)
    print("✅ 流水线初始化完成")

    # 打印配置
    print("\n📋 配置信息:")
    print(f"  - 行人检测模型: {pipeline.person_detector is not None}")
    print(f"  - 人脸检测模型: {pipeline.face_detector is not None}")
    print(f"  - 表情识别模型: {pipeline.emotion_model is not None}")
    print(f"  - 年龄估计模型: {pipeline.age_model is not None}")
    print(f"  - 置信度阈值: 行人={pipeline.person_conf}, 人脸={pipeline.face_conf}")

    # 打开摄像头
    print(f"\n📹 打开摄像头 (ID={camera_id})...")
    cap = cv2.VideoCapture(camera_id)

    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return

    # 获取摄像头参数
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(f"✅ 摄像头已打开: {width}x{height} @ {fps}fps")

    print("\n🎯 开始检测...")
    print("  按 'q' 键退出")
    print("  按 's' 键保存当前帧")
    print("-" * 60)

    frame_count = 0
    save_frame = False

    try:
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                print("⚠️  无法读取帧")
                break

            frame_count += 1

            # 处理帧
            result_img, persons = pipeline.process_frame(frame)

            # 在图像上绘制信息
            info_text = f"Frame: {frame_count} | Persons: {len(persons)}"
            cv2.putText(result_img, info_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # 显示结果
            cv2.imshow("Multi-Task Detection", result_img)

            # 保存帧（如果请求）
            if save_frame:
                save_path = f"output/frame_{frame_count}.jpg"
                Path(save_path).parent.mkdir(exist_ok=True)
                cv2.imwrite(save_path, result_img)
                print(f"💾 已保存: {save_path}")
                save_frame = False

            # 打印检测信息
            if persons:
                print(f"Frame {frame_count}: 检测到 {len(persons)} 个人", end="\r")
                for i, person in enumerate(persons):
                    face = person.face
                    if face:
                        emotion = face.emotion if face.emotion else "N/A"
                        age = face.age if face.age else "N/A"
                        print(f"  Person {i+1}: emotion={emotion}, age={age}")

            # 按键处理
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n🛑 用户退出")
                break
            elif key == ord('s'):
                save_frame = True

    except KeyboardInterrupt:
        print("\n⚠️  检测被中断")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"\n✅ 检测完成! 共处理 {frame_count} 帧")
        print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="多任务摄像头检测")
    parser.add_argument("--config", default="configs/config.yaml", help="配置文件路径")
    parser.add_argument("--camera", type=int, default=0, help="摄像头ID")
    parser.add_argument("--frames", type=int, default=100, help="最大帧数")

    args = parser.parse_args()

    test_camera_multitask(
        config_path=args.config,
        camera_id=args.camera,
        max_frames=args.frames
    )
