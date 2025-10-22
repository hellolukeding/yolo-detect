"""
测试摄像头是否可用
用于诊断 macOS 摄像头权限问题
"""

import sys

import cv2


def test_camera(camera_id=0):
    """
    测试指定的摄像头是否可用

    Args:
        camera_id: 摄像头索引 (0, 1, 2, ...)
    """
    print("=" * 60)
    print("🔍 摄像头测试工具")
    print("=" * 60)
    print(f"\n正在测试摄像头 {camera_id}...")

    # 尝试打开摄像头
    cap = cv2.VideoCapture(camera_id)

    if not cap.isOpened():
        print("\n❌ 错误: 无法打开摄像头")
        print("\n可能的原因:")
        print("1. macOS 摄像头权限未授予")
        print("2. 摄像头正被其他应用使用")
        print("3. 摄像头索引不正确")
        print("\n解决方案:")
        print("请查看 CAMERA_PERMISSION_FIX.md 文件获取详细帮助")
        print("\n快速修复:")
        print("1. 打开 系统设置 > 隐私与安全性 > 摄像头")
        print("2. 勾选 Terminal (或 VS Code)")
        print("3. 完全关闭并重新打开终端")
        print("4. 重新运行此脚本")
        cap.release()
        return False

    print("✅ 摄像头打开成功!")

    # 获取摄像头属性
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"\n📹 摄像头信息:")
    print(f"   分辨率: {int(width)} x {int(height)}")
    print(f"   帧率: {int(fps) if fps > 0 else '未知'} FPS")

    # 尝试读取一帧
    print("\n正在读取画面...")
    ret, frame = cap.read()

    if not ret:
        print("❌ 错误: 无法读取摄像头画面")
        cap.release()
        return False

    print("✅ 成功读取摄像头画面!")

    # 显示画面
    print("\n正在显示测试画面（2秒后自动关闭）...")
    try:
        cv2.imshow('Camera Test - Press any key to close', frame)
        cv2.waitKey(2000)  # 等待2秒或按键
        cv2.destroyAllWindows()
        print("✅ 画面显示成功!")
    except Exception as e:
        print(f"⚠️  无法显示画面: {e}")

    cap.release()

    print("\n" + "=" * 60)
    print("🎉 摄像头测试完成!")
    print("=" * 60)
    print("\n✅ 摄像头工作正常，可以运行 YOLO 检测了！")
    print("\n运行命令:")
    print("poetry run python scripts/webcam_detect.py")
    print("=" * 60)

    return True


def test_all_cameras():
    """测试多个摄像头索引"""
    print("=" * 60)
    print("🔍 扫描所有可用摄像头")
    print("=" * 60)

    available_cameras = []

    for i in range(5):  # 测试前5个索引
        print(f"\n测试摄像头 {i}...", end=" ")
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print("✅ 可用")
                available_cameras.append(i)
            else:
                print("⚠️  打开但无法读取")
        else:
            print("❌ 不可用")
        cap.release()

    print("\n" + "=" * 60)
    if available_cameras:
        print(f"找到 {len(available_cameras)} 个可用摄像头: {available_cameras}")
        print(f"\n推荐使用摄像头索引: {available_cameras[0]}")
    else:
        print("❌ 未找到可用摄像头")
        print("\n请检查:")
        print("1. macOS 摄像头权限设置")
        print("2. 摄像头是否被其他应用占用")
        print("\n查看详细帮助: CAMERA_PERMISSION_FIX.md")
    print("=" * 60)

    return available_cameras


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="摄像头测试工具")
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="摄像头索引 (默认: 0)"
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="扫描所有可用摄像头"
    )

    args = parser.parse_args()

    try:
        if args.scan:
            test_all_cameras()
        else:
            test_camera(args.camera)
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
