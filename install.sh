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

ln -sfn "$SUBKEEN_DIR" /opt/sbin/SubKeen-current

mkdir -p /opt/bin

WRAPPER="/opt/bin/subkeen"
echo "#!/bin/sh" > "$WRAPPER"
echo "python3 /opt/sbin/SubKeen-current/subkeen.py \"\$@\"" >> "$WRAPPER"
chmod +x "$WRAPPER"

echo "Установка завершена!"

if ! echo "$PATH" | grep -q "/opt/bin"; then
    echo "export PATH=\$PATH:/opt/bin" >> ~/.profile
    echo "Добавьте /opt/bin в PATH или перезайдите в терминал"
fi

echo "Установка завершена! Введи subkeen -url https://твоя-сабка.ru"
