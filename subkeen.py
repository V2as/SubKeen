#!/usr/bin/env python3
import urllib.request
from urllib.parse import urlparse, parse_qs
import ssl
import base64
import json
from typing import Tuple
import subprocess
import os
import argparse
import sys
xkeen_outbound_path = "/opt/etc/xray/configs/04_outbounds.json"
cron_comment = "# subkeen_cron"

def decode_base64(data: str) -> str:
    clean_data = data.strip().replace("\n", "")
    decoded_bytes = base64.b64decode(clean_data)
    return decoded_bytes.decode("utf-8", errors="replace")

def parse_xray_sub(sub_url: str) -> Tuple[str, int]:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    request = urllib.request.Request(sub_url, method="GET")
    with urllib.request.urlopen(request, context=ctx) as response:
        headers = dict(response.getheaders())
        body = response.read().decode(errors="replace")

    update_interval = int(headers.get("profile-update-interval"))
    xray_url = decode_base64(body).split("\n")[0]

    return xray_url, update_interval

def parse_xray_url(xray_url: str) -> dict:
    default_url = xray_url.replace("vless://", "http://", 1)
    urlData = urlparse(default_url)
    queryData = parse_qs(urlData.query)
    security = queryData["security"][0]

    if security == "reality":
        securitySettingsName = "realitySettings"
        securitySettingsData = {
                "fingerprint": queryData["fp"][0],
                "publicKey": queryData["pbk"][0],
                "serverName": queryData["sni"][0],
                "shortId": queryData["sid"][0]
            }
    elif security == "tls":
        securitySettingsName = "tlsSettings"
        tlsSettingsData = {}

        if "serverName" in queryData: tlsSettingsData["serverName"] = queryData["serverName"][0]
        if "sni" in queryData: tlsSettingsData["serverName"] = queryData["sni"][0]
        if "alpn" in queryData: tlsSettingsData["alpn"] = queryData["alpn"][0]
        if "minVersion" in queryData: tlsSettingsData["minVersion"] = queryData["minVersion"][0]
        if "maxVersion" in queryData: tlsSettingsData["maxVersion"] = queryData["maxVersion"][0]
        if "cipherSuites" in queryData: tlsSettingsData["cipherSuites"] = queryData["cipherSuites"][0]
        if "certificates" in queryData: tlsSettingsData["certificates"] = queryData["certificates"][0]
        if "disableSessionResumption" in queryData: tlsSettingsData["disableSessionResumption"] = queryData["disableSessionResumption"][0].lower() == "true"
        if "disableSystemRoot" in queryData: tlsSettingsData["disableSystemRoot"] = queryData["disableSystemRoot"][0].lower() == "true"
        if "disableOCSPStapling" in queryData: tlsSettingsData["disableOCSPStapling"] = queryData["disableOCSPStapling"][0].lower() == "true"
        if "allowInsecure" in queryData: tlsSettingsData["allowInsecure"] = queryData["allowInsecure"][0].lower() == "true"
        if "rejectedHandshake" in queryData: tlsSettingsData["rejectedHandshake"] = queryData["rejectedHandshake"][0]
        if "psk" in queryData: tlsSettingsData["psk"] = queryData["psk"][0]
        if tlsSettingsData == {}:
            tlsSettingsData = {

  "allowInsecure": False,
  "alpn": [
            "http/1.1"
          ]
}
        securitySettingsData = tlsSettingsData
    else:
        securitySettingsName = "realitySettings"
        securitySettingsData = {
            "fingerprint": queryData["fp"][0],
            "publicKey": queryData["pbk"][0],
            "serverName": queryData["sni"][0],
            "shortId": queryData["sid"][0]
        }
    network = queryData["type"][0]

    if network == "tcp":
        connectSettingsName = "tcpSettings"
        connectSettingsData = {}

    elif network == "xhttp":
        connectSettingsName = "xhttpSettings"
        connectSettingsData = {"path": queryData["path"][0]}

    elif network == "grpc":
        connectSettingsName = "grpcSettings"
        connectSettingsData = {}

    elif network == "ws":
        connectSettingsName = "wsSettings"

        connectSettingsData = {
            "host": queryData["host"][0],
            "path": queryData["path"][0]}

    else:
        connectSettingsName = "tcpSettings"
        connectSettingsData = {}

    protocol = xray_url.split('://')[0]
    print(queryData, urlData)
    cfg = {
        "protocol": protocol,
        "settings": {
            "vnext": [
                {
                    "address": urlData.hostname,
                    "port": int(urlData.port),
                    "users": [
                        {
                            "encryption": "none",

                            "id": urlData.username
                        }
                    ]
                }
            ]
        },
        "streamSettings" : {
            "network": queryData["type"][0],
            securitySettingsName : securitySettingsData,
            "security": queryData["security"][0],
            connectSettingsName : connectSettingsData
        },
        "tag": "vless-reality"
    }
    try:
        cfg["settings"]["vnext"][0]["users"][0]["flow"] = queryData["flow"][0]
    except: pass

    return cfg

def setup_cron(sub_url: str, update_interval: int):
    """
    Добавляет или обновляет cron-задачу, которая выполняет subkeen каждые update_interval часов.

    :param sub_url: URL для передачи в subkeen
    :param update_interval: интервал в часах
    """
    # 1. Получаем текущие записи crontab
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    lines = result.stdout.splitlines() if result.returncode == 0 else []

    # 2. Удаляем старые строки с нашим комментарием
    lines = [line for line in lines if cron_comment not in line]

    # 3. Формируем новую строку для cron
    hours = update_interval
    # Используем команду subkeen вместо python скрипта
    cron_cmd = f"0 */{hours} * * * subkeen -url {sub_url} {cron_comment}"
    lines.append(cron_cmd)

    # 4. Сохраняем все строки в временный файл
    cron_text = "\n".join(lines) + "\n"
    temp_file = "/tmp/cron_temp.txt"
    with open(temp_file, "w") as f:
        f.write(cron_text)

    # 5. Обновляем crontab
    proc = subprocess.run(["crontab", temp_file])
    if proc.returncode == 0:
        print(f"Cron успешно установлен: обновление каждые {update_interval} часов.")
    else:
        print("Не удалось обновить cron.")

def update_xkeen_outbounds(sub_url: str):
    black_list = {"vless-reality"}

    xray_url, update_interval = parse_xray_sub(sub_url)
    xrayData = parse_xray_url(xray_url)

    with open(xkeen_outbound_path, 'r') as file:
        outbound_data = json.load(file)

    outbound_data["outbounds"] = [
        obj for obj in outbound_data['outbounds']
        if obj.get('tag') not in black_list
    ]
    outbound_data["outbounds"].append(xrayData)

    with open(xkeen_outbound_path, 'w') as file:
        file.write(json.dumps(outbound_data, indent=4))

    try:
        subprocess.run(["xkeen", "-restart"], check=True)
        print("xkeen успешно перезапущен.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при перезапуске xkeen: {e}")

    setup_cron(sub_url, update_interval)

def main():
    parser = argparse.ArgumentParser(
        description="сабкин) добавляй свою подписку в xkeen"
    )
    parser.add_argument("-url", type=str, help="URL подписки Xray VLESS/REALITY")
    parser.add_argument("--version", action="store_true", help="Показать версию")
    parser.add_argument("--update", action="store_true", help="Обновить сабкин (не работает)")

    args = parser.parse_args()

    if args.version:
        print("сабкин) v1.0")
        sys.exit(0)
    if args.url:
        update_xkeen_outbounds(args.url)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()



