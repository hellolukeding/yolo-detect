"""
YOLO 模型训练示例
训练自定义YOLO模型
"""

from pathlib import Path

from ultralytics import YOLO


def train_model(data_yaml: str = "configs/dataset.yaml",
                model: str = "yolo11n.pt",
                epochs: int = 100,
                imgsz: int = 640,
                batch: int = 16,
                name: str = "yolo_custom"):
    """
    训练YOLO模型

    Args:
        data_yaml: 数据集配置文件路径
        model: 预训练模型路径
        epochs: 训练轮数
        imgsz: 图像大小
        batch: 批次大小
        name: 实验名称
    """
    # 加载模型
    print(f"加载预训练模型: {model}")
    yolo_model = YOLO(model)

    # 检查数据配置文件
    data_path = Path(data_yaml)
    if not data_path.exists():
        print(f"错误: 数据配置文件 {data_yaml} 不存在")
        print("\n请创建数据集配置文件，格式如下:")
        print("""
# dataset.yaml
path: /path/to/dataset  # 数据集根目录
train: images/train     # 训练集路径（相对于path）
val: images/val         # 验证集路径（相对于path）
test: images/test       # 测试集路径（可选）

# 类别
names:
  0: person
  1: bicycle
  2: car
  # ... 更多类别
""")
        return None

    # 开始训练
    print(f"\n开始训练...")
    print(f"数据集: {data_yaml}")
    print(f"轮数: {epochs}")
    print(f"批次大小: {batch}")
    print(f"图像大小: {imgsz}")

    results = yolo_model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name=name,
        patience=50,           # 早停耐心值
        save=True,             # 保存检查点
        device='auto',         # 自动选择设备（GPU或CPU）
        workers=8,             # 数据加载线程数
        project='runs/train',  # 项目路径
        exist_ok=True,         # 允许覆盖现有项目
    )

    print("\n训练完成!")
    print(f"最佳模型保存在: runs/train/{name}/weights/best.pt")
    print(f"最后模型保存在: runs/train/{name}/weights/last.pt")

    return results


def validate_model(model_path: str = "runs/train/yolo_custom/weights/best.pt",
                   data_yaml: str = "configs/dataset.yaml"):
    """
    验证训练好的模型

    Args:
        model_path: 模型路径
        data_yaml: 数据集配置文件
    """
    print(f"加载模型: {model_path}")
    model = YOLO(model_path)

    print(f"验证模型...")
    results = model.val(data=data_yaml)

    print(f"\n验证结果:")
    print(f"mAP50: {results.box.map50:.4f}")
    print(f"mAP50-95: {results.box.map:.4f}")

    return results


def export_model(model_path: str = "runs/train/yolo_custom/weights/best.pt",
                 format: str = "onnx"):
    """
    导出模型到不同格式

    Args:
        model_path: 模型路径
        format: 导出格式 (onnx, torchscript, coreml, tensorflow, etc.)
    """
    print(f"加载模型: {model_path}")
    model = YOLO(model_path)

    print(f"导出模型为 {format} 格式...")
    model.export(format=format)

    print(f"导出完成!")


if __name__ == "__main__":
    # 示例1: 使用COCO8数据集进行快速测试
    print("=" * 50)
    print("示例: 使用COCO8数据集训练")
    print("=" * 50)
    print("\n这将下载COCO8示例数据集并进行训练演示")

    # 使用内置的coco8数据集进行快速测试（仅用于演示）
    train_model(
        data_yaml="coco8.yaml",  # 内置示例数据集
        model="yolo11n.pt",
        epochs=3,                # 少量epoch用于演示
        batch=8,
        name="demo_coco8"
    )

    # 示例2: 训练自定义数据集（取消注释使用）
    # train_model(
    #     data_yaml="configs/dataset.yaml",
    #     model="yolo11n.pt",
    #     epochs=100,
    #     batch=16,
    #     name="my_custom_model"
    # )

    # 示例3: 验证模型
    # validate_model()

    # 示例4: 导出模型
    # export_model(format="onnx")
