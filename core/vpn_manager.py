import subprocess
import os
import sys
import json
import base64
import urllib.parse
import urllib.request  # <--- Добавили модуль для скачивания динамических ключей


class VPNManager:
    def __init__(self, vpn_key):
        self.process = None
        self.vpn_key = vpn_key
        self.bin_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'vpn', 'xray.exe')
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'vpn', 'config.json')

    def _parse_ss_key(self):
        try:
            # --- ЛОГИКА ДЛЯ ДИНАМИЧЕСКИХ КЛЮЧЕЙ (ДЯДЯ ВАНЯ / OUTLINE) ---
            if self.vpn_key.startswith("ssconf://"):
                # Превращаем ssconf в обычную ссылку
                url = self.vpn_key.replace("ssconf://", "https://")
                if "#" in url:
                    url = url.split("#")[0]

                print("Скачиваем актуальный конфиг с сервера VPN...")

                # Притворяемся обычным браузером и скачиваем настройки
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))

                server = data.get("server")
                port = data.get("server_port")
                method = data.get("method")
                password = data.get("password")

                if not all([server, port, method, password]):
                    print("Ошибка: Провайдер вернул пустой или неполный конфиг.")
                    return False

            # --- ЛОГИКА ДЛЯ ОБЫЧНЫХ КЛЮЧЕЙ СТАТИЧНОГО SHADOWSOCKS ---
            else:
                clean_key = self.vpn_key.replace("ss://", "")
                if "#" in clean_key:
                    clean_key = clean_key.split("#")[0]

                # Формат SIP002: base64(method:password)@server:port
                if "@" in clean_key and not clean_key.endswith("="):
                    auth_b64, server_part = clean_key.split("@", 1)
                    pad = len(auth_b64) % 4
                    if pad: auth_b64 += "=" * (4 - pad)
                    auth_part = base64.b64decode(auth_b64).decode('utf-8')
                    method, password = auth_part.split(':', 1)
                    server, port = server_part.split(':')
                else:
                    clean_key = urllib.parse.unquote(clean_key)
                    clean_key = clean_key.replace("-", "+").replace("_", "/")
                    pad = len(clean_key) % 4
                    if pad: clean_key += "=" * (4 - pad)
                    decoded_str = base64.b64decode(clean_key).decode('utf-8')
                    auth_part, server_part = decoded_str.split('@')
                    method, password = auth_part.split(':', 1)
                    server, port = server_part.split(':')

            # --- СОБИРАЕМ ФИНАЛЬНЫЙ КОНФИГ ДЛЯ XRAY ---
            config = {
                "inbounds": [{
                    "port": 10808,
                    "listen": "127.0.0.1",
                    "protocol": "socks",
                    "settings": {"udp": True}
                }],
                "outbounds": [{
                    "protocol": "shadowsocks",
                    "settings": {
                        "servers": [{
                            "address": server,
                            "port": int(port),
                            "method": method,
                            "password": password
                        }]
                    }
                }]
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            return True
        except Exception as e:
            print(f"Ошибка расшифровки ключа: {e}")
            return False

    def start(self):
        if self.process:
            return True

        if not self.vpn_key:
            print("Ошибка: Ключ VPN отсутствует в .env")
            return False

        if not self._parse_ss_key():
            return False

        try:
            args = ["-config", self.config_path]

            self.process = subprocess.Popen(
                [self.bin_path] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=0x08000000 if sys.platform == 'win32' else 0
            )
            return True
        except Exception as e:
            print(f"Ошибка запуска VPN: {e}")
            return False

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

            if os.path.exists(self.config_path):
                os.remove(self.config_path)
            print("VPN успешно остановлен.")