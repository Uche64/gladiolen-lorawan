from pyLoRa import LoRa, ModemConfig
import time
import board
import busio
import digitalio

# SPI pins setup
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D5)
irq = digitalio.DigitalInOut(board.D6)
rst = digitalio.DigitalInOut(board.D4)

# Initialize LoRa object
lora = LoRa(spi, cs, irq, rst, frequency=868.1, modem_config=ModemConfig.Bw125Cr45Sf128, tx_power=14)

while True:
    payload = bytes("Hello ChirpStack!", "utf-8")
    lora.send_packet(payload)
    print("Packet Sent:", payload)
    time.sleep(30)
