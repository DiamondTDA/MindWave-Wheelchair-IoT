import serial
import time

# Configuration
baud_rate = 57600
serial_port = 'COM3'
filename = 'fk.txt'
record_duration = 2  # Seconds to record

try:
    # 1. Open the port
    ser = serial.Serial(serial_port, baud_rate, timeout=3)
    
    # 2. Let the hardware settle (prevents the 'garbage' sync issue)
    print("Connecting and stabilizing...")
    time.sleep(1)
    ser.reset_input_buffer() 
    
    print(f"Recording data for {record_duration} seconds...")
    
    # 3. Capture data for exactly 2 seconds
    start_time = time.time()
    captured_data = bytearray()
    
    while (time.time() - start_time) < record_duration:
        if ser.in_waiting > 0:
            # Read whatever is available in the buffer
            captured_data.extend(ser.read(ser.in_waiting))
    
    # 4. Write to file if we got anything
    if captured_data:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(captured_data.hex(' ') + '\n')
        print(f"Success! Wrote {len(captured_data)} bytes to {filename}")
    else:
        print("No data captured. Is the headset turned on and paired?")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # 5. This is the part that fixes your 'lag' - it closes the link immediately
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Link closed. You can now safely restart or disconnect.")
