"""
YOLO 快速入门示例
最简单的使用示例，适合初学者
"""

from ultralytics import YOLO

# 1. 加载预训练模型（第一次运行会自动下载）
print("正在加载YOLO模型...")
model = YOLO('yolo11n.pt')  # nano模型，速度最快

# 2. 检测图像
print("\n开始检测图像...")
results = model('https://ultralytics.com/images/bus.jpg')

# 3. 显示结果
print("\n检测结果:")
for result in results:
    boxes = result.boxes
    print(f"共检测到 {len(boxes)} 个目标\n")

    for box in boxes:
        # 获取类别名称和置信度
        class_id = int(box.cls[0])
        class_name = model.names[class_id]
        confidence = float(box.conf[0])

        # 获取边界框坐标
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        print(f"目标: {class_name}")
        print(f"  置信度: {confidence:.2%}")
        print(f"  位置: x1={x1:.0f}, y1={y1:.0f}, x2={x2:.0f}, y2={y2:.0f}\n")

# 4. 结果已自动保存
print(f"带标注的图像已保存到: {results[0].save_dir}")
print("\n完成! 🎉")

# 更多示例：
#
# 检测本地图像:
# results = model('path/to/your/image.jpg')
#
# 检测视频:
# results = model('path/to/your/video.mp4')
#
# 使用摄像头:
# results = model(0, show=True)
#
# 调整置信度阈值:
# results = model('image.jpg', conf=0.5)
#
# 只检测特定类别（例如只检测人）:
# results = model('image.jpg', classes=[0])
