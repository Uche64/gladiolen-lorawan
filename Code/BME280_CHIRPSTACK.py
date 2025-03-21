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
devaddr = bytearray([0x01, 0x54, 0x78, 0x0C])
nwkey = bytearray([
    0xE3, 0xB0, 0x39, 0x08, 0xEE, 0xC6, 0xEA, 0x53,
    0x1A, 0xF1, 0x0A, 0xB8, 0xBD, 0x63, 0x49, 0x14])
app = bytearray([
    0xC1, 0xD8, 0xCF, 0x67, 0x74, 0xC4, 0x99, 0x5F,
    0xF6, 0x54, 0x50, 0x27, 0x81, 0xBD, 0xD4, 0x12])

# --- Initialize LoRa and TTN session ---
chirpstack_config = TTN(devaddr, nwkey, app, country='EU')
lora = TinyLoRa(spi, cs, irq, rst, chirpstack_config)

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
        print("Sending packet to ChirpStack...")
        lora.send_data(data, len(data), lora.frame_counter)
        print("Packet sent successfully!")

        # --- Increment frame counter to avoid duplicates ---
        lora.frame_counter += 1

        # --- Wait before next reading ---
        print(f"Waiting {interval} seconds before next transmission...")
        time.sleep(interval)

except KeyboardInterrupt:
    print("\nTransmission stopped by user. Exiting...")

