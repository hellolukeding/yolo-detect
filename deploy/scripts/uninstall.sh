#!/bin/bash
################################################################################
# YOLO 检测推流服务 - 卸载脚本
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SERVICE_NAME="yolo-streaming"
INSTALL_DIR="/opt/yolo-detect"

echo -e "${RED}========================================${NC}"
echo -e "${RED}YOLO 检测推流服务 - 卸载脚本${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 确认
echo -e "${YELLOW}警告: 此操作将：${NC}"
echo "  1. 停止并禁用系统服务"
echo "  2. 删除系统服务文件"
echo "  3. 保留项目文件（可选删除）"
echo ""
read -p "确认继续? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 停止并禁用服务
echo ""
echo -e "${YELLOW}[1/3] 停止服务...${NC}"
systemctl stop $SERVICE_NAME 2>/dev/null || true
systemctl disable $SERVICE_NAME 2>/dev/null || true

# 删除服务文件
echo -e "${YELLOW}[2/3] 删除服务文件...${NC}"
rm -f "/etc/systemd/system/$SERVICE_NAME.service"
systemctl daemon-reload

# 询问是否删除项目文件
echo -e "${YELLOW}[3/3] 项目文件...${NC}"
echo "项目文件位于: $INSTALL_DIR"
read -p "是否删除项目文件? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}项目文件已删除${NC}"
else
    echo -e "${YELLOW}项目文件已保留${NC}"
fi

echo ""
echo -e "${GREEN}卸载完成！${NC}"
