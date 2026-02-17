import serial, select
import time
import os
import pandas as pd

# Byte codes
SYNC                 = b'\xaa'
EXCODE               = 0x55

POOR_SIGNAL          = 0x02
ATTENTION            = 0x04
MEDITATION           = 0x05
BLINK                = 0x16

RAW_VALUE            = 0x80
ASIC_EEG_POWER       = b'\x83'	

baud_rate = 57600
serial_port = '/dev/rfcomm0'
ser = serial.Serial(serial_port, baud_rate, timeout= 2)
file = open(r'/home/pi/Downloads/MindwaveMobile/rawdata.txt', 'a', encoding='utf-8')

def Checksum(s):
    try:
        if s.read() == SYNC and s.read() == SYNC:
            # Packet found, determine plength
            while True:
                plength = ord(s.read())
                if plength != 170:
                    break
            if plength > 170:
                return None
            payload = s.read(plength)
            val = sum(payload) & 0xff
            val = (~val) & 0xff
            chksum = ord(s.read())
            if val == chksum:
                return payload
    except (OSError, serial.SerialException):
        return None

def parse_payload(payload):
    while payload:
        code = payload[0]
        payload = payload[1:]

        # Ignore EXCODE for now
        while code == EXCODE:  # EXCODE
            code = payload[0]
            payload = payload[1:]

        # Single-byte codes
        if code < 0x80:
            value = payload[0]
            payload = payload[1:]

            if code == POOR_SIGNAL:  # POOR_SIGNAL
                print("Poor signal:", value)

            elif code == ATTENTION:  # ATTENTION
                print("Attention:", value)

            elif code == MEDITATION:  # MEDITATION
                print("Meditation:", value)

            elif code == BLINK:  # BLINK
                print("Blink:", value)

        # Multi-byte codes
        else:
            vlength = payload[0]
            payload = payload[1:]

            value = payload[:vlength]
            payload = payload[vlength:]

            if code == 0x80 and len(value) >= 2:  # RAW_VALUE
                raw = value[0] * 256 + value[1]
                if raw >= 32768:
                    raw -= 65536
                #print("Raw EEG:", raw)

try:
	ser.reset_input_buffer()
	while ser.is_open:
		packet = Checksum(ser)
		parse_payload(packet)
except KeyboardInterrupt:
    print("\nInterrupt received! Cleaning up...")
finally:
    # This block runs no matter how the script stops (Ctrl+C, error, or finishing)
    ser.reset_output_buffer()
    ser.close()
    file.close()
    print("Serial port and file closed successfully.")

# def parse_payload(payload, state, csv_file):
#     while payload:
#         code = payload[0]
#         payload = payload[1:]

#         # Skip EXCODE
#         while code == EXCODE:
#             code = payload[0]
#             payload = payload[1:]

#         # Single-byte codes
#         if code < 0x80:
#             value = payload[0]
#             payload = payload[1:]

#             if code == POOR_SIGNAL:
#                 state["poor_signal"] = value

#             elif code == ATTENTION:
#                 state["attention"] = value

#             elif code == MEDITATION:
#                 state["meditation"] = value

#             elif code == BLINK:
#                 state["blink"] = value

#         # Multi-byte codes
#         else:
#             vlength = payload[0]
#             payload = payload[1:]

#             value = payload[:vlength]
#             payload = payload[vlength+1:]

#             # RAW EEG
#             if code == RAW_VALUE and len(value) >= 2:
#                 raw = value[0] * 256 + value[1]
#                 if raw >= 32768:
#                     raw -= 65536
#                 state["raw"] = raw

#                 csv_file.write(
#                     f"{time.time()},{raw},{state['attention']},{state['meditation']},{state['poor_signal']}\n"
#                 )

#             # EEG POWER BANDS
#             elif code == ASIC_EEG_POWER and len(value) >= 24:
#                 bands = {}
#                 names = [
#                     "delta","theta","low_alpha","high_alpha",
#                     "low_beta","high_beta","low_gamma","mid_gamma"
#                 ]

#                 j = 0
#                 for name in names:
#                     bands[name] = value[j]*256*256 + value[j+1]*256 + value[j+2]
#                     j += 3

#                 state["bands"] = bands

#                 csv_file.write(
#                     f"{time.time()},POWER,"
#                     + ",".join(str(bands[n]) for n in names)
#                     + "\n"
#                 )

# state = {
#     "raw": 0,
#     "attention": 0,
#     "meditation": 0,
#     "poor_signal": 200,
#     "blink": 0,
#     "bands": {}
# }

# with open("mindwave_data.csv", "w") as f:
#     f.write("timestamp,raw,attention,meditation,poor_signal\n")

#     while ser.is_open:
#         payload = read_packet(ser)
#         if payload:
#             parse_payload(payload, state, f)
