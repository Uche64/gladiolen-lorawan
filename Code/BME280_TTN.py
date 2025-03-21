# --- Imports ---
import time
import board
import busio
import digitalio
from adafruit_bme280.basic import Adafruit_BME280_I2C
from adafruit_tinylora.adafruit_tinylora import TTN, TinyLoRa

# --- Initialize I2C for BME280 ---
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = Adafruit_BME280_I2C(i2c, address=0x76)  # Use address from i2cdetect

# --- Optional: Set sea level pressure for accurate altitude (adjust to your location) ---
bme280.sea_level_pressure = 1013.25

# --- Initialize SPI for RFM95 (LoRa) ---
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# --- LoRa Pins Setup ---
cs = digitalio.DigitalInOut(board.D5)  # Chip Select (NSS)
irq = digitalio.DigitalInOut(board.D6)  # IRQ (DIO0)
rst = digitalio.DigitalInOut(board.D4)  # Reset (RST)

# --- TTN ABP Keys and DevAddr (replace with your TTN values) ---
devaddr = bytearray([0x26, 0x0B, 0x70, 0xBC])  # DevAddr
nwkey = bytearray([
    0xB1, 0xF1, 0x71, 0x47, 0x4C, 0x02, 0x2A, 0x0D,
    0x31, 0x4B, 0x6A, 0xFA, 0x07, 0x81, 0xF4, 0x46
])  # NwkSKey
app = bytearray([
    0xDB, 0x4A, 0x30, 0x05, 0x6F, 0xF9, 0x6B, 0x49,
    0x99, 0xA0, 0x5B, 0x4B, 0xF4, 0x52, 0x79, 0xD0
])  # AppSKey

# --- Initialize LoRa and TTN session ---
ttn_config = TTN(devaddr, nwkey, app, country='EU')  # Change country if needed
lora = TinyLoRa(spi, cs, irq, rst, ttn_config)

# --- Data packet buffer (6 bytes for 3 values) ---
data = bytearray(6)

# --- Function to encode float into two-byte integer (scaled by 100) ---
def encode_value(value):
    value = int(value * 10)  # Scale float to int (2 decimal places)
    return (value >> 8) & 0xFF, value & 0xFF  # High byte, Low byte

# --- Main loop ---
interval = 30  # Interval in seconds

print("Starting BME280 LoRaWAN Transmission... Press CTRL+C to stop.")

try:
    while True:
        # --- Read data from BME280 ---
        temperature = bme280.temperature  # °C
        humidity = bme280.humidity  # %
        pressure = bme280.pressure  # hPa

        # --- Debug: Print readable sensor output ---
        print(f"\nCurrent Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
        print(f"\nTemperature: {temperature:.2f} °C")
        print(f"Humidity: {humidity:.2f} %")
        print(f"Pressure: {pressure:.2f} hPa")

        # --- Encode sensor data into bytes ---
        data[0], data[1] = encode_value(temperature)
        data[2], data[3] = encode_value(humidity)
        data[4], data[5] = encode_value(pressure)

        # --- Debug: Show encoded bytes to send ---
        print(f"Encoded Data: {[hex(b) for b in data]}")

        # --- Send the data over LoRa ---
        print("Sending packet to TTN...")
        lora.send_data(data, len(data), lora.frame_counter)
        print("Packet sent successfully!")

        # --- Increment frame counter to avoid duplicates ---
        lora.frame_counter += 1

        # --- Wait before next reading ---
        print(f"Waiting {interval} seconds before next transmission...")
        time.sleep(interval)

except KeyboardInterrupt:
    print("\nTransmission stopped by user. Exiting...")
