from signal_reader import SignalReader

# 1. A tiny dummy object to feed the raw bytes to your reader
class DummySerial:
    def __init__(self, byte_data):
        self.data = byte_data
        self.index = 0
        
    def read(self, size=1):
        # Spit out the exact number of bytes read_packet asks for
        if self.index >= len(self.data):
            return b'' 
        chunk = self.data[self.index : self.index + size]
        self.index += size
        return chunk

# 2. Your two full packets (from SYNC to Checksum)
# Packet 1: Raw = 150
packet_1 = b'\xaa\xaa\x06\x02\x00\x80\x02\x00\x96\xe5'
# Packet 2: Raw = 800
packet_2 = b'\xaa\xaa\x06\x02\x00\x80\x02\x03\x20\x58'

# Combine them into our dummy serial port
dummy_port = DummySerial(packet_1 + packet_2)

# 3. Setup your SignalReader
reader = SignalReader()

# Define the hook just to prove it fires instantly
def test_hook(raw_val):
    print(f"HOOK FIRED! Instant Raw Value: {raw_val}")

reader.on_raw_received = test_hook

# 4. Run the test exactly twice
print("--- Testing Packet 1 ---")
payload1 = reader.read_packet(dummy_port)
if payload1:
    print(f"Payload extracted: {payload1}")
    reader.parse_payload(payload1)
    print(f"State updated: {reader.state['poor_signal']}")

print("\n--- Testing Packet 2 ---")
payload2 = reader.read_packet(dummy_port)
if payload2:
    print(f"Payload extracted: {payload2}")
    reader.parse_payload(payload2)
    print(f"State updated: {reader.state['poor_signal']}")