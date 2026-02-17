import serial, select
import time
import datetime
import os
import pandas as pd
import numpy as np
from collections import deque
# Byte codes
SYNC                 = b'\xaa'
EXCODE               = 0x55

POOR_SIGNAL          = 0x02
ATTENTION            = 0x04
MEDITATION           = 0x05
BLINK                = 0x16

RAW_VALUE            = 0x80
ASIC_EEG_POWER       = 0x83	
WINDOW_SIZE = 3
window_numbers = 3
current_command = ""
window_buffer = deque(maxlen=WINDOW_SIZE)
counter = 0
baud_rate = 57600
serial_port = '/dev/rfcomm0'
def read_packet(s):
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

def parse_payload(payload, csv_file,read_latency):
	proccess_start = time.perf_counter()
	global state
	while payload:
		code = payload[0]
		payload = payload[1:]

		# Skip EXCODE
		while code == EXCODE:
			code = payload[0]
			payload = payload[1:]

		# Single-byte codes
		if code < 0x80:
			value = payload[0]
			payload = payload[1:]

			if code == POOR_SIGNAL:
				state["poor_signal"] = value

			elif code == ATTENTION:
				state["attention"] = value

			elif code == MEDITATION:
				state["meditation"] = value

			# elif code == BLINK:
				# state["blink"] = value

		# Multi-byte codes
		else:
			vlength = payload[0]
			payload = payload[1:]

			value = payload[:vlength]
			payload = payload[vlength:]

			# RAW EEG
			#  if code == RAW_VALUE and len(value) >= 2:
			#      raw = value[0] * 256 + value[1]
			#      if raw >= 32768:
			#          raw -= 65536
			#      state["raw"] = raw

			#      csv_file.write(
			#          f"{time.time()},{raw},{state['attention']},{state['meditation']},{state['poor_signal']}\n"
			#      )

			# EEG POWER BANDS
			if code == ASIC_EEG_POWER and len(value) >= 24:
				names = [
				"delta","theta","low_alpha","high_alpha",
				"low_beta","high_beta","low_gamma","mid_gamma"
				]

				j = 0
				for name in names:
					state[name] = value[j]*256*256 + value[j+1]*256 + value[j+2]
					j += 3
				global window_buffer
				window_buffer.append(state.copy())
				if len(window_buffer) >= WINDOW_SIZE:
					mean_state = compute_mean(window_buffer)
					mean_state['command'] = current_command
					proccess_end = time.perf_counter()
					proccess_latency = (proccess_end - proccess_start) * 1000
					total_latency = read_latency + proccess_latency
					csv_file.write(
									f"{datetime.datetime.now()},{mean_state['attention']},{mean_state['meditation']},{mean_state['poor_signal']},{mean_state['delta']},"
									f"{mean_state['theta']},{mean_state['low_alpha']},{mean_state['high_alpha']},{mean_state['low_beta']},{mean_state['high_beta']},"
									f"{mean_state['low_gamma']},{mean_state['mid_gamma']},{read_latency},{proccess_latency},{total_latency}\n"
								 )
					file.flush()
					# window_buffer = window_buffer[1:]
					global counter
					counter+=1
					if counter >= window_numbers:
						raise EndReading("Stopping Reading after certain window numbers")
					
					
				#csv_file.write(
				#f"{time.time()},POWER,"
				#+ ",".join(str(bands[n]) for n in names)
				#+ "\n"
				#)
def compute_mean(window_buffer):
	mean_state = {}
	keys = window_buffer[0].keys()
	for key in keys:
		mean_state[key] = int(np.mean([d[key] for d in window_buffer]))
	return mean_state
def replace_or_append_file(dec,files):
	if dec == 2:
		f = read_files(files,"a")
	elif dec == 3:
		f =read_files(files,"w")
	return f
def read_files(files,mode):
	if len(files) !=0:
		readings_dict = {}
		print("Choose One of the Files to Append or Replace ")
		for index,file in enumerate(files):
			readings_dict[index+1] = file
			print(f"{index+1} : {file}")
		try:
			file_number = int(input("Choose a number of file: "))
			f = open(os.path.join(os.getcwd(),f"Readings/{readings_dict[file_number]}"),mode)
			return f
		except KeyError as e:
			print("There is no such number Try again")
	else:
		print("No Files Try again to Create New file")
	return None

file = None
state = {
	"attention": 0,
	"meditation": 0,
	"poor_signal": 200,
	"delta": 0,
	"theta": 0,
	"low_alpha": 0,
	"high_alpha": 0,
	"low_beta": 0,
	"high_beta": 0,
	"low_gamma": 0,
	"mid_gamma" : 0
}

class EndReading(Exception):
	pass
class Exit(Exception):
	pass
try:
	ser = serial.Serial(serial_port, baud_rate)
	ser.reset_input_buffer()
	ser.reset_output_buffer()
	print("connected succesfuly")

	while file is None:
		print("1) Create New File\n2) Append to a File\n3) Replace Existing file\n4)Exit")
		number = int(input("Choose Your Number of Decision : "))
		if number == 1:
			name = input("Choose the name for the File,same File Name replaces its contents: ")
			file = open(os.path.join(os.getcwd(),f"Readings/{name}.csv"),"w")
			file.write("timestamp,attention,meditation,poor_signal,delta,theta,low_alpha,high_alpha,low_beta,high_beta,low_gamma,mid_gamma,read_latency(ms),proccess_latency(ms),total_latency(ms)\n")
			print("File Created/Replaced Successfully")
		elif number == 2: #append
			Readings = os.listdir(os.path.join(os.getcwd(),"Readings"))
			file = replace_or_append_file(number,Readings)
		elif number == 3: #replace
			Readings = os.listdir(os.path.join(os.getcwd(),"Readings"))
			file = replace_or_append_file(number,Readings)
			file.write("timestamp,attention,meditation,poor_signal,delta,theta,low_alpha,high_alpha,low_beta,high_beta,low_gamma,mid_gamma,read_latency(ms),proccess_latency(ms),total_latency(ms)\n")
		else:
			raise Exit("Program exit")
	print("Window Size?")
	WINDOW_SIZE = int(input("Choose window size: "))
	print("How many Readings?")
	window_numbers = int(input("Number of Readings : "))
	print("What is Command You want to Make ?")
	current_command = input("Enter Command Name : ")
	
	while ser.is_open:
		read_start = time.perf_counter()
		payload = read_packet(ser)
		read_end = time.perf_counter()
		read_latency = (read_end - read_start) * 1000
		if payload:
			parse_payload(payload, file,read_latency)
except KeyboardInterrupt:
	print("\nInterrupt received! Cleaning up...")

except serial.SerialException as e:
	print('Serial error:', e)
except EndReading as e:
	print("End reading after certain window number")
except Exit as e:
	print("Program exit")
finally:
	if file is not None:
    # This block runs no matter how the script stops (Ctrl+C, error, or finishing)
		file.flush()
		file.close()
		print("file closed")
    
	if ser.is_open:
		ser.close()
		print("Serial port closed successfully.")


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
