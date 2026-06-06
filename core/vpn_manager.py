import subprocess
import os
import sys
import json
import base64
import urllib.parse  # <--- Та самая библиотека для парсинга URL


class VPNManager:
    def __init__(self, vpn_key):
        self.process = None
        self.vpn_key = vpn_key
        self.bin_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'vpn', 'xray.exe')
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'vpn', 'config.json')

    def _parse_ss_key(self):
        try:
            clean_key = self.vpn_key.replace("ssconf://", "").replace("ss://", "")

            if "#" in clean_key:
                clean_key = clean_key.split("#")[0]

            clean_key = urllib.parse.unquote(clean_key)
            clean_key = clean_key.replace("-", "+").replace("_", "/")

            padding_needed = len(clean_key) % 4
            if padding_needed:
                clean_key += "=" * (4 - padding_needed)

            decoded_bytes = base64.b64decode(clean_key)
            decoded_str = decoded_bytes.decode('utf-8')

            if '@' not in decoded_str:
                print("Ошибка: Неверный формат расшифрованного ключа.")
                return False

            auth_part, server_part = decoded_str.split('@')
            method, password = auth_part.split(':', 1)
            server, port = server_part.split(':')

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