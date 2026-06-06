import ctypes
import sys
import os


# --- БЛОК ЗАПРОСА ПРАВ АДМИНИСТРАТОРА ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if not is_admin():
    print("Запрос прав администратора...")
    # Перезапускаем этот же скрипт, но с запросом UAC
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()
# ----------------------------------------

import customtkinter as ctk
from dotenv import load_dotenv
from core.dpi_manager import DPIManager
from core.vpn_manager import VPNManager

load_dotenv()
VPN_KEY = os.getenv("VPN_KEY")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VPN & DPI Bypass Ultimate")
        self.geometry("400x500")
        self.resizable(False, False)

        self.dpi = DPIManager()
        self.vpn = VPNManager(VPN_KEY)

        self.label_title = ctk.CTkLabel(self, text="DPI & VPN Control", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_title.pack(pady=(20, 10))

        self.label_status = ctk.CTkLabel(self, text="Статус: Отключено", text_color="red", font=ctk.CTkFont(size=14))
        self.label_status.pack(pady=5)

        self.switch_dpi = ctk.CTkSwitch(self, text="Обход DPI (Zapret - YouTube/Discord)")
        self.switch_dpi.pack(pady=(30, 10), padx=20, anchor="w")

        self.switch_vpn = ctk.CTkSwitch(self, text="VPN (Shadowsocks - Полный обход)")
        self.switch_vpn.pack(pady=10, padx=20, anchor="w")

        self.btn_connect = ctk.CTkButton(self, text="ПОДКЛЮЧИТЬ", command=self.toggle_connection, height=40)
        self.btn_connect.pack(pady=40)

        key_preview = VPN_KEY[:15] + "..." if VPN_KEY else "Ключ не найден"
        self.label_key = ctk.CTkLabel(self, text=f"Текущий ключ: {key_preview}", text_color="gray",
                                      font=ctk.CTkFont(size=10))
        self.label_key.pack(side="bottom", pady=10)

        self.is_connected = False

    def toggle_connection(self):
        if not self.is_connected:
            dpi_success = True
            vpn_success = True

            if self.switch_dpi.get():
                dpi_success = self.dpi.start()

            if self.switch_vpn.get():
                vpn_success = self.vpn.start()

            if dpi_success and vpn_success:
                self.label_status.configure(text="Статус: Подключено", text_color="green")
                self.btn_connect.configure(text="ОТКЛЮЧИТЬ", fg_color="red")
                self.switch_dpi.configure(state="disabled")
                self.switch_vpn.configure(state="disabled")
                self.is_connected = True
        else:
            self.dpi.stop()
            self.vpn.stop()

            self.label_status.configure(text="Статус: Отключено", text_color="red")
            self.btn_connect.configure(text="ПОДКЛЮЧИТЬ", fg_color=['#3a7ebf', '#1f538d'])
            self.switch_dpi.configure(state="normal")
            self.switch_vpn.configure(state="normal")
            self.is_connected = False

    def destroy(self):
        if hasattr(self, 'dpi'):
            self.dpi.stop()
        if hasattr(self, 'vpn'):
            self.vpn.stop()
        super().destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()