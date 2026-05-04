#!/usr/bin/env python3

"""
==============================================
  Seri Port & CAN Haberleşme Testi - GÖNDERİCİ
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
║   GÖNDERİCİ                             ║
╚══════════════════════════════════════════╝{RESET}

  Gönderici port seçin:

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
# SERİ PORT GÖNDERİCİ
# ───────────────────────────────────────────
def serial_sender(port):
    
    print(f"  Port     : {YELLOW}{port}{RESET}")
    print(f"  Baud Rate: 9600 | Aralık: 500ms | Ctrl+C: Çık\n")

    sayac = 1
    bagli = False

    while True:
        try:
            with serial.Serial(port, 9600, timeout=1) as ser:
                if not bagli:
                    print(f"{GREEN}✔ Port açıldı: {port}{RESET}\n")
                    bagli = True

                while True:
                    zaman = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    mesaj = f"[{zaman}] PAKET#{sayac:05d} | PORT:{port}"
                    ser.write((mesaj + "\n").encode("utf-8"))
                    print(f"{GREEN}  ↑ Gönderildi [{sayac:05d}]:{RESET} {mesaj}")
                    sayac += 1
                    time.sleep(0.5)

        except serial.SerialException as e:
            if bagli:
                print(f"\n{RED}✘ BAĞLANTI KESİLDİ! Kablo çekildi mi?{RESET}")
                print(f"  Hata: {e}")
                bagli = False
            print(f"{YELLOW}  ↻ Yeniden bağlanmaya çalışılıyor...{RESET}")
            time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}Test durduruldu. Toplam gönderilen paket: {sayac - 1}{RESET}")
            sys.exit(0)

# ───────────────────────────────────────────
# CAN GÖNDERİCİ
# ───────────────────────────────────────────
def can_sender(port):
    
    print(f"  Arayüz   : {YELLOW}{port}{RESET}")
    print(f"  Protokol : CAN Bus | Aralık: 500ms | Ctrl+C: Çık\n")

    sayac = 1
    bagli = False

    while True:
        try:
            bus = can.interface.Bus(channel=port, interface='socketcan')
            if not bagli:
                print(f"{GREEN}✔ CAN arayüzü açıldı: {port}{RESET}\n")
                bagli = True

            while True:
                zaman = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                # CAN mesajı: arbitration_id=0x100, 8 byte veri
                veri = f"{sayac:08d}".encode("utf-8")[:8]
                msg = can.Message(
                    arbitration_id=0x100,
                    data=veri,
                    is_extended_id=False
                )
                bus.send(msg)
                print(f"{GREEN}  ↑ Gönderildi [{sayac:05d}]:{RESET} [{zaman}] ID:0x100 DATA:{veri}")
                sayac += 1
                time.sleep(0.5)

        except can.CanError as e:
            if bagli:
                print(f"\n{RED}✘ CAN BAĞLANTISI KESİLDİ! Kablo çekildi mi?{RESET}")
                print(f"  Hata: {e}")
                bagli = False
            print(f"{YELLOW}  ↻ Yeniden bağlanmaya çalışılıyor...{RESET}")
            try:
                bus.shutdown()
            except:
                pass
            time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}Test durduruldu. Toplam gönderilen paket: {sayac - 1}{RESET}")
            try:
                bus.shutdown()
            except:
                pass
            sys.exit(0)

# ───────────────────────────────────────────
# ANA PROGRAM
# ───────────────────────────────────────────
def main():
    tip, port = port_sec()
    if tip == "serial":
        serial_sender(port)
    elif tip == "can":
        can_sender(port)

if __name__ == "__main__":
    main()