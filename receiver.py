#!/usr/bin/env python3
"""
==============================================
  Seri Port & CAN Haberleşme Testi - ALICI
==============================================
"""

import sys
import time
from datetime import datetime
import can
import serial

# Renk kodları
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PORTLAR = {
    "1": ("serial", "/dev/COM1", "COM1 - RS-232"),
    "2": ("serial", "/dev/COM2", "COM2 - RS-232"),
    "3": ("serial", "/dev/COM3", "COM3 - RS-485"),
    "4": ("serial", "/dev/COM4", "COM4 - RS-485"),
    "5": ("can",    "can1",      "CAN1"),
    "6": ("can",    "can2",      "CAN2"),
}

def port_sec():
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════╗
║   SERİ PORT & CAN HABERLEŞME TESTİ      ║
║   ALICI                                 ║
╚══════════════════════════════════════════╝{RESET}

  Alıcı port seçin:

    {YELLOW}1{RESET} → COM1 (/dev/COM1) - RS-232
    {YELLOW}2{RESET} → COM2 (/dev/COM2) - RS-232
    {YELLOW}3{RESET} → COM3 (/dev/COM3) - RS-485
    {YELLOW}4{RESET} → COM4 (/dev/COM4) - RS-485
    {YELLOW}5{RESET} → CAN1 (can1)      - CAN Bus
    {YELLOW}6{RESET} → CAN2 (can2)      - CAN Bus
""")
    while True:
        secim = input(f"  {BOLD}Seçiminiz (1-6): {RESET}").strip()
        if secim in PORTLAR:
            tip, port, isim = PORTLAR[secim]
            print(f"\n  {GREEN}✔ Seçilen port: {isim}{RESET}\n")
            return tip, port
        print(f"  {RED}Geçersiz seçim, 1-6 arasında bir değer girin.{RESET}")

# ───────────────────────────────────────────
# SERİ PORT ALICI
# ───────────────────────────────────────────
def serial_receiver(port):
    print(f"  Port     : {YELLOW}{port}{RESET}")
    print(f"  Baud Rate: 9600 | Ctrl+C: Çık\n")

    alinan_paket = 0
    son_alinan = time.time()
    bagli = False
    kesinti_bildirildi = False

    while True:
        try:
            with serial.Serial(port, 9600, timeout=1) as ser:
                if not bagli:
                    print(f"{GREEN}✔ Port açıldı: {port}{RESET}\n")
                    bagli = True
                    kesinti_bildirildi = False

                while True:
                    satir = ser.readline()
                    if satir:
                        mesaj = satir.decode("utf-8", errors="replace").strip()
                        alinan_paket += 1
                        son_alinan = time.time()
                        kesinti_bildirildi = False
                        print(f"{GREEN}  ↓ Alındı [{alinan_paket:05d}]:{RESET} {mesaj}")
                    else:
                        gecen = time.time() - son_alinan
                        if gecen > 1.5 and not kesinti_bildirildi:
                            print(f"\n{RED}⚠ VERİ GELMİYOR! Kablo çekildi mi? ({gecen:.1f}s sessizlik){RESET}")
                            kesinti_bildirildi = True

        except serial.SerialException as e:
            if bagli:
                print(f"\n{RED}✘ BAĞLANTI KESİLDİ! Kablo çekildi mi?{RESET}")
                print(f"  Hata: {e}")
                bagli = False
            print(f"{YELLOW}  ↻ Yeniden bağlanmaya çalışılıyor...{RESET}")
            time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}Test durduruldu. Toplam alınan paket: {alinan_paket}{RESET}")
            sys.exit(0)

# ───────────────────────────────────────────
# CAN ALICI
# ───────────────────────────────────────────
def can_receiver(port):
    print(f"  Arayüz   : {YELLOW}{port}{RESET}")
    print(f"  Protokol : CAN Bus | Sadece ID:0x100 Bekleniyor... | Ctrl+C: Çık\n")

    alinan_paket = 0
    son_alinan = time.time()
    kesinti_bildirildi = False

    # Filtre Tanımı: Sadece ID'si 0x100 olan Standart (11-bit) mesajları kabul et
    # can_mask: 0x7FF (tüm bitleri kontrol et demek)
    can_filtresi = [{"can_id": 0x100, "can_mask": 0x7FF, "extended": False}]

    while True:
        try:
            # Bus başlatılırken filtreyi ekliyoruz
            bus = can.interface.Bus(channel=port, interface='socketcan', can_filters=can_filtresi)
            print(f"{GREEN}✔ CAN arayüzü filtre ile açıldı: {port}{RESET}\n")

            while True:
                msg = bus.recv(timeout=1.0)
                
                if msg:
                    # Gelen mesaj bir hata çerçevesi mi kontrol et
                    if msg.is_error_frame:
                        print(f"{RED}  ! Donanımsal Hata Çerçevesi Algılandı!{RESET}")
                        continue

                    zaman = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    alinan_paket += 1
                    son_alinan = time.time()
                    kesinti_bildirildi = False
                    print(f"{GREEN}  ↓ Alındı [{alinan_paket:05d}]:{RESET} [{zaman}] ID:0x{msg.arbitration_id:03X} DATA:{msg.data}")
                else:
                    gecen = time.time() - son_alinan
                    if gecen > 1.5 and not kesinti_bildirildi:
                        print(f"\n{RED}⚠ VERİ GELMİYOR! (ID:0x100 bekleniyor...){RESET}")
                        kesinti_bildirildi = True

        except can.CanError as e:
            print(f"\n{RED}✘ CAN BAĞLANTISI KESİLDİ!{RESET} Hata: {e}")
            time.sleep(1)
            break # Veya yeniden bağlanma mantığı

        except KeyboardInterrupt:
            print(f"\n{YELLOW}Test durduruldu. Toplam alınan paket: {alinan_paket}{RESET}")
            sys.exit(0)

# ───────────────────────────────────────────
# ANA PROGRAM
# ───────────────────────────────────────────
def main():
    tip, port = port_sec()
    if tip == "serial":
        serial_receiver(port)
    elif tip == "can":
        can_receiver(port)

if __name__ == "__main__":
    main()