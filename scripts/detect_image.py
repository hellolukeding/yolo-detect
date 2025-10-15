"""
YOLO 图像检测示例
使用预训练的YOLO模型对图像进行目标检测
"""

from pathlib import Path

from ultralytics import YOLO


def detect_image(model_path: str = "yolo11n.pt",
                 image_path: str = None,
                 conf: float = 0.25,
                 save: bool = True):
    """
    使用YOLO模型检测图像中的目标

    Args:
        model_path: 模型路径，默认使用yolo11n.pt（会自动下载）
        image_path: 图像路径
        conf: 置信度阈值
        save: 是否保存结果
    """
    # 加载模型
    print(f"加载模型: {model_path}")
    model = YOLO(model_path)

    # 如果没有指定图像，使用示例图像
    if image_path is None:
        print("未指定图像，将使用Ultralytics示例图像")
        image_path = "https://ultralytics.com/images/bus.jpg"

    # 执行检测
    print(f"检测图像: {image_path}")
    results = model(image_path, conf=conf, save=save)

    # 打印结果
    for result in results:
        boxes = result.boxes
        print(f"\n检测到 {len(boxes)} 个目标:")
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()
            print(f"  - 类别: {model.names[cls]}, 置信度: {conf:.2f}, 位置: {xyxy}")

    print(f"\n结果保存在: {results[0].save_dir}")
    return results


if __name__ == "__main__":
    # 示例1: 使用默认设置检测示例图像
    print("=" * 50)
    print("示例1: 检测示例图像")
    print("=" * 50)
    detect_image()

    # 示例2: 检测自定义图像（如果存在）
    # detect_image(image_path="path/to/your/image.jpg")

    # 示例3: 使用不同的模型
    # detect_image(model_path="yolo11s.pt")  # 更大更准确的模型
