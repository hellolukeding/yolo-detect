"""
年龄估计模型训练脚本
基于 WikiFace 数据集训练 CNN 回归模型
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms, models
from PIL import Image
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm


class AgeEstimator(nn.Module):
    """年龄估计模型 - 基于 ResNet50"""

    def __init__(self, pretrained: bool = True):
        super().__init__()

        # 使用 ResNet50 作为 backbone
        self.backbone = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1 if pretrained else None)

        # 替换最后的全连接层
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 1)  # 回归输出年龄
        )

    def forward(self, x):
        return self.backbone(x).squeeze()


class WikiFaceDataset(Dataset):
    """WikiFace 数据集"""

    def __init__(self, root_dir: str, csv_path: str, transform=None, max_samples: int = None):
        self.root_dir = Path(root_dir)
        self.transform = transform or transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        # 加载 CSV
        self.df = pd.read_csv(csv_path)

        # 过滤无效数据
        self.df = self.df[(self.df['age'] >= 0) & (self.df['age'] <= 100)]

        if max_samples:
            self.df = self.df.sample(n=min(max_samples, len(self.df)), random_state=42)

        print(f"  加载 {len(self.df)} 条数据")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = self.root_dir / row['path']
        age = float(row['age'])

        # 加载图片
        try:
            image = Image.open(img_path).convert('RGB')
        except:
            # 返回一个黑色图片作为 fallback
            image = Image.new('RGB', (224, 224), (0, 0, 0))

        if self.transform:
            image = self.transform(image)

        return image, age


def train_age_model(
    data_dir: str = '/opt/2026/yolo-detect/datasets/wiki',
    csv_path: str = '/opt/2026/yolo-detect/datasets/wiki/wiki_labels.csv',
    output_path: str = 'multitask/models/age_model.pt',
    epochs: int = 30,
    batch_size: int = 32,
    lr: float = 0.0001,
    max_samples: int = None,
    device: str = 'cuda'
):
    """训练年龄估计模型"""

    print("=" * 60)
    print("👶👴 年龄估计模型训练")
    print("=" * 60)

    # 数据增强
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # 加载数据集
    print("\n📂 加载数据集...")
    full_dataset = WikiFaceDataset(data_dir, csv_path, transform=train_transform, max_samples=max_samples)

    # 划分训练集和验证集
    train_size = int(0.9 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    # 验证集使用不同的 transform
    val_dataset.dataset = WikiFaceDataset(data_dir, csv_path, transform=val_transform, max_samples=max_samples)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=4)

    print(f"  训练集: {len(train_dataset)}, 验证集: {len(val_dataset)}")

    # 创建模型
    print(f"\n🔧 创建模型 (设备: {device})...")
    model = AgeEstimator(pretrained=True).to(device)

    # 损失函数和优化器
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=3, factor=0.5)

    # 训练
    best_mae = float('inf')

    print(f"\n🚀 开始训练 ({epochs} epochs)...\n")

    for epoch in range(epochs):
        # 训练阶段
        model.train()
        train_loss = 0.0
        train_mae = 0.0

        pbar = tqdm(train_loader, desc=f'Epoch {epoch+1}/{epochs} [Train]')
        for images, ages in pbar:
            images = images.to(device)
            ages = ages.to(device).float()

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, ages)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            train_mae += torch.abs(outputs - ages).sum().item()

            pbar.set_postfix({'loss': f'{loss.item():.4f}', 'MAE': f'{train_mae/len(train_dataset):.2f}'})

        train_mae = train_mae / len(train_dataset)

        # 验证阶段
        model.eval()
        val_loss = 0.0
        val_mae = 0.0

        with torch.no_grad():
            for images, ages in tqdm(val_loader, desc=f'Epoch {epoch+1}/{epochs} [Val]'):
                images = images.to(device)
                ages = ages.to(device).float()

                outputs = model(images)
                loss = criterion(outputs, ages)

                val_loss += loss.item()
                val_mae += torch.abs(outputs - ages).sum().item()

        val_mae = val_mae / len(val_dataset)
        avg_val_loss = val_loss / len(val_loader)

        print(f'\n  Epoch {epoch+1}: Train MAE: {train_mae:.2f} | Val MAE: {val_mae:.2f} | Val Loss: {avg_val_loss:.4f}')

        # 更新学习率
        scheduler.step(avg_val_loss)

        # 保存最佳模型
        if val_mae < best_mae:
            best_mae = val_mae
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            torch.save(model, output_path)
            print(f'  ✅ 保存最佳模型: {output_path} (MAE: {best_mae:.2f})')

    print("\n" + "=" * 60)
    print(f"✅ 训练完成! 最佳 MAE: {best_mae:.2f} 岁")
    print(f"📁 模型保存至: {output_path}")
    print("=" * 60)

    return model


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='训练年龄估计模型')
    parser.add_argument('--data', type=str, default='/opt/2026/yolo-detect/datasets/wiki')
    parser.add_argument('--csv', type=str, default='/opt/2026/yolo-detect/datasets/wiki/wiki_labels.csv')
    parser.add_argument('--output', type=str, default='multitask/models/age_model.pt')
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument('--batch', type=int, default=32)
    parser.add_argument('--lr', type=float, default=0.0001)
    parser.add_argument('--max-samples', type=int, default=None, help='最大样本数 (用于快速测试)')
    parser.add_argument('--device', type=str, default='cuda')

    args = parser.parse_args()

    train_age_model(
        data_dir=args.data,
        csv_path=args.csv,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch,
        lr=args.lr,
        max_samples=args.max_samples,
        device=args.device
    )
