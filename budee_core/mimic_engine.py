#!/usr/bin/env python3
"""
BUD-EE Mimic Engine
Gesture mirroring system using pose detection and motor response
"""

import cv2
import numpy as np
import time
import threading
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import mediapipe as mp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GestureType(Enum):
    """Types of gestures that can be detected"""
    HEAD_TILT_LEFT = "head_tilt_left"
    HEAD_TILT_RIGHT = "head_tilt_right"
    HEAD_NOD = "head_nod"
    WAVE = "wave"
    HAND_RAISE = "hand_raise"
    APPROACH = "approach"
    RETREAT = "retreat"
    LEAN_LEFT = "lean_left"
    LEAN_RIGHT = "lean_right"
    UNKNOWN = "unknown"

@dataclass
class GestureEvent:
    """Single gesture detection event"""
    gesture_type: GestureType
    confidence: float
    timestamp: float
    response_executed: bool = False
    pose_landmarks: Optional[Dict] = None

@dataclass
class PoseAnalysis:
    """Pose analysis results"""
    head_tilt_angle: float
    head_position: Tuple[float, float]
    shoulder_angle: float
    hand_positions: List[Tuple[float, float]]
    bounding_box_area: float
    body_center: Tuple[float, float]

class MimicEngine:
    """Gesture detection and mirroring system for BUD-EE"""
    
    def __init__(self, motor_controller=None, interaction_controller=None):
        # External controllers
        self.motor_controller = motor_controller
        self.interaction_controller = interaction_controller
        
        # Mediapipe setup
        self.mp_pose = mp.solutions.pose
        self.mp_hands = mp.solutions.hands
        self.mp_face = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize pose detection
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5
        )
        
        # Initialize hand detection
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5
        )
        
        # Initialize face detection
        self.face_detection = self.mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.6
        )
        
        # Gesture detection parameters
        self.gesture_history = []
        self.last_gesture_time = 0
        self.gesture_cooldown = 2.0  # Seconds between gesture responses
        self.pose_history = []  # For temporal analysis
        self.pose_history_size = 10
        
        # Thresholds for gesture detection
        self.TILT_THRESHOLD = 15.0  # degrees
        self.NOD_THRESHOLD = 0.03  # normalized distance
        self.WAVE_THRESHOLD = 0.05  # hand movement threshold
        self.APPROACH_THRESHOLD = 1.2  # area increase ratio
        self.RETREAT_THRESHOLD = 0.8  # area decrease ratio
        
        # Mimic response parameters
        self.mimic_enabled = True
        self.mimic_intensity = 1.0  # Multiplier for response strength
        self.response_delay = 0.5  # Seconds delay before responding
        
        # Tracking state
        self.running = False
        self.current_pose = None
        self.baseline_pose = None
        self.frame_count = 0
        
        logger.info("Mimic Engine initialized")
    
    def set_controllers(self, motor_controller=None, interaction_controller=None):
        """Set external controllers"""
        if motor_controller:
            self.motor_controller = motor_controller
        if interaction_controller:
            self.interaction_controller = interaction_controller
    
    def analyze_pose(self, landmarks, frame_shape: Tuple[int, int]) -> PoseAnalysis:
        """Analyze pose landmarks to extract gesture information"""
        h, w = frame_shape[:2]
        
        # Extract key landmark positions
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
        
        # Calculate head tilt angle
        shoulder_vector = np.array([right_shoulder.x - left_shoulder.x, 
                                  right_shoulder.y - left_shoulder.y])
        horizontal = np.array([1, 0])
        head_tilt_angle = np.degrees(np.arccos(
            np.dot(shoulder_vector, horizontal) / 
            (np.linalg.norm(shoulder_vector) * np.linalg.norm(horizontal))
        ))
        
        # Adjust for direction
        if shoulder_vector[1] > 0:  # Right shoulder lower
            head_tilt_angle = -head_tilt_angle
        
        # Head position (nose)
        head_position = (nose.x * w, nose.y * h)
        
        # Shoulder angle (body lean)
        shoulder_angle = np.degrees(np.arctan2(
            right_shoulder.y - left_shoulder.y,
            right_shoulder.x - left_shoulder.x
        ))
        
        # Hand positions
        hand_positions = [
            (left_wrist.x * w, left_wrist.y * h),
            (right_wrist.x * w, right_wrist.y * h)
        ]
        
        # Body center and bounding box
        all_x = [lm.x for lm in landmarks]
        all_y = [lm.y for lm in landmarks]
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        bounding_box_area = (max_x - min_x) * (max_y - min_y) * w * h
        body_center = ((min_x + max_x) / 2 * w, (min_y + max_y) / 2 * h)
        
        return PoseAnalysis(
            head_tilt_angle=head_tilt_angle,
            head_position=head_position,
            shoulder_angle=shoulder_angle,
            hand_positions=hand_positions,
            bounding_box_area=bounding_box_area,
            body_center=body_center
        )
    
    def detect_gesture(self, current_pose: PoseAnalysis, previous_pose: Optional[PoseAnalysis] = None) -> GestureType:
        """Detect gesture based on pose analysis"""
        
        # Head tilt detection
        if abs(current_pose.head_tilt_angle) > self.TILT_THRESHOLD:
            if current_pose.head_tilt_angle > 0:
                return GestureType.HEAD_TILT_RIGHT
            else:
                return GestureType.HEAD_TILT_LEFT
        
        # Body lean detection
        if abs(current_pose.shoulder_angle) > self.TILT_THRESHOLD:
            if current_pose.shoulder_angle > self.TILT_THRESHOLD:
                return GestureType.LEAN_RIGHT
            elif current_pose.shoulder_angle < -self.TILT_THRESHOLD:
                return GestureType.LEAN_LEFT
        
        # Movement-based gestures (require previous pose)
        if previous_pose:
            # Approach/retreat detection based on bounding box area
            area_ratio = current_pose.bounding_box_area / previous_pose.bounding_box_area
            
            if area_ratio > self.APPROACH_THRESHOLD:
                return GestureType.APPROACH
            elif area_ratio < self.RETREAT_THRESHOLD:
                return GestureType.RETREAT
            
            # Head nod detection (vertical head movement)
            head_y_change = abs(current_pose.head_position[1] - previous_pose.head_position[1])
            if head_y_change > self.NOD_THRESHOLD * 480:  # Assuming 480p height
                return GestureType.HEAD_NOD
        
        return GestureType.UNKNOWN
    
    def detect_hand_gestures(self, hand_landmarks, frame_shape: Tuple[int, int]) -> GestureType:
        """Detect hand-based gestures"""
        if not hand_landmarks:
            return GestureType.UNKNOWN
        
        h, w = frame_shape[:2]
        
        for hand in hand_landmarks:
            landmarks = hand.landmark
            
            # Get hand landmarks
            wrist = landmarks[self.mp_hands.HandLandmark.WRIST]
            thumb_tip = landmarks[self.mp_hands.HandLandmark.THUMB_TIP]
            index_tip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            middle_tip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
            ring_tip = landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP]
            pinky_tip = landmarks[self.mp_hands.HandLandmark.PINKY_TIP]
            
            # Check for hand raise (hand above wrist level)
            fingers_up = 0
            tips = [thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip]
            
            for tip in tips:
                if tip.y < wrist.y:  # Finger is above wrist
                    fingers_up += 1
            
            if fingers_up >= 3:  # At least 3 fingers up
                return GestureType.HAND_RAISE
            
            # Check for wave (horizontal hand movement would require temporal analysis)
            # This is simplified - real wave detection would need motion tracking
            if index_tip.y < wrist.y and middle_tip.y < wrist.y:
                return GestureType.WAVE
        
        return GestureType.UNKNOWN
    
    def execute_mimic_response(self, gesture: GestureType, confidence: float):
        """Execute mimic response for detected gesture"""
        if not self.mimic_enabled or not self.motor_controller:
            logger.info(f"Mimic response disabled or no controller: {gesture.value}")
            return
        
        try:
            # Apply response delay
            time.sleep(self.response_delay)
            
            # Scale response by confidence and intensity
            response_strength = confidence * self.mimic_intensity
            
            if gesture == GestureType.HEAD_TILT_LEFT:
                # Servo tilt left
                angle = int(-20 * response_strength)
                self.motor_controller.set_steering(angle)
                threading.Timer(1.5, lambda: self.motor_controller.set_steering(0)).start()
                
            elif gesture == GestureType.HEAD_TILT_RIGHT:
                # Servo tilt right
                angle = int(20 * response_strength)
                self.motor_controller.set_steering(angle)
                threading.Timer(1.5, lambda: self.motor_controller.set_steering(0)).start()
                
            elif gesture == GestureType.LEAN_LEFT:
                # Stronger left tilt
                angle = int(-25 * response_strength)
                self.motor_controller.set_steering(angle)
                threading.Timer(2.0, lambda: self.motor_controller.set_steering(0)).start()
                
            elif gesture == GestureType.LEAN_RIGHT:
                # Stronger right tilt
                angle = int(25 * response_strength)
                self.motor_controller.set_steering(angle)
                threading.Timer(2.0, lambda: self.motor_controller.set_steering(0)).start()
                
            elif gesture == GestureType.APPROACH:
                # Vehicle moves forward slightly
                speed = int(20 * response_strength)
                duration = 0.8
                self.motor_controller.move_forward(speed, duration)
                
            elif gesture == GestureType.RETREAT:
                # Vehicle moves backward slightly
                speed = int(15 * response_strength)
                duration = 0.6
                self.motor_controller.move_backward(speed, duration)
                
            elif gesture == GestureType.HEAD_NOD:
                # Quick forward-backward nod
                self.motor_controller.move_forward(25, 0.3)
                time.sleep(0.1)
                self.motor_controller.move_backward(20, 0.3)
                
            elif gesture == GestureType.WAVE:
                # Excited wiggle response
                if self.interaction_controller:
                    self.interaction_controller.on_human_gesture("wave")
                else:
                    # Direct wiggle
                    for _ in range(3):
                        self.motor_controller.set_steering(-15)
                        time.sleep(0.3)
                        self.motor_controller.set_steering(15)
                        time.sleep(0.3)
                    self.motor_controller.set_steering(0)
                    
            elif gesture == GestureType.HAND_RAISE:
                # Acknowledging tilt
                if self.interaction_controller:
                    self.interaction_controller.on_human_gesture("hand_raise")
                else:
                    self.motor_controller.set_steering(15)
                    time.sleep(1.0)
                    self.motor_controller.set_steering(0)
            
            logger.info(f"Executed mimic response for {gesture.value} (confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Mimic response error: {e}")
    
    def process_frame(self, frame: np.ndarray) -> List[GestureEvent]:
        """Process a single frame for gesture detection"""
        self.frame_count += 1
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        current_time = time.time()
        detected_gestures = []
        
        # Skip processing if too soon after last gesture
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return detected_gestures
        
        try:
            # Pose detection
            pose_results = self.pose.process(rgb_frame)
            
            if pose_results.pose_landmarks:
                # Analyze current pose
                current_pose = self.analyze_pose(pose_results.pose_landmarks.landmark, frame.shape)
                
                # Get previous pose for temporal analysis
                previous_pose = self.pose_history[-1] if self.pose_history else None
                
                # Detect pose-based gestures
                gesture_type = self.detect_gesture(current_pose, previous_pose)
                
                if gesture_type != GestureType.UNKNOWN:
                    confidence = 0.8  # Base confidence for pose gestures
                    
                    gesture_event = GestureEvent(
                        gesture_type=gesture_type,
                        confidence=confidence,
                        timestamp=current_time,
                        pose_landmarks={
                            'head_tilt': current_pose.head_tilt_angle,
                            'body_center': current_pose.body_center,
                            'bounding_area': current_pose.bounding_box_area
                        }
                    )
                    
                    detected_gestures.append(gesture_event)
                
                # Update pose history
                self.pose_history.append(current_pose)
                if len(self.pose_history) > self.pose_history_size:
                    self.pose_history.pop(0)
                
                self.current_pose = current_pose
                
                # Draw pose landmarks for debugging
                if hasattr(self, 'debug_mode') and self.debug_mode:
                    self.mp_drawing.draw_landmarks(
                        frame, pose_results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            
            # Hand gesture detection
            hand_results = self.hands.process(rgb_frame)
            
            if hand_results.multi_hand_landmarks:
                hand_gesture = self.detect_hand_gestures(hand_results.multi_hand_landmarks, frame.shape)
                
                if hand_gesture != GestureType.UNKNOWN:
                    confidence = 0.7  # Base confidence for hand gestures
                    
                    gesture_event = GestureEvent(
                        gesture_type=hand_gesture,
                        confidence=confidence,
                        timestamp=current_time
                    )
                    
                    detected_gestures.append(gesture_event)
                
                # Draw hand landmarks for debugging
                if hasattr(self, 'debug_mode') and self.debug_mode:
                    for hand_landmarks in hand_results.multi_hand_landmarks:
                        self.mp_drawing.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
            
            # Execute responses for detected gestures
            for gesture_event in detected_gestures:
                if not gesture_event.response_executed:
                    self.execute_mimic_response(gesture_event.gesture_type, gesture_event.confidence)
                    gesture_event.response_executed = True
                    self.last_gesture_time = current_time
                    
                    # Add to history
                    self.gesture_history.append(gesture_event)
                    
                    # Limit history size
                    if len(self.gesture_history) > 50:
                        self.gesture_history.pop(0)
            
            # Add gesture info to frame for debugging
            if detected_gestures:
                for i, gesture in enumerate(detected_gestures):
                    text = f"{gesture.gesture_type.value}: {gesture.confidence:.2f}"
                    cv2.putText(frame, text, (10, 30 + i * 25), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Show current pose info
            if self.current_pose:
                tilt_text = f"Head Tilt: {self.current_pose.head_tilt_angle:.1f}°"
                cv2.putText(frame, tilt_text, (10, frame.shape[0] - 50), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                area_text = f"Area: {int(self.current_pose.bounding_box_area)}"
                cv2.putText(frame, area_text, (10, frame.shape[0] - 25), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        except Exception as e:
            logger.error(f"Frame processing error: {e}")
        
        return detected_gestures
    
    def run_mimic_loop(self, camera_index: int = 0, display: bool = False):
        """Run the main mimic detection loop"""
        self.running = True
        self.debug_mode = display
        
        # Initialize camera
        camera = cv2.VideoCapture(camera_index)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
        
        logger.info("Starting mimic engine loop")
        
        try:
            while self.running:
                ret, frame = camera.read()
                if not ret:
                    logger.error("Failed to read frame from camera")
                    break
                
                # Process frame for gestures
                gestures = self.process_frame(frame)
                
                # Display frame if requested
                if display:
                    cv2.imshow('BUD-EE Mimic Engine', frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord(' '):  # Space to toggle mimic
                        self.mimic_enabled = not self.mimic_enabled
                        logger.info(f"Mimic {'enabled' if self.mimic_enabled else 'disabled'}")
                
                # Small delay for processing
                time.sleep(0.033)  # ~30 FPS
                
        except KeyboardInterrupt:
            logger.info("Mimic loop interrupted by user")
        except Exception as e:
            logger.error(f"Mimic loop error: {e}")
        finally:
            camera.release()
            cv2.destroyAllWindows()
            self.running = False
    
    def stop(self):
        """Stop the mimic engine"""
        self.running = False
        logger.info("Mimic engine stopped")
    
    def set_mimic_enabled(self, enabled: bool):
        """Enable or disable mimic responses"""
        self.mimic_enabled = enabled
        logger.info(f"Mimic responses {'enabled' if enabled else 'disabled'}")
    
    def set_mimic_intensity(self, intensity: float):
        """Set mimic response intensity (0.0 to 2.0)"""
        self.mimic_intensity = max(0.0, min(2.0, intensity))
        logger.info(f"Mimic intensity set to {self.mimic_intensity:.1f}")
    
    def get_gesture_stats(self) -> Dict:
        """Get gesture detection statistics"""
        recent_gestures = [g for g in self.gesture_history 
                          if time.time() - g.timestamp < 300]  # Last 5 minutes
        
        gesture_counts = {}
        for gesture in recent_gestures:
            gesture_type = gesture.gesture_type.value
            gesture_counts[gesture_type] = gesture_counts.get(gesture_type, 0) + 1
        
        return {
            "total_gestures": len(self.gesture_history),
            "recent_gestures": len(recent_gestures),
            "gesture_types": gesture_counts,
            "mimic_enabled": self.mimic_enabled,
            "mimic_intensity": self.mimic_intensity,
            "frame_count": self.frame_count,
            "current_pose_available": self.current_pose is not None
        }

def main():
    """Test function for mimic engine"""
    try:
        mimic = MimicEngine()
        
        print("🤖 BUD-EE Mimic Engine Test")
        print("=" * 40)
        print("Controls:")
        print("  q - Quit")
        print("  Space - Toggle mimic responses")
        print("\nShow your gestures to the camera!")
        
        # Run with display for testing
        mimic.run_mimic_loop(display=True)
        
        # Show final stats
        stats = mimic.get_gesture_stats()
        print(f"\nFinal Stats: {stats}")
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        logger.error(f"Test error: {e}")
    finally:
        if 'mimic' in locals():
            mimic.stop()

if __name__ == "__main__":
    main() 