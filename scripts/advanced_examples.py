"""
YOLO 完整工作流示例
展示从加载模型到检测、跟踪、导出的完整流程
"""

from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


class YOLODetector:
    """YOLO检测器封装类"""

    def __init__(self, model_path: str = "yolo11n.pt"):
        """
        初始化YOLO检测器

        Args:
            model_path: 模型路径
        """
        print(f"加载模型: {model_path}")
        self.model = YOLO(model_path)
        self.model_path = model_path

    def predict(self, source, conf=0.25, iou=0.7, show=False, save=True):
        """
        执行预测

        Args:
            source: 图像源（路径、URL、numpy数组等）
            conf: 置信度阈值
            iou: NMS的IOU阈值
            show: 是否显示结果
            save: 是否保存结果
        """
        results = self.model.predict(
            source=source,
            conf=conf,
            iou=iou,
            show=show,
            save=save,
            verbose=True
        )
        return results

    def track(self, source, conf=0.25, iou=0.7, show=False, save=True):
        """
        执行目标跟踪

        Args:
            source: 视频源
            conf: 置信度阈值
            iou: NMS的IOU阈值
            show: 是否显示结果
            save: 是否保存结果
        """
        results = self.model.track(
            source=source,
            conf=conf,
            iou=iou,
            show=show,
            save=save,
            persist=True,  # 持续跟踪
            tracker="bytetrack.yaml",  # 使用ByteTrack跟踪器
            verbose=True
        )
        return results

    def get_model_info(self):
        """获取模型信息"""
        print(f"\n模型信息:")
        print(f"模型路径: {self.model_path}")
        print(f"模型类型: {self.model.task}")
        print(f"类别数量: {len(self.model.names)}")
        print(f"类别列表: {list(self.model.names.values())[:10]}...")  # 显示前10个类别

    def benchmark(self):
        """性能基准测试"""
        print("\n执行性能基准测试...")
        results = self.model.benchmark()
        return results


def example_image_detection():
    """示例1: 图像检测"""
    print("\n" + "=" * 50)
    print("示例1: 图像检测")
    print("=" * 50)

    detector = YOLODetector("yolo11n.pt")
    detector.get_model_info()

    # 检测示例图像
    results = detector.predict(
        source="https://ultralytics.com/images/bus.jpg",
        conf=0.25,
        save=True
    )

    # 处理结果
    for result in results:
        boxes = result.boxes
        print(f"\n检测到 {len(boxes)} 个目标:")
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            print(f"  - {detector.model.names[cls]}: {conf:.2f}")


def example_custom_processing():
    """示例2: 自定义结果处理"""
    print("\n" + "=" * 50)
    print("示例2: 自定义结果处理")
    print("=" * 50)

    detector = YOLODetector("yolo11n.pt")

    # 检测图像
    results = detector.predict(
        source="https://ultralytics.com/images/bus.jpg",
        save=False
    )

    # 获取原始图像和检测结果
    for result in results:
        # 获取带标注的图像
        annotated_img = result.plot()

        # 获取检测框
        boxes = result.boxes

        # 自定义处理
        print(f"\n自定义处理结果:")
        for box in boxes:
            # 获取边界框坐标
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            # 获取置信度和类别
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            class_name = detector.model.names[cls]

            # 计算中心点和面积
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            area = (x2 - x1) * (y2 - y1)

            print(f"类别: {class_name}")
            print(f"  置信度: {conf:.2f}")
            print(f"  边界框: ({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")
            print(f"  中心点: ({center_x:.1f}, {center_y:.1f})")
            print(f"  面积: {area:.1f}")
            print()


def example_model_comparison():
    """示例3: 不同模型对比"""
    print("\n" + "=" * 50)
    print("示例3: 不同YOLO模型对比")
    print("=" * 50)

    models = ["yolo11n.pt", "yolo11s.pt"]  # nano和small模型
    source = "https://ultralytics.com/images/bus.jpg"

    for model_name in models:
        print(f"\n测试模型: {model_name}")
        detector = YOLODetector(model_name)

        results = detector.predict(source=source, save=False)

        for result in results:
            boxes = result.boxes
            print(f"检测到 {len(boxes)} 个目标")

            # 显示高置信度的检测
            high_conf_boxes = [
                box for box in boxes if float(box.conf[0]) > 0.5]
            print(f"高置信度(>0.5)目标: {len(high_conf_boxes)}")


def example_class_filtering():
    """示例4: 类别过滤"""
    print("\n" + "=" * 50)
    print("示例4: 只检测特定类别")
    print("=" * 50)

    detector = YOLODetector("yolo11n.pt")

    # 只检测人、车、卡车
    # COCO类别: 0=person, 2=car, 7=truck
    results = detector.model.predict(
        source="https://ultralytics.com/images/bus.jpg",
        classes=[0, 2, 5, 7],  # person, car, bus, truck
        save=True
    )

    for result in results:
        boxes = result.boxes
        print(f"\n检测到 {len(boxes)} 个目标 (仅限特定类别):")
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            print(f"  - {detector.model.names[cls]}: {conf:.2f}")


if __name__ == "__main__":
    # 运行所有示例
    example_image_detection()
    example_custom_processing()
    example_model_comparison()
    example_class_filtering()

    print("\n" + "=" * 50)
    print("所有示例完成!")
    print("=" * 50)
