"""
数据集准备脚本
修正 train.txt 路径并划分训练集和验证集
"""

import random
from pathlib import Path
from typing import List, Tuple


def fix_train_txt_paths(train_txt_path: Path,
                        output_path: Path,
                        old_prefix: str = "./yolo_person_train/anno/",
                        new_prefix: str = "anno/") -> int:
    """
    修正 train.txt 中的路径格式

    Args:
        train_txt_path: 原始 train.txt 路径
        output_path: 输出文件路径
        old_prefix: 旧的路径前缀
        new_prefix: 新的路径前缀

    Returns:
        修正的行数
    """
    print(f"读取文件: {train_txt_path}")

    with open(train_txt_path, 'r') as f:
        lines = f.readlines()

    fixed_lines = []
    fixed_count = 0

    for line in lines:
        line = line.strip()
        if line.startswith(old_prefix):
            # 修正路径
            fixed_line = line.replace(old_prefix, new_prefix, 1)
            fixed_lines.append(fixed_line)
            fixed_count += 1
        else:
            fixed_lines.append(line)

    # 写入修正后的文件
    with open(output_path, 'w') as f:
        f.write('\n'.join(fixed_lines))

    print(f"修正完成: {fixed_count} 行路径已更新")
    print(f"保存到: {output_path}")

    return fixed_count


def split_dataset(image_list: List[str],
                  val_ratio: float = 0.2,
                  seed: int = 42) -> Tuple[List[str], List[str]]:
    """
    划分训练集和验证集

    Args:
        image_list: 图片路径列表
        val_ratio: 验证集比例
        seed: 随机种子

    Returns:
        (训练集列表, 验证集列表)
    """
    random.seed(seed)

    # 打乱数据
    shuffled_list = image_list.copy()
    random.shuffle(shuffled_list)

    # 计算划分点
    val_size = int(len(shuffled_list) * val_ratio)

    val_list = shuffled_list[:val_size]
    train_list = shuffled_list[val_size:]

    return train_list, val_list


def prepare_yolo_person_dataset(dataset_root: str = "datasets/yolo_person_train",
                                val_ratio: float = 0.2):
    """
    准备 YOLO Person 数据集

    Args:
        dataset_root: 数据集根目录
        val_ratio: 验证集比例
    """
    dataset_path = Path(dataset_root)
    anno_path = dataset_path / "anno"

    # 原始 train.txt
    original_train_txt = anno_path / "train.txt"

    # 备份原始文件
    backup_path = anno_path / "train.txt.backup"
    if not backup_path.exists():
        print(f"备份原始文件到: {backup_path}")
        import shutil
        shutil.copy2(original_train_txt, backup_path)

    # 1. 修正路径
    print("\n=== 步骤 1: 修正路径格式 ===")
    temp_fixed_txt = anno_path / "train_fixed.txt"
    fixed_count = fix_train_txt_paths(
        original_train_txt,
        temp_fixed_txt,
        old_prefix="./yolo_person_train/anno/",
        new_prefix="anno/"
    )

    # 2. 读取修正后的文件
    with open(temp_fixed_txt, 'r') as f:
        all_images = [line.strip() for line in f if line.strip()]

    print(f"\n总样本数: {len(all_images)}")

    # 3. 划分训练集和验证集
    print(f"\n=== 步骤 2: 划分训练集和验证集 (验证集比例: {val_ratio*100}%) ===")
    train_images, val_images = split_dataset(all_images, val_ratio=val_ratio)

    print(f"训练集: {len(train_images)} 张")
    print(f"验证集: {len(val_images)} 张")

    # 4. 验证图片和标签是否存在
    print("\n=== 步骤 3: 验证数据完整性 ===")
    missing_images = 0
    missing_labels = 0

    for img_path_str in train_images[:100]:  # 只检查前100个
        img_path = dataset_path / img_path_str
        label_path = dataset_path / \
            img_path_str.replace('images', 'labels').replace('.jpg', '.txt')

        if not img_path.exists():
            missing_images += 1
        if not label_path.exists():
            missing_labels += 1

    if missing_images > 0 or missing_labels > 0:
        print(f"⚠️  警告: 发现缺失文件（前100个样本检查）")
        print(f"   缺失图片: {missing_images}")
        print(f"   缺失标签: {missing_labels}")
    else:
        print("✓ 数据完整性检查通过（前100个样本）")

    # 5. 保存新的训练集和验证集文件
    print("\n=== 步骤 4: 保存文件 ===")

    train_txt = anno_path / "train.txt"
    val_txt = anno_path / "val.txt"

    with open(train_txt, 'w') as f:
        f.write('\n'.join(train_images))
    print(f"✓ 训练集保存到: {train_txt}")

    with open(val_txt, 'w') as f:
        f.write('\n'.join(val_images))
    print(f"✓ 验证集保存到: {val_txt}")

    # 删除临时文件
    temp_fixed_txt.unlink()

    print("\n" + "="*50)
    print("数据集准备完成！")
    print("="*50)
    print(f"\n现在可以使用以下命令训练模型:")
    print(f"python scripts/train_model.py")
    print(f"\n或者指定配置文件:")
    print(f"python scripts/train_model.py --data configs/dataset.yaml")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="准备 YOLO Person 数据集")
    parser.add_argument(
        "--dataset-root",
        type=str,
        default="datasets/yolo_person_train",
        help="数据集根目录"
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.2,
        help="验证集比例 (0.0-1.0)"
    )

    args = parser.parse_args()

    prepare_yolo_person_dataset(
        dataset_root=args.dataset_root,
        val_ratio=args.val_ratio
    )
