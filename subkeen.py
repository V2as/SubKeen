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
    if queryData["security"][0] == "reality":
        securitySettingsName = "realitySettings"
    else:
        securitySettingsName = "realitySettings"
    if queryData["type"][0] == "tcp":
        connectSettingsName = "tcpSettings"
    else:
        connectSettingsName = "tcpSettings"

    protocol = xray_url.split('://')[0]

    return {
        "protocol": protocol,
        "settings": {
            "vnext": [
                {
                    "address": urlData.hostname,
                    "port": int(urlData.port),
                    "users": [
                        {
                            "encryption": "none",
                            "flow": queryData["flow"][0],
                            "id": urlData.username
                        }
                    ]
                }
            ]
        },
        "streamSettings" : {
            "network": queryData["type"][0],
            securitySettingsName : {
                "fingerprint": queryData["fp"],
                "publicKey": queryData["pbk"],
                "serverName": queryData["sni"],
                "shortId": queryData["sid"]
            },
            "security": queryData["security"][0],
            connectSettingsName : {

            }
        },
        "tag": "vless-reality"
    }

def setup_cron(sub_url: str, update_interval: int):
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    lines = result.stdout.splitlines() if result.returncode == 0 else []
    lines = [line for line in lines if cron_comment not in line]

    hours = update_interval
    cron_cmd = f"0 */{hours} * * * /usr/bin/python3 {os.path.abspath(__file__)} -url {sub_url} {cron_comment}"
    lines.append(cron_cmd)
    cron_text = "\n".join(lines) + "\n"

    proc = subprocess.run(["crontab"], input=cron_text, text=True)
    if proc.returncode == 0:
        print(f"Cron set to update every {update_interval} hours.")
    else:
        print("Failed to update cron.")

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



