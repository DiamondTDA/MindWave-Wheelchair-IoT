import time
import numpy as np
from collections import deque
from scipy.signal import find_peaks

class BlinkProcessor:
    def __init__(self):
        # Configuration
        self.WINDOW_SIZE = 512
        self.STEP = 256
        self.THRESHOLD = 1100  # Slightly lowered for better sensitivity
        self.MIN_DIST = 250    # Minimum samples between peaks within a window
        
        # Timing
        self.DOUBLE_GAP = 1.1  # Max time allowed between blinks in a sequence
        self.COOLDOWN = 0.7    # Min time to wait before allowing another blink
        
        # Buffers
        self.raw_buffer = deque(maxlen=self.WINDOW_SIZE)
        self.sample_counter = 0
        
        # State Tracking
        self.blink_timestamps = []
        self.last_detection_time = 0

    def process_raw(self, raw_value):
        self.raw_buffer.append(raw_value)
        self.sample_counter += 1

        # Process window every 'STEP' samples
        if self.sample_counter >= self.STEP and len(self.raw_buffer) == self.WINDOW_SIZE:
            self.analyze_window()
            self.sample_counter = 0
        
        # Check if the "Blink Sequence" is finished
        return self.check_sequence_completion()

    def analyze_window(self):
        now = time.time()
        # Convert deque to array for scipy
        data = np.array(self.raw_buffer)
        
        # Find peaks that meet height and distance requirements
        peaks, _ = find_peaks(data, height=self.THRESHOLD, distance=self.MIN_DIST)
        
        if len(peaks) > 0:
            # We only count the blink if we aren't in a cooldown from the last one
            if (now - self.last_detection_time) > self.COOLDOWN:
                self.blink_timestamps.append(now)
                self.last_detection_time = now

    def check_sequence_completion(self):
        if not self.blink_timestamps:
            return

        now = time.time()
        # If the last blink happened more than DOUBLE_GAP seconds ago, the sequence is over
        if (now - self.last_detection_time) > self.DOUBLE_GAP:
            count = len(self.blink_timestamps)
            
            action = 0
            if count == 1:
                action = 1
            elif count == 2:
                action = 2
            elif count == 3:
                action = 3
            
            # Clear the list to start a fresh sequence
            self.blink_timestamps = []
            return action