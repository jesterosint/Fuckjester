#!/data/data/com.termux/files/usr/bin/bash
# Установка fuckjester в Termux
set -e

echo "[*] Обновление пакетов..."
pkg update -y && pkg upgrade -y

echo "[*] Установка зависимостей..."
pkg install -y python unrar git clang libxml2 libxslt

echo "[*] Обновление pip..."
python -m pip install --upgrade pip wheel setuptools

echo "[*] Установка Python-зависимостей..."
pip install -r requirements.txt

echo "[*] Создание директорий..."
mkdir -p data/databases data/archives data/generated logs

echo "[*] Права на запуск..."
chmod +x fuckjester.sh

echo "[+] Установка завершена. Запуск: ./fuckjester.sh"