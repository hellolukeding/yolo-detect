"""
多任务视觉推理 Pipeline
支持: 行人检测 + 人脸检测 + 表情识别 + 年龄估计
"""

import cv2
import numpy as np
import torch
import torch.nn as nn
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple
from torchvision import models
from PIL import Image, ImageDraw, ImageFont

from ultralytics import YOLO

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


# ============== 模型定义 ==============
# 注意：这些类名必须与训练脚本中的类名一致

class EmotionCNN(nn.Module):
    """表情识别 CNN 模型 - 与 train_emotion.py 中定义一致"""
    def __init__(self, num_classes: int = 7):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Dropout(0.25),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Dropout(0.25),
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Dropout(0.25),
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Dropout(0.25),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512 * 3 * 3, 1024),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


class AgeEstimator(nn.Module):
    """年龄估计模型 - 基于 ResNet50"""
    def __init__(self, pretrained: bool = True):
        super().__init__()
        self.backbone = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1 if pretrained else None)
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 1)
        )

    def forward(self, x):
        return self.backbone(x).squeeze()


# ============== 数据结构 ==============


@dataclass
class Person:
    """行人检测结果"""
    bbox: List[int]          # [x1, y1, x2, y2]
    confidence: float
    face: Optional['Face'] = None


@dataclass
class Face:
    """人脸检测结果"""
    bbox: List[int]          # [x1, y1, x2, y2]
    confidence: float
    emotion: Optional[str] = None
    emotion_conf: Optional[float] = None
    age: Optional[int] = None
    age_conf: Optional[float] = None


# ============== 工具函数 ==============

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
FONT_PATH = PROJECT_ROOT / "assets" / "fonts" / "AlibabaPuHuiTi-Regular.ttf"


def cv2_add_chinese_text(img, text, position, font_size=20, color=(0, 255, 0)):
    """
    在 OpenCV 图像上添加中文文本

    Args:
        img: OpenCV 图像 (BGR 格式)
        text: 要添加的文本
        position: 位置 (x, y)
        font_size: 字体大小
        color: 颜色 (B, G, R)

    Returns:
        添加了文本的图像
    """
    # 转换为 PIL 图像
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    # 加载本地中文字体
    try:
        if FONT_PATH.exists():
            font = ImageFont.truetype(str(FONT_PATH), font_size)
        else:
            # 降级到系统字体
            font_paths = [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/simhei.ttf',
            ]
            font = None
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
            if font is None:
                font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    # 绘制文本
    draw.text(position, text, font=font, fill=color[::-1])  # PIL 使用 RGB，OpenCV 使用 BGR

    # 转换回 OpenCV 格式
    img_cv2 = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return img_cv2


class MultiTaskPipeline:
    """多任务视觉推理 Pipeline"""

    def __init__(self, config_path: str = "multitask/configs/config.yaml"):
        # 加载配置
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.device = self.config['inference']['device']
        self.imgsz = self.config['inference']['imgsz']
        self.person_conf = self.config['inference']['person_conf']
        self.face_conf = self.config['inference']['face_conf']
        self.emotions = self.config['emotions']

        # 加载模型
        self._load_models()

    def _load_models(self):
        """加载所有模型"""
        print("🔄 加载模型...")

        # 行人检测模型
        person_path = self.config['models']['person_detector']
        if Path(person_path).exists():
            self.person_detector = YOLO(person_path)
            print(f"  ✅ 行人检测模型: {person_path}")
        else:
            self.person_detector = YOLO('yolo11x.pt')  # 使用预训练模型
            print(f"  ⚠️ 使用预训练模型: yolo11x.pt")

        # 人脸检测模型
        face_path = self.config['models']['face_detector']
        if Path(face_path).exists():
            self.face_detector = YOLO(face_path)
            print(f"  ✅ 人脸检测模型: {face_path}")
        else:
            self.face_detector = None
            print(f"  ⚠️ 人脸检测模型未找到，将使用行人检测模型")

        # 表情识别模型
        emotion_path = self.config['models']['emotion_classifier']
        if Path(emotion_path).exists():
            # 添加安全全局，允许加载 EmotionCNN 类
            import __main__
            # 将当前模块的类注册到 __main__，以便加载旧模型
            __main__.EmotionCNN = EmotionCNN
            self.emotion_model = torch.load(emotion_path, map_location=self.device, weights_only=False)
            self.emotion_model.eval()
            print(f"  ✅ 表情识别模型: {emotion_path}")
        else:
            self.emotion_model = None
            print(f"  ⚠️ 表情识别模型未找到")

        # 年龄估计模型
        age_path = self.config['models']['age_estimator']
        if Path(age_path).exists():
            # 添加安全全局，允许加载 AgeEstimator 类
            import __main__
            # 将当前模块的类注册到 __main__，以便加载旧模型
            __main__.AgeEstimator = AgeEstimator
            self.age_model = torch.load(age_path, map_location=self.device, weights_only=False)
            self.age_model.eval()
            print(f"  ✅ 年龄估计模型: {age_path}")
        else:
            self.age_model = None
            print(f"  ⚠️ 年龄估计模型未找到")

        print("✅ 模型加载完成!\n")

    def detect_persons(self, image: np.ndarray) -> List[Person]:
        """检测行人"""
        results = self.person_detector.predict(
            image,
            conf=self.person_conf,
            device=self.device,
            verbose=False
        )

        persons = []
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                # 检查是否是行人类别 (0=person in COCO)
                if cls == 0 or r.names[cls] in ['person', 'pedestrian', 'rider']:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    persons.append(Person(
                        bbox=[x1, y1, x2, y2],
                        confidence=float(box.conf[0])
                    ))
        return persons

    def detect_faces(self, image: np.ndarray) -> List[Face]:
        """检测人脸"""
        if self.face_detector is None:
            return []

        results = self.face_detector.predict(
            image,
            conf=self.face_conf,
            device=self.device,
            verbose=False
        )

        faces = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                faces.append(Face(
                    bbox=[x1, y1, x2, y2],
                    confidence=float(box.conf[0])
                ))
        return faces

    def classify_emotion(self, face_image: np.ndarray) -> Tuple[str, float]:
        """识别表情"""
        if self.emotion_model is None:
            return "unknown", 0.0

        # 预处理
        face = cv2.resize(face_image, (48, 48))
        face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        face = face.astype(np.float32) / 255.0
        face = torch.from_numpy(face).unsqueeze(0).unsqueeze(0)
        face = face.to(self.device)

        # 推理
        with torch.no_grad():
            output = self.emotion_model(face)
            prob = torch.softmax(output, dim=1)
            conf, idx = torch.max(prob, dim=1)

        emotion = self.emotions[idx.item()]
        return emotion, conf.item()

    def estimate_age(self, face_image: np.ndarray) -> Tuple[int, float]:
        """估计年龄"""
        if self.age_model is None:
            return -1, 0.0

        # 预处理
        face = cv2.resize(face_image, (224, 224))
        face = face.astype(np.float32) / 255.0
        face = (face - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
        face = torch.from_numpy(face).permute(2, 0, 1).unsqueeze(0)
        face = face.float().to(self.device)  # 确保是 float32

        # 推理
        with torch.no_grad():
            output = self.age_model(face)
            age = output.item()

        return int(age), 1.0

    def process_frame(self, image: np.ndarray) -> Tuple[np.ndarray, List[Person]]:
        """处理单帧图像"""
        # 1. 检测行人
        persons = self.detect_persons(image)

        # 2. 检测人脸
        faces = self.detect_faces(image)

        # 3. 将人脸与行人关联
        for face in faces:
            fx1, fy1, fx2, fy2 = face.bbox
            face_center = ((fx1 + fx2) // 2, (fy1 + fy2) // 2)

            for person in persons:
                px1, py1, px2, py2 = person.bbox
                # 检查人脸是否在行人框内
                if px1 <= face_center[0] <= px2 and py1 <= face_center[1] <= py2:
                    # 裁剪人脸区域
                    h, w = image.shape[:2]
                    x1, y1 = max(0, fx1), max(0, fy1)
                    x2, y2 = min(w, fx2), min(h, fy2)
                    face_img = image[y1:y2, x1:x2]

                    if face_img.size > 0:
                        # 识别表情
                        if self.emotion_model:
                            emotion, conf = self.classify_emotion(face_img)
                            face.emotion = emotion
                            face.emotion_conf = conf

                        # 估计年龄
                        if self.age_model:
                            age, conf = self.estimate_age(face_img)
                            face.age = age
                            face.age_conf = conf

                    person.face = face
                    break

        # 4. 绘制结果
        result_image = self._draw_results(image, persons)

        return result_image, persons

    def _draw_results(self, image: np.ndarray, persons: List[Person]) -> np.ndarray:
        """绘制检测结果"""
        result = image.copy()

        for person in persons:
            x1, y1, x2, y2 = person.bbox

            # 绘制行人框 (蓝色)
            cv2.rectangle(result, (x1, y1), (x2, y2), (255, 0, 0), 2)
            # 使用中文绘制
            result = cv2_add_chinese_text(result, f"行人 {person.confidence:.2f}",
                                         (x1, y1 - 25), font_size=20, color=(255, 0, 0))

            # 如果有人脸，绘制人脸信息
            if person.face:
                face = person.face
                fx1, fy1, fx2, fy2 = face.bbox

                # 绘制人脸框 (绿色)
                cv2.rectangle(result, (fx1, fy1), (fx2, fy2), (0, 255, 0), 2)

                # 构建信息文本
                info_parts = []
                if face.emotion:
                    emotion_cn = EMOTION_CN.get(face.emotion, face.emotion)
                    info_parts.append(f"{emotion_cn}")
                if face.age and face.age > 0:
                    info_parts.append(f"{face.age}岁")

                if info_parts:
                    info_text = " | ".join(info_parts)
                    # 使用中文绘制
                    result = cv2_add_chinese_text(result, info_text,
                                                 (fx1, fy1 - 25), font_size=18, color=(0, 255, 0))

        return result

    def process_video(self, source, output_path: str = None, show: bool = True):
        """处理视频"""
        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            print(f"❌ 无法打开视频源: {source}")
            return

        # 获取视频信息
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # 输出视频
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        print(f"📹 处理视频: {source}")
        print(f"   分辨率: {width}x{height}, FPS: {fps}")

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 处理帧
            result_frame, persons = self.process_frame(frame)

            # 保存
            if output_path:
                out.write(result_frame)

            # 显示
            if show:
                cv2.imshow('Multi-Task Detection', result_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            frame_count += 1
            if frame_count % 30 == 0:
                print(f"   已处理 {frame_count} 帧...")

        cap.release()
        if output_path:
            out.release()
        if show:
            cv2.destroyAllWindows()

        print(f"✅ 处理完成: {frame_count} 帧")


def main():
    """测试入口"""
    import argparse

    parser = argparse.ArgumentParser(description='多任务视觉推理')
    parser.add_argument('--source', type=str, default='0', help='视频源 (0=摄像头, 或视频文件路径)')
    parser.add_argument('--output', type=str, default=None, help='输出视频路径')
    parser.add_argument('--no-show', action='store_true', help='不显示窗口')
    args = parser.parse_args()

    # 初始化 Pipeline
    pipeline = MultiTaskPipeline()

    # 处理视频
    source = 0 if args.source == '0' else args.source
    pipeline.process_video(
        source=source,
        output_path=args.output,
        show=not args.no_show
    )


if __name__ == '__main__':
    main()
