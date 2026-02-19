import time
from Bt_manager import BTManager
from signal_reader import SignalReader
from blink_processor import BlinkProcessor
from data_collection import DataCollector
# from jaw_clench import JawClench # Placeholder for now
# from bci_ai_model import BCIModel # Placeholder for later

# 1. Initiate Components
bt = BTManager()
reader = SignalReader()
blinker = BlinkProcessor()
collector = DataCollector()
# clench = JawClench() 
# model = BCIModel()

# 2. Setup Data Collection
target_file = collector.get_file_handle()

if target_file and bt.connect():
    current_label = input("Enter label for this session (e.g., 'F' for Forward): ")
    duration = int(input("Collection duration in seconds: "))
    
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    start_time = time.time()
    
    try:
        while time.time() - start_time < duration:
            # --- Buffer Management ---
            if bt.ser.in_waiting > 500:
                print("Buffer overflow - resetting")
                bt.ser.reset_input_buffer()
                continue

            if bt.ser.in_waiting > 0:
                # T1: Start Total Latency (Serial arrival)
                t_total_start = time.perf_counter()
                
                payload = reader.read_packet(bt.ser)
                
                if payload:
                    # T2: Start Logic Latency (Parsing start)
                    t_logic_start = time.perf_counter()
                    
                    # 3. Process Data
                    reader.parse_payload(payload)
                    
                    # Pass raw data to blink and jaw clench
                    if reader.last_code == 0x80: # RAW_WAVE code
                        raw_val = reader.state["raw"]
                        blinker.process_raw(raw_val)
                        # clench.process_raw(raw_val) # For future implementation

                    # T3: End of processing
                    t_end = time.perf_counter()
                    
                    # Calculate Latencies (ms)
                    total_lat = (t_end - t_total_start) * 1000
                    logic_t = (t_end - t_logic_start) * 1000

                    # 4. Collect Data (Temp Step)
                    # We save whenever a power packet (0x83) arrives (~1Hz)
                    if reader.last_code == 0x83:
                        collector.save_row(target_file, reader.state, current_label, total_lat, logic_t)
                        print(f"Recorded: {int(time.time() - start_time)}s", end="\r")

            # 5. Movement Logic (Future implementation)
            # prediction = model.predict(reader.state)
            # wheelchair.move(prediction)

    except KeyboardInterrupt:
        print("\nManual stop.")
    finally:
        bt.close()
        print("Done.")