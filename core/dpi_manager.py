import subprocess
import os
import sys


class DPIManager:
    def __init__(self):
        self.process = None
        self.bin_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'zapret', 'winws.exe')
        # Получаем путь к папке zapret, чтобы процесс видел лежащие там .bin файлы
        self.work_dir = os.path.dirname(self.bin_path)

        # Усиленная стратегия обхода для ВСЕХ сайтов (без hostlist)
        self.args = [
            "--wf-tcp=80,443", "--wf-udp=443",
            "--filter-udp=443", "--dpi-desync=fake", "--dpi-desync-repeats=6",
            "--dpi-desync-fake-quic=quic_initial_www_google_com.bin", "--new",
            "--filter-tcp=443", "--dpi-desync=fake,split2", "--dpi-desync-repeats=6", "--dpi-desync-fooling=md5sig",
            "--dpi-desync-fake-tls=tls_clienthello_www_google_com.bin"
        ]

    def start(self):
        if self.process:
            return True

        try:
            self.process = subprocess.Popen(
                [self.bin_path] + self.args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.work_dir,  # <--- КРИТИЧЕСКИ ВАЖНО для загрузки .bin файлов
                creationflags=0x08000000 if sys.platform == 'win32' else 0
            )
            return True
        except Exception as e:
            print(f"Ошибка запуска Zapret: {e}")
            return False

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            print("Zapret успешно остановлен.")