import RPi.GPIO as GPIO
import threading
import time
import math
import requests
import os
import RequestSensorData
import ParseSensorData

from dotenv import load_dotenv
from datetime import datetime, timedelta
from pypresence import Presence

def convert_to_timestamp(date_time_str):
    """Converts a date and time string with AM/PM to a timestamp."""

    # Parse the string into a datetime object
    dt_object = datetime.strptime(date_time_str, '%m/%d/%Y %I:%M:%S %p')
    return dt_object

def connectToLibreLinkUp():
    """ Tries to make a connection to LibreLinkUp and requests patient_id
    """
    global patient_id
    try:
        RequestSensorData.setToken(email, password)
        patient_id = RequestSensorData.getPatientId()
    except:
        print(f"\n{time.strftime('%H:%M:%S')} - API timeout. Trying again.")

# Load environment variables
load_dotenv()
email = os.getenv('EMAIL')
password = os.getenv('PASSWORD')

# GPIO Setup
LED_PIN = 47
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

# PWM setup for breathing effect
pwm = GPIO.PWM(LED_PIN, 100)  # 200 Hz frequency

class GlucoseLEDMonitor:
    def __init__(self):
        self.stop_event = threading.Event()
        self.current_pattern = None
        self.pattern_thread = None

    def get_glucose_level(self):
        """
        Retrieve glucose level from the monitoring device API.
        Returns a tuple of (glucose_value, timestamp)
        
        Note: Replace with actual API call details
        """
        try:
            # request data from LibreLinkUp
            try:
                print("getting data")
                data = RequestSensorData.getData(patient_id)
            except:
                 connectToLibreLinkUp()
            # get blood glucose and quote
            BG_value = ParseSensorData.getLatestMeasurement(data)
            TS = ParseSensorData.getLatestMeasurementTimestamp(data)
            TrendArrow = ParseSensorData.getLatestMeasurementTrendArrow(data)
            print("BG value=",BG_value, "mg/dL")
            print("Trend:",TrendArrow)
            return BG_value,TS
        
        except Exception as e:
            print(f"Error retrieving glucose level: {e}")
            return None, None

    def calculate_breathing_brightness(self, speed=2.0):
        """
        Calculate LED brightness using a sine wave for breathing effect
        
        :param speed: Controls the speed of breathing (lower is slower)
        :return: Duty cycle value between 0 and 100
        """
        current_time = time.time() * speed
        brightness = (math.sin(current_time) + 1) / 2  # Sine wave between 0 and 1
        return brightness * 100  # Convert to duty cycle (0-100)

    def critical_low_pattern(self):
        print("extreme low, fast")
        """Extremely fast blinking pattern for critical low glucose"""
        while not self.stop_event.is_set():
            pwm.start(100)  # Full brightness
            time.sleep(0.051)
            pwm.start(0)    # Off
            time.sleep(0.051)

    def in_range_pattern(self):
        """Slow breathing pattern for in-range glucose levels"""
        print("in range, breathing")
        while not self.stop_event.is_set():
            brightness = self.calculate_breathing_brightness(speed=2.0)
            pwm.start(brightness)
            time.sleep(0.01)  # Small delay to make breathing smooth

    def critical_high_pattern(self):
        """Fast breathing pattern for critical high glucose"""
        print("critical high, fast breathing")
        while not self.stop_event.is_set():
            brightness = self.calculate_breathing_brightness(speed=8.0)
            pwm.start(brightness)
            time.sleep(0.05)  # Small delay to make breathing fast

    def issue_pattern(self):
        print("issue, issue pattern")
        """Pattern when there's an issue retrieving glucose data"""
        while not self.stop_event.is_set():
            # Blink 3x quickly
            for _ in range(3):
                pwm.start(100)
                time.sleep(0.1)
                pwm.start(0)
                time.sleep(0.1)
            
            #pwm.start(100)
            #time.sleep(0.3)
            #pwm.start(0)
            time.sleep(2)  # Pause between repetitions

    def start_pattern(self, pattern_method):
        """Start a new LED pattern"""
        # Stop any existing pattern
        self.stop_pattern()
        
        # Start new pattern
        self.stop_event.clear()
        self.pattern_thread = threading.Thread(target=pattern_method)
        self.pattern_thread.daemon = True
        self.pattern_thread.start()

    def stop_pattern(self):
        """Stop the current LED pattern"""
        if self.pattern_thread and self.pattern_thread.is_alive():
            self.stop_event.set()
            self.pattern_thread.join()
            pwm.start(0)  # Ensure LED is off

    def monitor_glucose(self):
        """Main monitoring loop"""
        while True:
            try:
                glucose_value, timestamp = self.get_glucose_level()
 
                # Check if data retrieval was successful
                if glucose_value is None or timestamp is None:
                    self.start_pattern(self.issue_pattern)
                    continue
                
                # Check timestamp age
                current_time = datetime.now()
                
                TS = convert_to_timestamp(timestamp)
                #print("Data collected at:",timestamp)
                #print("Current time:",current_time)
                if current_time - TS > timedelta(minutes=15):
                    self.start_pattern(self.issue_pattern)
                    continue
                
                # Determine LED pattern based on glucose level
                if glucose_value < 70:
                    self.start_pattern(self.critical_low_pattern)
                elif 70 <= glucose_value <= 170:
                    self.start_pattern(self.in_range_pattern)
                else:  # > 170
                    self.start_pattern(self.critical_high_pattern)
                
                # Wait before next check
                time.sleep(300)  # 5 minutes
            
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                self.start_pattern(self.issue_pattern)
                time.sleep(60)  # Wait before retrying

    def cleanup(self):
        """Cleanup GPIO resources"""
        self.stop_pattern()
        pwm.stop()
        GPIO.cleanup()

def main():
    connectToLibreLinkUp() 
    monitor = GlucoseLEDMonitor()
    try:
        monitor.monitor_glucose()
    except KeyboardInterrupt:
        print("Monitoring stopped by user")
    finally:
        monitor.cleanup()

if __name__ == '__main__':
    main()
