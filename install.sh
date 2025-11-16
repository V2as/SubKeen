#!/bin/sh

url="https://github.com/V2as/SubKeen/archive/refs/tags/v.1.0.tar.gz"

if ! curl -OL "$url"; then
    if ! curl -OL "https://ghfast.top/$url"; then
        echo "Ошибка: не удалось загрузить subkeen.tar.gz"
        exit 1
    fi
fi

tar -xvzf v.1.0.tar.gz -C /opt/sbin > /dev/null
rm v.1.0.tar.gz

if [ "$(id -u)" -ne 0 ]; then
    echo "Запустите сабкина от root, это нужно чтобы установить python"
    exit 1
fi

echo "Устанавливаем python -->"
opkg update
opkg install python3 python3-pip -y

SUBKEEN_DIR=$(find /opt/sbin -maxdepth 1 -type d -name "SubKeen-*" | head -n 1)

if [ -z "$SUBKEEN_DIR" ]; then
    echo "Ошибка: папка SubKeen не найдена!"
    exit 1
fi

SCRIPT_PATH="$SUBKEEN_DIR/subkeen.py"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Файл $SCRIPT_PATH не найден!"
    exit 1
fi

echo "Копируем скрипт в /usr/local/bin/subkeen"
cp "$SCRIPT_PATH" /usr/local/bin/subkeen

chmod +x /usr/local/bin/subkeen

echo "Установка завершена! Введи subkeen -url https://твоя-сабка.ru"
