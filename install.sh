#!/bin/sh

# URL последней версии subkeen.py
url="https://raw.githubusercontent.com/V2as/SubKeen/main/subkeen.py"

# Папка для установки
INSTALL_DIR="/opt/sbin/SubKeen-current"
BIN_DIR="/opt/bin"

# Проверяем наличие Python3
if ! command -v python3 >/dev/null 2>&1; then
    echo "Python3 не найден, устанавливаем..."
    if [ "$(id -u)" -ne 0 ]; then
        echo "Запустите скрипт от root для установки Python3"
        exit 1
    fi
    opkg update
    opkg install python3 python3-pip -y
else
    echo "Python3 уже установлен, пропускаем установку"
fi

# Создаем папки, если их нет
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Скачиваем subkeen.py
echo "Скачиваем subkeen.py..."
if ! curl -o "$INSTALL_DIR/subkeen.py" -L "$url"; then
    echo "Ошибка: не удалось скачать subkeen.py"
    exit 1
fi

# Делаем файл исполняемым
chmod +x "$INSTALL_DIR/subkeen.py"

# Создаем wrapper для команды subkeen
WRAPPER="$BIN_DIR/subkeen"
echo "#!/bin/sh" > "$WRAPPER"
echo "python3 $INSTALL_DIR/subkeen.py \"\$@\"" >> "$WRAPPER"
chmod +x "$WRAPPER"

# Добавляем /opt/bin в PATH, если его там нет
if ! echo "$PATH" | grep -q "/opt/bin"; then
    echo "export PATH=\$PATH:/opt/bin" >> ~/.profile
    echo "Добавьте /opt/bin в PATH или перезайдите в терминал"
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
RESET='\033[0m'

echo -e "${GREEN}Установка завершена!${RESET}"
echo -e "${CYAN}Теперь команда ${YELLOW}subkeen${CYAN} доступна глобально.${RESET}"
echo -e "${MAGENTA}Пример запуска: ${BLUE}subkeen -url https://твоя-сабка.ru${RESET}"
echo -e "${RED}Не забудьте, если PATH не обновился, перезайдите в терминал.${RESET}"