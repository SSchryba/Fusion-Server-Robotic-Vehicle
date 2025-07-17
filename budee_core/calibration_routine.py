#!/usr/bin/env python3
"""
BUD-EE Calibration Routine
Performs initial calibration sweep to generate motor and vision calibration data
"""

import cv2
import json
import numpy as np
import time
import pigpio
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import mediapipe as mp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CalibrationPoint:
    """Single calibration data point"""
    servo_pwm: int
    servo_angle: int
    visual_offset_x: int
    motor_movement_distance: float
    box_area_change: float

class BudeeCalibrationSystem:
    """Calibration system for BUD-EE vehicle"""
    
    def __init__(self, output_file: str = "budee_calibration_map.json"):
        self.output_file = output_file
        
        # Hardware setup
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Failed to connect to pigpio daemon")
        
        # GPIO Pin Configuration (BCM numbering)
        self.SERVO_PIN = 4     # GPIO 4 (Pin 7) - Steering Servo PWM
        self.MOTOR_PIN_1 = 17  # GPIO 17 (Pin 11) - L298N IN1
        self.MOTOR_PIN_2 = 27  # GPIO 27 (Pin 13) - L298N IN2
        self.MOTOR_PWM_PIN = 22  # GPIO 22 (Pin 15) - L298N ENA (PWM)
        self.FAN_PIN = 20      # GPIO 20 (Pin 38) - Cooling Fan Control
        
        # Calibration parameters
        self.SERVO_PWM_MIN = 1000
        self.SERVO_PWM_MAX = 2000
        self.SERVO_PWM_CENTER = 1500
        self.SERVO_STEPS = 5  # Number of calibration points
        self.MOTOR_SPEED = 30  # Moderate speed for calibration
        self.MOVE_DURATION = 1.0  # Seconds to move for distance measurement
        
        # Vision setup
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        # Mediapipe setup for reference detection
        self.mp_face = mp.solutions.face_detection
        self.face_detection = self.mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.3
        )
        
        # Calibration data storage
        self.servo_calibration_points = []
        self.motion_calibration_data = {}
        self.visual_center = {"frame_width": 640, "frame_height": 480, "center_x": 320, "center_y": 240}
        
        self.setup_gpio()
        logger.info("Calibration system initialized")
    
    def setup_gpio(self):
        """Initialize GPIO pins"""
        # Setup servo
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, self.SERVO_PWM_CENTER)
        
        # Setup motor pins
        self.pi.set_mode(self.MOTOR_PIN_1, pigpio.OUTPUT)
        self.pi.set_mode(self.MOTOR_PIN_2, pigpio.OUTPUT)
        self.pi.set_PWM_frequency(self.MOTOR_PWM_PIN, 1000)
        
        # Setup fan
        self.pi.set_mode(self.FAN_PIN, pigpio.OUTPUT)
        self.pi.write(self.FAN_PIN, 0)
        
        # Ensure motors are stopped
        self.stop_motors()
        
        logger.info("GPIO setup completed")
    
    def stop_motors(self):
        """Stop all motor movement"""
        self.pi.write(self.MOTOR_PIN_1, 0)
        self.pi.write(self.MOTOR_PIN_2, 0)
        self.pi.set_PWM_dutycycle(self.MOTOR_PWM_PIN, 0)
    
    def move_forward(self, duration: float = 1.0):
        """Move vehicle forward for specified duration"""
        self.pi.write(self.MOTOR_PIN_1, 1)
        self.pi.write(self.MOTOR_PIN_2, 0)
        self.pi.set_PWM_dutycycle(self.MOTOR_PWM_PIN, int(self.MOTOR_SPEED * 255 / 100))
        time.sleep(duration)
        self.stop_motors()
    
    def move_backward(self, duration: float = 1.0):
        """Move vehicle backward for specified duration"""
        self.pi.write(self.MOTOR_PIN_1, 0)
        self.pi.write(self.MOTOR_PIN_2, 1)
        self.pi.set_PWM_dutycycle(self.MOTOR_PWM_PIN, int(self.MOTOR_SPEED * 255 / 100))
        time.sleep(duration)
        self.stop_motors()
    
    def detect_reference_object(self, frame: np.ndarray) -> Tuple[int, int, int]:
        """Detect reference object (face) and return center coordinates and area"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)
        
        if results.detections:
            detection = results.detections[0]  # Use first detection
            bbox = detection.location_data.relative_bounding_box
            h, w, _ = frame.shape
            
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)
            
            center_x = x + width // 2
            center_y = y + height // 2
            area = width * height
            
            return center_x, center_y, area
        
        return -1, -1, 0  # No detection
    
    def capture_stable_frame(self, wait_time: float = 1.0) -> np.ndarray:
        """Capture a stable frame after waiting for movement to settle"""
        time.sleep(wait_time)
        
        # Capture multiple frames and use the last one
        for _ in range(10):
            ret, frame = self.camera.read()
            if not ret:
                raise RuntimeError("Failed to capture frame")
        
        return frame
    
    def calibrate_servo_sweep(self) -> List[CalibrationPoint]:
        """Perform servo sweep calibration"""
        logger.info("Starting servo sweep calibration...")
        
        print("\n🔧 SERVO CALIBRATION")
        print("=" * 50)
        print("Please position a person's face in front of the camera.")
        print("The face should be centered and at a comfortable distance.")
        print("Press Enter when ready...")
        input()
        
        # Get baseline measurement at center position
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, self.SERVO_PWM_CENTER)
        baseline_frame = self.capture_stable_frame(2.0)
        baseline_x, baseline_y, baseline_area = self.detect_reference_object(baseline_frame)
        
        if baseline_x == -1:
            raise RuntimeError("No reference object detected! Please ensure a person's face is visible.")
        
        logger.info(f"Baseline detection: center=({baseline_x}, {baseline_y}), area={baseline_area}")
        
        # Perform servo sweep
        calibration_points = []
        pwm_values = np.linspace(self.SERVO_PWM_MIN, self.SERVO_PWM_MAX, self.SERVO_STEPS)
        
        for i, pwm_value in enumerate(pwm_values):
            pwm_int = int(pwm_value)
            angle = self.pwm_to_angle(pwm_int)
            
            print(f"\nCalibrating servo position {i+1}/{self.SERVO_STEPS}")
            print(f"PWM: {pwm_int}, Angle: {angle}°")
            
            # Set servo position
            self.pi.set_servo_pulsewidth(self.SERVO_PIN, pwm_int)
            
            # Capture frame after movement settles
            frame = self.capture_stable_frame(1.5)
            
            # Detect object
            center_x, center_y, area = self.detect_reference_object(frame)
            
            if center_x != -1:
                visual_offset_x = center_x - baseline_x
                
                calibration_point = CalibrationPoint(
                    servo_pwm=pwm_int,
                    servo_angle=angle,
                    visual_offset_x=visual_offset_x,
                    motor_movement_distance=0.0,  # Will be filled later
                    box_area_change=0.0  # Will be filled later
                )
                
                calibration_points.append(calibration_point)
                
                logger.info(f"Servo angle {angle}°: PWM={pwm_int}, Visual offset={visual_offset_x}px")
                
                # Draw detection on frame for visual feedback
                if center_x != -1:
                    cv2.circle(frame, (center_x, center_y), 10, (0, 255, 0), -1)
                    cv2.putText(frame, f"Angle: {angle}°", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"Offset: {visual_offset_x}px", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow('Servo Calibration', frame)
                cv2.waitKey(1000)  # Show for 1 second
            else:
                logger.warning(f"No detection at servo angle {angle}°")
        
        # Return to center
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, self.SERVO_PWM_CENTER)
        cv2.destroyAllWindows()
        
        logger.info(f"Servo calibration completed with {len(calibration_points)} points")
        return calibration_points
    
    def calibrate_motion_distance(self) -> Dict[str, Any]:
        """Calibrate motion distance and area change measurements"""
        logger.info("Starting motion distance calibration...")
        
        print("\n🚗 MOTION CALIBRATION")
        print("=" * 50)
        print("The vehicle will now move forward and backward to calibrate distance sensing.")
        print("Please ensure there's clear space around the vehicle.")
        print("Keep the reference person/face in view of the camera.")
        print("Press Enter when ready...")
        input()
        
        # Get initial reference
        initial_frame = self.capture_stable_frame(1.0)
        initial_x, initial_y, initial_area = self.detect_reference_object(initial_frame)
        
        if initial_x == -1:
            raise RuntimeError("No reference object detected for motion calibration!")
        
        logger.info(f"Initial reference: area={initial_area}")
        
        # Test forward movement
        print("\n📏 Testing forward movement...")
        self.move_forward(self.MOVE_DURATION)
        
        forward_frame = self.capture_stable_frame(1.0)
        forward_x, forward_y, forward_area = self.detect_reference_object(forward_frame)
        
        # Test backward movement (return to original position and go further back)
        print("📏 Returning to start position...")
        self.move_backward(self.MOVE_DURATION)
        time.sleep(1.0)
        
        print("📏 Testing backward movement...")
        self.move_backward(self.MOVE_DURATION)
        
        backward_frame = self.capture_stable_frame(1.0)
        backward_x, backward_y, backward_area = self.detect_reference_object(backward_frame)
        
        # Return to initial position
        print("📏 Returning to initial position...")
        self.move_forward(self.MOVE_DURATION)
        time.sleep(1.0)
        
        # Calculate motion parameters
        motion_data = {
            "pixels_per_inch": 22.5,  # Default estimate
            "baseline_box_area": initial_area,
            "forward_threshold": 1.2,
            "reverse_threshold": 0.8
        }
        
        if forward_area > 0 and backward_area > 0:
            # Calculate area ratios
            forward_ratio = forward_area / initial_area
            backward_ratio = backward_area / initial_area
            
            # Update thresholds based on actual measurements
            motion_data["forward_threshold"] = max(forward_ratio * 0.9, 1.1)
            motion_data["reverse_threshold"] = min(backward_ratio * 1.1, 0.9)
            
            logger.info(f"Motion calibration: forward_ratio={forward_ratio:.2f}, backward_ratio={backward_ratio:.2f}")
        
        return motion_data
    
    def pwm_to_angle(self, pwm_value: int) -> int:
        """Convert PWM value to approximate steering angle"""
        # Linear mapping from PWM range to angle range
        angle_range = 60  # -30 to +30 degrees
        pwm_range = self.SERVO_PWM_MAX - self.SERVO_PWM_MIN
        
        normalized = (pwm_value - self.SERVO_PWM_MIN) / pwm_range
        angle = int((normalized - 0.5) * angle_range)
        
        return max(-30, min(30, angle))
    
    def generate_servo_map(self, calibration_points: List[CalibrationPoint]) -> Dict[str, int]:
        """Generate servo angle to PWM mapping"""
        servo_map = {}
        
        # Always include center position
        servo_map["0"] = self.SERVO_PWM_CENTER
        
        # Add calibration points
        for point in calibration_points:
            servo_map[str(point.servo_angle)] = point.servo_pwm
        
        # Ensure we have left and right extremes
        if "-30" not in servo_map:
            servo_map["-30"] = self.SERVO_PWM_MIN + 200  # Safe margin
        
        if "30" not in servo_map:
            servo_map["30"] = self.SERVO_PWM_MAX - 200  # Safe margin
        
        return servo_map
    
    def run_full_calibration(self) -> Dict[str, Any]:
        """Run complete calibration procedure"""
        print("🤖 BUD-EE CALIBRATION SYSTEM")
        print("=" * 60)
        print("This calibration will help BUD-EE learn to navigate and track objects.")
        print("The process will take about 5-10 minutes.")
        print("Please follow the instructions carefully.")
        print("\nStarting calibration...")
        
        try:
            # Servo calibration
            servo_points = self.calibrate_servo_sweep()
            servo_map = self.generate_servo_map(servo_points)
            
            # Motion calibration
            motion_data = self.calibrate_motion_distance()
            
            # Generate complete calibration map
            calibration_map = {
                "servo_map": servo_map,
                "motion_gain": motion_data,
                "visual_center": self.visual_center,
                "motor_speed_map": {
                    "low": 20,
                    "normal": 40,
                    "fast": 80
                },
                "calibration_metadata": {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "servo_points_count": len(servo_points),
                    "baseline_area": motion_data["baseline_box_area"],
                    "version": "1.0"
                }
            }
            
            # Save calibration
            with open(self.output_file, 'w') as f:
                json.dump(calibration_map, f, indent=2)
            
            print(f"\n✅ Calibration completed successfully!")
            print(f"📄 Calibration saved to: {self.output_file}")
            print(f"📊 Servo calibration points: {len(servo_points)}")
            print(f"📏 Baseline detection area: {motion_data['baseline_box_area']} pixels")
            
            logger.info("Full calibration completed successfully")
            return calibration_map
            
        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            raise
        finally:
            self.cleanup()
    
    def test_calibration(self, calibration_file: str = None):
        """Test the generated calibration"""
        if calibration_file is None:
            calibration_file = self.output_file
        
        print(f"\n🧪 Testing calibration from {calibration_file}")
        
        try:
            with open(calibration_file, 'r') as f:
                calibration = json.load(f)
            
            # Test servo positions
            print("Testing servo positions...")
            servo_map = calibration["servo_map"]
            
            for angle_str, pwm in servo_map.items():
                angle = int(angle_str)
                print(f"  Setting servo to {angle}° (PWM: {pwm})")
                self.pi.set_servo_pulsewidth(self.SERVO_PIN, pwm)
                time.sleep(1.0)
            
            # Return to center
            self.pi.set_servo_pulsewidth(self.SERVO_PIN, self.SERVO_PWM_CENTER)
            
            print("✅ Calibration test completed")
            
        except Exception as e:
            logger.error(f"Calibration test failed: {e}")
            raise
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_motors()
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, self.SERVO_PWM_CENTER)
        
        if hasattr(self, 'camera'):
            self.camera.release()
        
        cv2.destroyAllWindows()
        
        if hasattr(self, 'pi'):
            self.pi.stop()
        
        logger.info("Calibration system cleaned up")

def main():
    """Main calibration function"""
    try:
        calibrator = BudeeCalibrationSystem()
        
        # Check if calibration already exists
        try:
            with open("budee_calibration_map.json", 'r') as f:
                existing_cal = json.load(f)
            
            print("⚠️  Existing calibration found!")
            response = input("Do you want to recalibrate? (y/N): ").lower()
            
            if response != 'y':
                print("Using existing calibration.")
                calibrator.test_calibration()
                return
        except FileNotFoundError:
            pass
        
        # Run calibration
        calibration_map = calibrator.run_full_calibration()
        
        # Optionally test the calibration
        test_response = input("\nDo you want to test the calibration? (Y/n): ").lower()
        if test_response != 'n':
            calibrator.test_calibration()
        
    except KeyboardInterrupt:
        print("\n❌ Calibration interrupted by user")
    except Exception as e:
        logger.error(f"Calibration error: {e}")
        print(f"❌ Calibration failed: {e}")
    finally:
        if 'calibrator' in locals():
            calibrator.cleanup()

if __name__ == "__main__":
    main() 