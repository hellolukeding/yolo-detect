"""
YOLO 批量图像检测示例
批量处理文件夹中的所有图像
"""

import json
from pathlib import Path

from ultralytics import YOLO


def batch_detect(model_path: str = "yolo11n.pt",
                 source_dir: str = "datasets/images",
                 conf: float = 0.25,
                 save: bool = True,
                 export_json: bool = True):
    """
    批量检测文件夹中的所有图像

    Args:
        model_path: 模型路径
        source_dir: 图像文件夹路径
        conf: 置信度阈值
        save: 是否保存结果图像
        export_json: 是否导出JSON结果
    """
    # 加载模型
    print(f"加载模型: {model_path}")
    model = YOLO(model_path)

    # 检查源文件夹
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"警告: 文件夹 {source_dir} 不存在")
        print("将使用示例图像进行演示")
        source_dir = "https://ultralytics.com/images/bus.jpg"

    # 执行批量检测
    print(f"批量检测: {source_dir}")
    results = model(source_dir, conf=conf, save=save)

    # 统计结果
    all_detections = []
    total_objects = 0

    for idx, result in enumerate(results):
        boxes = result.boxes
        if boxes is not None:
            num_objects = len(boxes)
            total_objects += num_objects

            # 收集检测结果
            detections = {
                'image': str(result.path) if hasattr(result, 'path') else f'image_{idx}',
                'num_objects': num_objects,
                'objects': []
            }

            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()

                detections['objects'].append({
                    'class': model.names[cls],
                    'confidence': conf,
                    'bbox': xyxy
                })

            all_detections.append(detections)
            print(f"图像 {idx + 1}: 检测到 {num_objects} 个目标")

    # 导出JSON结果
    if export_json and all_detections:
        output_dir = Path("runs/detect")
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "batch_results.json"

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_detections, f, indent=2, ensure_ascii=False)

        print(f"\nJSON结果已保存到: {json_path}")

    print(f"\n总计: 处理了 {len(results)} 张图像, 检测到 {total_objects} 个目标")
    return results, all_detections


if __name__ == "__main__":
    print("=" * 50)
    print("批量检测示例")
    print("=" * 50)

    # 批量检测
    results, detections = batch_detect()

    # 打印详细结果
    print("\n详细结果:")
    for detection in detections:
        print(f"\n图像: {detection['image']}")
        for obj in detection['objects']:
            print(f"  - {obj['class']}: {obj['confidence']:.2f}")
