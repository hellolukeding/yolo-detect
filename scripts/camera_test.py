#!/usr/bin/env python3
"""
多任务视觉系统 - 长期摄像头测试脚本
- 使用完整流水线（行人检测 + 人脸检测 + 表情识别 + 年龄估计）
- 支持长期运行，帧率适中
- 手动按 'q' 键退出
"""

import sys
sys.path.insert(0, 'src')

import cv2
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from pipeline import MultiTaskPipeline, cv2_add_chinese_text

# 表情英文 -> 中文映射
EMOTION_CN = {
    'angry': '生气',
    'disgust': '厌恶',
    'fear': '恐惧',
    'happy': '开心',
    'neutral': '平静',
    'sad': '伤心',
    'surprise': '惊讶',
}


def main():
    print("=" * 70)
    print("🎬 多任务视觉系统 - 长期摄像头测试")
    print("=" * 70)

    # 配置参数
    config_path = "configs/config.yaml"
    camera_id = 0
    save_video = False  # 是否保存检测视频
    output_dir = Path("output/test_videos")

    # 初始化流水线
    print("\n🔄 初始化流水线...")
    pipeline = MultiTaskPipeline(config_path)
    print("✅ 流水线初始化完成")

    # 打开摄像头
    print(f"\n📹 打开摄像头 (ID={camera_id})...")
    cap = cv2.VideoCapture(camera_id)

    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return

    # 设置摄像头参数（降低帧率以节省资源）
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 15)  # 请求15fps

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"✅ 摄像头已打开: {width}x{height}")

    # 视频写入器（可选）
    video_writer = None
    if save_video:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = output_dir / f"detection_{timestamp}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(str(video_path), fourcc, 15, (width, height))
        print(f"📼 将保存视频到: {video_path}")

    print("\n" + "=" * 70)
    print("🎯 开始检测...")
    print("  按 'q' 键退出")
    print("  按 's' 键截图")
    print("  按 'v' 键切换视频保存")
    print("=" * 70)

    # 统计信息
    frame_count = 0
    start_time = time.time()
    last_fps_time = start_time
    fps_frames = 0
    current_fps = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️  无法读取帧，尝试重新连接...")
                cap.release()
                time.sleep(1)
                cap = cv2.VideoCapture(camera_id)
                continue

            frame_count += 1

            # 处理帧（检测）
            result_img, persons = pipeline.process_frame(frame)

            # 计算FPS
            fps_frames += 1
            now = time.time()
            if now - last_fps_time >= 1.0:
                current_fps = fps_frames
                fps_frames = 0
                last_fps_time = now

            # 统计信息
            total_time = now - start_time
            person_count = len(persons)
            face_count = sum(1 for p in persons if p.face)

            # 在图像上绘制信息面板
            info_x, info_y = 10, 30
            line_height = 35

            # 背景面板
            panel_height = 160
            cv2.rectangle(result_img, (5, 5), (500, panel_height), (0, 0, 0), -1)

            # 信息文本
            infos = [
                f"时间: {int(total_time//60)}:{int(total_time%60):02d} | 帧数: {frame_count}",
                f"FPS: {current_fps} | 行人: {person_count} | 人脸: {face_count}",
            ]

            # 添加检测到的人脸信息
            if persons:
                for i, p in enumerate(persons):
                    if p.face:
                        f = p.face
                        emotion_en = f.emotion if f.emotion else "?"
                        emotion_cn = EMOTION_CN.get(emotion_en, emotion_en)
                        age = f.age if f.age else "?"
                        infos.append(f"  [{i+1}] {emotion_cn} | {age}岁")
                        if i >= 2:  # 最多显示3个人
                            if len(persons) > 3:
                                infos.append(f"  ... 还有{len(persons)-3}人")
                            break

            # 绘制信息（使用中文支持）
            for i, info in enumerate(infos):
                result_img = cv2_add_chinese_text(result_img, info,
                                                  (info_x, info_y + i * line_height),
                                                  font_size=22, color=(0, 255, 0))

            # 保存状态
            status_text = "录制" if video_writer else ""
            if status_text:
                result_img = cv2_add_chinese_text(result_img, status_text,
                                                  (width - 120, 20),
                                                  font_size=30, color=(0, 0, 255))

            # 显示结果
            cv2.imshow("Multi-Task Detection", result_img)

            # 写入视频
            if video_writer:
                video_writer.write(result_img)

            # 按键处理
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n🛑 用户退出")
                break
            elif key == ord('s'):
                # 截图
                output_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                snapshot_path = output_dir / f"snapshot_{timestamp}.jpg"
                cv2.imwrite(str(snapshot_path), result_img)
                print(f"📸 已保存截图: {snapshot_path}")
            elif key == ord('v'):
                # 切换视频保存
                if video_writer is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    video_path = output_dir / f"detection_{timestamp}.mp4"
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    video_writer = cv2.VideoWriter(str(video_path), fourcc, 15, (width, height))
                    print(f"📼 开始录制: {video_path}")
                else:
                    video_writer.release()
                    video_writer = None
                    print("⏹️ 停止录制")

    except KeyboardInterrupt:
        print("\n⚠️  检测被中断")

    finally:
        # 清理
        if video_writer:
            video_writer.release()
            print("📼 视频已保存")
        cap.release()
        cv2.destroyAllWindows()

        # 最终统计
        total_time = time.time() - start_time
        avg_fps = frame_count / total_time if total_time > 0 else 0
        print("\n" + "=" * 70)
        print("📊 测试统计:")
        print(f"  总帧数: {frame_count}")
        print(f"  运行时间: {int(total_time//60)}:{int(total_time%60):02d}")
        print(f"  平均FPS: {avg_fps:.1f}")
        print("=" * 70)


if __name__ == "__main__":
    main()
