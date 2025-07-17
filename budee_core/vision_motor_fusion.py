#!/usr/bin/env python3
"""
BUD-EE Vision Motor Fusion System
Real-time control loop for camera-based navigation and motor control
"""

import cv2
import json
import numpy as np
import time
import threading
from typing import Dict, Tuple, Optional, Any
import logging
from dataclasses import dataclass
import pigpio
import mediapipe as mp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MotorCommand:
    """Motor command structure"""
    forward: bool = False
    reverse: bool = False
    speed: int = 0
    duration: float = 0.0
    steering_angle: int = 0

@dataclass
class DetectionResult:
    """Object detection result"""
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    center_x: int
    center_y: int
    area: int
    confidence: float
    object_type: str

class VisionMotorFusion:
    """Main vision-motor fusion control system"""
    
    def __init__(self, calibration_file: str = "budee_calibration_map.json"):
        self.calibration_file = calibration_file
        self.calibration = self.load_calibration()
        
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
        
        # Initialize GPIO
        self.setup_gpio()
        
        # Camera setup
        self.camera = cv2.VideoCapture(0)  # /dev/video0
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.calibration['visual_center']['frame_width'])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.calibration['visual_center']['frame_height'])
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        # Mediapipe setup for human detection
        self.mp_pose = mp.solutions.pose
        self.mp_face = mp.solutions.face_detection
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.face_detection = self.mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.5
        )
        
        # Control parameters
        self.running = False
        self.last_detection_time = 0
        self.motion_smoothing_buffer = []
        self.steering_smoothing_buffer = []
        
        # Safety parameters
        self.MAX_STEERING_ANGLE = 30
        self.MIN_MOTION_THRESHOLD = 5  # pixels
        self.MAX_MOTOR_SPEED = 80
        self.DETECTION_TIMEOUT = 2.0  # seconds
        
        logger.info("Vision Motor Fusion initialized successfully")
    
    def load_calibration(self) -> Dict[str, Any]:
        """Load calibration data from JSON file"""
        try:
            with open(self.calibration_file, 'r') as f:
                calibration = json.load(f)
            logger.info(f"Loaded calibration from {self.calibration_file}")
            return calibration
        except FileNotFoundError:
            logger.warning(f"Calibration file {self.calibration_file} not found, using defaults")
            return self.get_default_calibration()
    
    def get_default_calibration(self) -> Dict[str, Any]:
        """Return default calibration values"""
        return {
            "servo_map": {
                "-30": 1300,
                "0": 1500,
                "30": 1700
            },
            "motion_gain": {
                "pixels_per_inch": 22.5,
                "baseline_box_area": 5400,
                "forward_threshold": 1.2,
                "reverse_threshold": 0.8
            },
            "visual_center": {
                "frame_width": 640,
                "frame_height": 480,
                "center_x": 320,
                "center_y": 240
            },
            "motor_speed_map": {
                "low": 20,
                "normal": 40,
                "fast": 80
            }
        }
    
    def setup_gpio(self):
        """Initialize GPIO pins for motor and servo control"""
        # Set servo to center position
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, 1500)
        
        # Setup motor pins
        self.pi.set_mode(self.MOTOR_PIN_1, pigpio.OUTPUT)
        self.pi.set_mode(self.MOTOR_PIN_2, pigpio.OUTPUT)
        self.pi.set_PWM_frequency(self.MOTOR_PWM_PIN, 1000)
        
        # Setup fan pin
        self.pi.set_mode(self.FAN_PIN, pigpio.OUTPUT)
        self.pi.write(self.FAN_PIN, 0)
        
        # Stop motors initially
        self.stop_motors()
        
        logger.info("GPIO setup completed")
    
    def detect_human(self, frame: np.ndarray) -> Optional[DetectionResult]:
        """Detect human using Mediapipe face and pose detection"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Try face detection first (faster)
        face_results = self.face_detection.process(rgb_frame)
        
        if face_results.detections:
            for detection in face_results.detections:
                bbox = detection.location_data.relative_bounding_box
                h, w, _ = frame.shape
                
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                center_x = x + width // 2
                center_y = y + height // 2
                area = width * height
                
                return DetectionResult(
                    bbox=(x, y, width, height),
                    center_x=center_x,
                    center_y=center_y,
                    area=area,
                    confidence=detection.score[0],
                    object_type="face"
                )
        
        # Fallback to pose detection
        pose_results = self.pose.process(rgb_frame)
        
        if pose_results.pose_landmarks:
            landmarks = pose_results.pose_landmarks.landmark
            
            # Get bounding box from pose landmarks
            x_coords = [lm.x for lm in landmarks]
            y_coords = [lm.y for lm in landmarks]
            
            h, w, _ = frame.shape
            x = int(min(x_coords) * w)
            y = int(min(y_coords) * h)
            width = int((max(x_coords) - min(x_coords)) * w)
            height = int((max(y_coords) - min(y_coords)) * h)
            
            center_x = x + width // 2
            center_y = y + height // 2
            area = width * height
            
            return DetectionResult(
                bbox=(x, y, width, height),
                center_x=center_x,
                center_y=center_y,
                area=area,
                confidence=0.8,  # Default confidence for pose
                object_type="person"
            )
        
        return None
    
    def calculate_movement(self, detection: DetectionResult) -> MotorCommand:
        """Calculate motor movement based on detection"""
        center_x = self.calibration['visual_center']['center_x']
        center_y = self.calibration['visual_center']['center_y']
        baseline_area = self.calibration['motion_gain']['baseline_box_area']
        
        # Calculate horizontal offset (steering)
        delta_x = detection.center_x - center_x
        
        # Calculate steering angle
        steering_angle = 0
        if abs(delta_x) > self.MIN_MOTION_THRESHOLD:
            # Map pixel offset to steering angle
            max_offset = center_x  # Maximum possible offset
            steering_angle = int((delta_x / max_offset) * self.MAX_STEERING_ANGLE)
            steering_angle = max(-self.MAX_STEERING_ANGLE, min(self.MAX_STEERING_ANGLE, steering_angle))
        
        # Calculate distance/size change (forward/reverse)
        area_ratio = detection.area / baseline_area
        forward_threshold = self.calibration['motion_gain']['forward_threshold']
        reverse_threshold = self.calibration['motion_gain']['reverse_threshold']
        
        forward = False
        reverse = False
        speed = 0
        
        if area_ratio < reverse_threshold:
            # Object too small, move forward
            forward = True
            distance_factor = (reverse_threshold - area_ratio) / reverse_threshold
            speed = int(self.calibration['motor_speed_map']['normal'] * distance_factor)
            speed = min(speed, self.MAX_MOTOR_SPEED)
        elif area_ratio > forward_threshold:
            # Object too large, move backward
            reverse = True
            distance_factor = min((area_ratio - forward_threshold) / forward_threshold, 1.0)
            speed = int(self.calibration['motor_speed_map']['low'] * distance_factor)
            speed = min(speed, self.MAX_MOTOR_SPEED)
        
        return MotorCommand(
            forward=forward,
            reverse=reverse,
            speed=speed,
            duration=0.1,  # Short duration for smooth control
            steering_angle=steering_angle
        )
    
    def apply_smoothing(self, value: float, buffer: list, buffer_size: int = 5) -> float:
        """Apply smoothing to reduce jittery movement"""
        buffer.append(value)
        if len(buffer) > buffer_size:
            buffer.pop(0)
        return sum(buffer) / len(buffer)
    
    def set_servo_angle(self, angle: int):
        """Set servo angle based on calibration map"""
        # Clamp angle
        angle = max(-self.MAX_STEERING_ANGLE, min(self.MAX_STEERING_ANGLE, angle))
        
        # Apply smoothing
        smoothed_angle = self.apply_smoothing(angle, self.steering_smoothing_buffer)
        
        # Map angle to PWM value
        servo_map = self.calibration['servo_map']
        
        if smoothed_angle in [int(k) for k in servo_map.keys()]:
            pwm_value = servo_map[str(int(smoothed_angle))]
        else:
            # Interpolate between calibration points
            angles = sorted([int(k) for k in servo_map.keys()])
            
            for i in range(len(angles) - 1):
                if angles[i] <= smoothed_angle <= angles[i + 1]:
                    # Linear interpolation
                    ratio = (smoothed_angle - angles[i]) / (angles[i + 1] - angles[i])
                    pwm_low = servo_map[str(angles[i])]
                    pwm_high = servo_map[str(angles[i + 1])]
                    pwm_value = int(pwm_low + ratio * (pwm_high - pwm_low))
                    break
            else:
                pwm_value = servo_map['0']  # Default to center
        
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, pwm_value)
    
    def set_motor_movement(self, command: MotorCommand):
        """Control motor movement"""
        if command.speed == 0 or (not command.forward and not command.reverse):
            self.stop_motors()
            return
        
        # Apply smoothing to speed
        smoothed_speed = self.apply_smoothing(command.speed, self.motion_smoothing_buffer)
        pwm_value = int(smoothed_speed * 255 / 100)  # Convert to 0-255 range
        
        if command.forward:
            self.pi.write(self.MOTOR_PIN_1, 1)
            self.pi.write(self.MOTOR_PIN_2, 0)
        elif command.reverse:
            self.pi.write(self.MOTOR_PIN_1, 0)
            self.pi.write(self.MOTOR_PIN_2, 1)
        
        self.pi.set_PWM_dutycycle(self.MOTOR_PWM_PIN, pwm_value)
        
        # Schedule stop after duration
        if command.duration > 0:
            threading.Timer(command.duration, self.stop_motors).start()
    
    def stop_motors(self):
        """Stop all motor movement"""
        self.pi.write(self.MOTOR_PIN_1, 0)
        self.pi.write(self.MOTOR_PIN_2, 0)
        self.pi.set_PWM_dutycycle(self.MOTOR_PWM_PIN, 0)
    
    def center_servo(self):
        """Center the steering servo"""
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, 1500)
    
    def process_frame(self, frame: np.ndarray) -> Optional[MotorCommand]:
        """Process a single frame and return motor command"""
        detection = self.detect_human(frame)
        
        if detection is None:
            # No detection - check timeout
            if time.time() - self.last_detection_time > self.DETECTION_TIMEOUT:
                self.center_servo()
                self.stop_motors()
            return None
        
        self.last_detection_time = time.time()
        
        # Calculate and apply movement
        command = self.calculate_movement(detection)
        
        # Apply steering
        self.set_servo_angle(command.steering_angle)
        
        # Apply motor movement
        self.set_motor_movement(command)
        
        # Draw detection on frame for debugging
        if detection:
            x, y, w, h = detection.bbox
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (detection.center_x, detection.center_y), 5, (0, 0, 255), -1)
            
            # Display info
            info_text = f"{detection.object_type}: {detection.confidence:.2f}"
            cv2.putText(frame, info_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Display movement info
            move_text = f"Steer: {command.steering_angle}° Speed: {command.speed}"
            cv2.putText(frame, move_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        
        return command
    
    def run_vision_loop(self, display: bool = False):
        """Main vision processing loop"""
        self.running = True
        logger.info("Starting vision-motor fusion loop")
        
        try:
            while self.running:
                ret, frame = self.camera.read()
                if not ret:
                    logger.error("Failed to read frame from camera")
                    break
                
                # Process frame
                command = self.process_frame(frame)
                
                # Display frame if requested
                if display:
                    cv2.imshow('BUD-EE Vision', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.033)  # ~30 FPS
                
        except KeyboardInterrupt:
            logger.info("Vision loop interrupted by user")
        except Exception as e:
            logger.error(f"Error in vision loop: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the vision-motor fusion system"""
        self.running = False
        self.stop_motors()
        self.center_servo()
        
        if hasattr(self, 'camera'):
            self.camera.release()
        
        cv2.destroyAllWindows()
        
        if hasattr(self, 'pi'):
            self.pi.stop()
        
        logger.info("Vision Motor Fusion stopped")
    
    def manual_control(self, steering_angle: int, speed: int, direction: str, duration: float = 1.0):
        """Manual control interface for testing"""
        command = MotorCommand(
            forward=(direction == 'forward'),
            reverse=(direction == 'reverse'),
            speed=speed,
            duration=duration,
            steering_angle=steering_angle
        )
        
        self.set_servo_angle(command.steering_angle)
        self.set_motor_movement(command)
        
        logger.info(f"Manual control: {direction} at {speed}% speed, {steering_angle}° steering for {duration}s")

def main():
    """Main function for testing"""
    try:
        fusion = VisionMotorFusion()
        
        # Run with display for debugging
        fusion.run_vision_loop(display=True)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        if 'fusion' in locals():
            fusion.stop()

if __name__ == "__main__":
    main() 