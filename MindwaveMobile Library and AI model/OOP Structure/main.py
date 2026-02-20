import time
from Bt_manager import BTManager
from signal_reader import SignalReader
from blink_processor import BlinkProcessor
from data_collection import DataCollector
# from jaw_clench import JawClench # Placeholder for now
# from bci_ai_model import BCIModel # Placeholder for later

# ==========================================
# 1. Initiate Components & Setup Callbacks
# ==========================================
bt = BTManager()
reader = SignalReader()
blinker = BlinkProcessor()
collector = DataCollector()
# clench = JawClench() 
# model = BCIModel()

# --- THE HOOK ---
def handle_raw_data(raw_val):
    """
    Callback function triggered instantly by SignalReader whenever a 512 Hz raw packet is parsed.
    Bypasses the main loop to ensure zero delay or data loss for blink and jaw clench detection.
    """
    blink_action = blinker.process_raw(raw_val)
    # clench.process_raw(raw_val) # For future implementation
    if blink_action: # If it returns 1, 2, or 3
        print(f"\n---> BLINK DETECTED: {blink_action} <---")
        reader.state["blink"] = blink_action # Save it for the CSV

# Attach the hook to the reader
reader.on_raw_received = handle_raw_data

# ==========================================
# 2. Setup Data Collection & Main Loop
# ==========================================
target_file = collector.get_file_handle()

if target_file and bt.connect():
    current_label = input("Enter label for this session (e.g., 'F' for Forward): ")
    duration = int(input("Collection duration in seconds: "))
    
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    start_time = time.time()
    
    try:
        # Keep collecting until the requested duration is met
        while time.time() - start_time < duration:
            
            # --- Buffer Management ---
            # Prevent lag by clearing old data if the serial buffer backs up
            if bt.ser.in_waiting > 500:
                print("Buffer overflow - resetting")
                bt.ser.reset_input_buffer()
                continue

            # --- Data Processing ---
            if bt.ser.in_waiting > 0:
                # T1: Start Total Latency (Serial arrival)
                t_total_start = time.perf_counter()
                
                # Fetch a validated packet (verifies sync bytes and checksum)
                payload = reader.read_packet(bt.ser)
                
                if payload:
                    # T2: Start Logic Latency (Parsing start)
                    t_logic_start = time.perf_counter()
                    
                    # 3. Parse Data
                    # Returns the state dict ONLY if the 1Hz power packet was in this payload
                    updated_state = reader.parse_payload(payload)

                    # T3: End of processing
                    t_end = time.perf_counter()
                    
                    # Calculate Latencies (ms) for research analysis
                    total_lat = (t_end - t_total_start) * 1000
                    logic_t = (t_end - t_logic_start) * 1000

                    # 4. Collect Data 
                    # Trigger a save to CSV only when a 1 Hz power packet (0x83) finishes arriving
                    if updated_state:
                        updated_state["timestamp"] = time.strftime('%H:%M:%S')
                        collector.save_row(target_file, updated_state, current_label, total_lat, logic_t)
                        print(f"Recorded: {int(time.time() - start_time)}s", end="\r")

                        reader.state["blink"] = 0

            # 5. Movement Logic (Future implementation)
            # prediction = model.predict(reader.state)
            # wheelchair.move(prediction)

    except KeyboardInterrupt:
        print("\nManual stop triggered by user.")
    finally:
        bt.close()
        print("Done.")