import subprocess
import os
import sys
import json
import base64
from urllib.parse import urlparse


class VPNManager:
    def __init__(self, vpn_key):
        self.process = None
        self.vpn_key = vpn_key
        # Путь к ядру Xray
        self.bin_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'vpn', 'xray.exe')
        # Путь, где будем создавать временный конфиг
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'vpn', 'config.json')

    def _parse_ss_key(self):
        """Парсит ssconf:// ключ и создает JSON конфиг для Xray"""
        try:
            # Убираем префиксы
            clean_key = self.vpn_key.replace("ssconf://", "").replace("ss://", "")

            # Отрезаем имя сервера, если оно есть (всё что после #)
            if "#" in clean_key:
                clean_key = clean_key.split("#")[0]

            # Декодируем URL-символы (например, %3D превращаем в =)
            clean_key = urllib.parse.unquote(clean_key)

            # Конвертируем URL-safe Base64 в стандартный Base64
            clean_key = clean_key.replace("-", "+").replace("_", "/")

            # Надежное восстановление паддинга (добавляем нужные знаки =)
            padding_needed = len(clean_key) % 4
            if padding_needed:
                clean_key += "=" * (4 - padding_needed)

            # Декодируем
            decoded_bytes = base64.b64decode(clean_key)
            decoded_str = decoded_bytes.decode('utf-8')

            # Разбиваем строку (формат: method:password@server:port)
            if '@' not in decoded_str:
                print("Неизвестный формат ключа после расшифровки.")
                return False

            auth_part, server_part = decoded_str.split('@')
            # maxsplit=1 нужен, если в пароле случайно окажется двоеточие
            method, password = auth_part.split(':', 1)
            server, port = server_part.split(':')

            # Формируем JSON конфиг для Xray
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

        # Пытаемся распарсить ключ и создать конфиг
        if not self._parse_ss_key():
            return False

        try:
            # Запускаем Xray с нашим сгенерированным конфигом
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

            # Удаляем временный конфиг в целях безопасности
            if os.path.exists(self.config_path):
                os.remove(self.config_path)
            print("VPN успешно остановлен.")