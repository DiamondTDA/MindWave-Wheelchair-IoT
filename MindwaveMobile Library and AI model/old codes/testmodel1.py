import serial, select
import time
import datetime
import os
import pandas as pd
import numpy as np
from joblib import dump, load
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from collections import deque
from scipy.signal import find_peaks
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
smoothing_windows = 3

WINDOW_SIZE_BLINK = 512
OVERLAP_BLINK = 0.5
STEP_BLINK = int(WINDOW_SIZE_BLINK * (1 - OVERLAP_BLINK))
BLINK_THRESHOLD = 1200
MIN_DISTANCE = 260
COOLDOWN_SEC_BLINK = 0.6
DOUBLE_BLINK_MAX_GAP = 1.1

raw_buffer = deque(maxlen=WINDOW_SIZE_BLINK)
sample_counter = 0

last_blink_time = 0
previous_blink_time = None
blink_counter = 0

window_buffer = deque(maxlen=WINDOW_SIZE)
probaillity_buffer = deque(maxlen=smoothing_windows)

baud_rate = 57600
serial_port = '/dev/rfcomm0'

pipline = load("model.joblib")  # load model file
model = pipline['model']    #from dict access model
scaler = pipline['scaler']  #from dict access scaler
features = ["attention","meditation","delta","theta","low_alpha","high_alpha","low_beta","high_beta","low_gamma","mid_gamma"]

task_to_class = {
    0 :"forward",
    1 :"backward",
    2 :"noaction",
    3 :"stop",
    4 :"right",
    5 :"left",
    6 :"No command"
}
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

def parse_payload(payload):
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

			# if code == POOR_SIGNAL:
			# state["poor_signal"] = value

			if code == ATTENTION:
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
			if code == RAW_VALUE and len(value) >= 2:
				global raw_buffer
				global last_blink_time
				global previous_blink_time
				global sample_counter
				global blink_counter
				raw = value[0] * 256 + value[1]
				if raw >= 32768:
					 raw -= 65536
				raw_buffer.append(raw)
				sample_counter +=1
				if len(raw_buffer) >= WINDOW_SIZE_BLINK and sample_counter >= STEP_BLINK:
					data_array = np.array(raw_buffer)
					peaks,_ = find_peaks(data_array,height=BLINK_THRESHOLD,distance=MIN_DISTANCE)
					now = time.time()
					if len(peaks) > 0 and (now - last_blink_time) >= COOLDOWN_SEC_BLINK:
						if previous_blink_time is None:
							previous_blink_time = now
							blink_counter = 1
						else:
							if (now - previous_blink_time) <= DOUBLE_BLINK_MAX_GAP:
								blink_counter +=1
						last_blink_time = now
					sample_counter = 0
				if previous_blink_time is not None:
					elapsed = time.time() - previous_blink_time
					if elapsed > DOUBLE_BLINK_MAX_GAP:
						if blink_counter == 1:
							print("Single Blink Detected")
						elif blink_counter >=2:
							print("Double Blink Detected")
						previous_blink_time = None
						blink_counter = 0

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
					features_df = pd.DataFrame([mean_state],columns=features)
					scaled_features = scaler.transform(features_df)
					prob = model.predict_proba(scaled_features)[0]
					probaillity_buffer.append(prob)
					if len(probaillity_buffer) >= smoothing_windows:
						smoothing_proba = np.mean(np.array(probaillity_buffer),axis=0)
						smoothed_command = np.argmax(smoothing_proba)
						threshold = 0.7
						if smoothing_proba[smoothed_command] >=threshold:
							print("Predicted Command",task_to_class[smoothed_command])
							print("Probabillity : ",np.max(smoothing_proba))
						
						
					
					
					
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

state = {
	"attention": 0,
	"meditation": 0,
	"delta": 0,
	"theta": 0,
	"low_alpha": 0,
	"high_alpha": 0,
	"low_beta": 0,
	"high_beta": 0,
	"low_gamma": 0,
	"mid_gamma" : 0
}

try:
	ser = serial.Serial(serial_port, baud_rate, timeout= 2)
	ser.reset_input_buffer()
	ser.reset_output_buffer()
	print("connected succesfuly")

	while ser.is_open:
		payload = read_packet(ser)
		if payload:
			parse_payload(payload)
except KeyboardInterrupt:
	print("\nInterrupt received! Cleaning up...")

except serial.SerialException as e:
	print('Serial error:', e)
finally:
	if ser.is_open:
		ser.close()
		print("Serial port closed successfully.")


