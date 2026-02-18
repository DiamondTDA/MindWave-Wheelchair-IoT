import time
import numpy as np
from collections import deque
from scipy.signal import find_peaks

class BlinkProcessor:
    def __init__(self):
        # Constants from your working code
        self.WINDOW_SIZE = 512
        self.OVERLAP = 0.5
        self.STEP = int(self.WINDOW_SIZE * (1 - self.OVERLAP))
        self.THRESHOLD = 1200
        self.MIN_DIST = 260
        self.COOLDOWN = 0.6
        self.DOUBLE_GAP = 1.1

        # Buffers and Counters
        self.raw_buffer = deque(maxlen=self.WINDOW_SIZE)
        self.sample_counter = 0
        self.last_blink_time = 0
        self.prev_blink_time = None
        self.blink_count = 0

    def process_raw(self, raw_value):
        """This is the function we 'hook' to the SignalReader."""
        self.raw_buffer.append(raw_value)
        self.sample_counter += 1

        # Only check for peaks once we have enough new samples (Step size)
        if len(self.raw_buffer) >= self.WINDOW_SIZE and self.sample_counter >= self.STEP:
            self.analyze_window()
            self.sample_counter = 0

    def analyze_window(self):
        data = np.array(self.raw_buffer)
        peaks, _ = find_peaks(data, height=self.THRESHOLD, distance=self.MIN_DIST)
        
        now = time.time()
        if len(peaks) > 0 and (now - self.last_blink_time) >= self.COOLDOWN:
            self.handle_detection(now)
            self.last_blink_time = now

        # Logic to 'finalize' a single or double blink after the gap expires
        if self.prev_blink_time is not None:
            if (now - self.prev_blink_time) > self.DOUBLE_GAP:
                if self.blink_count == 1:
                    print("Single Blink Detected")
                elif self.blink_count >= 2:
                    print("Double Blink Detected")
                
                # Reset for next detection
                self.prev_blink_time = None
                self.blink_count = 0

    def handle_detection(self, now):
        if self.prev_blink_time is None:
            self.prev_blink_time = now
            self.blink_count = 1
        else:
            if (now - self.prev_blink_time) <= self.DOUBLE_GAP:
                self.blink_count += 1