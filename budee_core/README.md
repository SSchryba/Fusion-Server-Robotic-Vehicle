# 🤖 BUD-EE - Autonomous Emotional AI Vehicle

**BUD-EE** is a physically embodied conversational and emotional AI system designed to run on a Raspberry Pi 4-powered mobile vehicle. The system integrates real-time computer vision, emotional cognition, gesture mirroring, and server-based hybrid AI to create an autonomous, emotionally expressive AI companion that can interact naturally with humans.

## 🌟 System Overview

BUD-EE combines multiple AI technologies to create a complete autonomous emotional AI vehicle:

- **Vision-Motor Fusion**: Real-time object tracking and navigation
- **Emotion Engine**: Dynamic emotional state management
- **Interaction Rituals**: Complex behavioral engagement patterns  
- **Gesture Mirroring**: Human gesture detection and mimicry
- **Audio Control**: Synchronized speech and sound with fan effects
- **Server Integration**: WebSocket connection to hybrid AI backend
- **Auto-Calibration**: Self-configuring motor and vision systems

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BUD-EE SYSTEM                            │
├─────────────────────────────────────────────────────────────┤
│  🎭 Emotion Engine          🎯 Vision Motor Fusion         │
│  - Emotional states         - Object detection & tracking  │
│  - Context awareness        - Servo/motor control          │
│  - Behavior triggers        - Real-time navigation         │
├─────────────────────────────────────────────────────────────┤
│  🤝 Interaction Ritual      👤 Mimic Engine                │
│  - Engagement sequences     - Gesture recognition          │
│  - Response patterns        - Human pose mirroring         │
│  - Disappointment handling  - Adaptive responses           │
├─────────────────────────────────────────────────────────────┤
│  🔊 Audio Control           🌐 WebSocket Client             │
│  - TTS & sound effects     - Server communication          │
│  - Fan synchronization     - Real-time AI integration      │
│  - Emotion-based audio     - Command processing            │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Hardware Requirements

### Core Components
- **Raspberry Pi 4** (4GB+ recommended)
- **Front-facing Camera** (USB or CSI - /dev/video0)
- **Servo Motor** (steering control - GPIO 4)
- **L298N H-Bridge** (rear motor control)
- **USB Speaker** (audio output)
- **Cooling Fan** (GPIO 20)

### GPIO Pin Configuration (BCM Numbering)

🧩 **Raspberry Pi 4 — Primary Controller Wiring Table**

| Function | Component | GPIO Pin (BCM) | Physical Pin # | Connection Type |
|----------|-----------|----------------|----------------|-----------------|
| Rear Motor In1 | L298N IN1 | GPIO17 | Pin 11 | Digital OUT |
| Rear Motor In2 | L298N IN2 | GPIO27 | Pin 13 | Digital OUT |
| Motor Enable (ENA) | L298N ENA (PWM) | GPIO22 | Pin 15 | PWM (via pigpio) |
| Steering Servo | Servo PWM signal | GPIO4 | Pin 7 | PWM (via pigpio) |
| Fan Control | Cooling Fan (MOSFET Gate) | GPIO20 | Pin 38 | Digital OUT |
| I2C SDA | I2C Level Shifter / OLED | GPIO2 (SDA1) | Pin 3 | I2C |
| I2C SCL | I2C Level Shifter / OLED | GPIO3 (SCL1) | Pin 5 | I2C |
| USB Audio | USB Mini Speaker | — | USB Port | Audio OUT |
| USB Microphone | USB Mic | — | USB Port | Audio IN |
| Front Camera | ELP USB Autofocus Cam | — | USB Port | Video IN |
| Rear Cam (optional) | Innomaker USB2.0 Cam | — | USB Port | Video IN |
| 5V Power Output | All devices via buck conv. | — | Pins 2/4 | 5V |
| GND (shared) | All devices | — | Pins 6/9/14/20/30… | GND |

🧩 **Raspberry Pi Zero 2 W — Secondary Controller Wiring Table**

| Function | Component | GPIO Pin (BCM) | Physical Pin # | Connection Type |
|----------|-----------|----------------|----------------|-----------------|
| I2C SDA | Level Shifter | GPIO2 | Pin 3 | I2C |
| I2C SCL | Level Shifter | GPIO3 | Pin 5 | I2C |
| Camera Feed | Innomaker Cam | — | USB Port | Video IN |
| Logic + Boot comms | UART (optional to Pi 4) | GPIO14/15 | Pins 8/10 | UART TX/RX |
| 5V Power Input | Buck Converted Input | — | Pin 2 or 4 | Power |
| GND | Shared Ground | — | Pin 6 or 9 | GND |

⚡ **Power Distribution**

| Source | Destination Components | Method |
|--------|------------------------|---------|
| 11.1V Li-ion | Step-down via buck converter | 12V → 5V/3.3V |
| 5V Buck | RPi4, Fan, L298N, Servo | From battery system |
| 3.3V Buck | I2C devices, logic shifters | For level-safe comms |

🎛️ **Level Shifter (I2C)**

| Direction | From → To | Used For |
|-----------|-----------|----------|
| 3.3V → 5V | Pi GPIO → I2C | OLEDs, sensors |
| 5V → 3.3V | Sensors → Pi | Logic safety |

```
Quick Reference:
GPIO 4  - Servo PWM (steering)
GPIO 17 - Motor IN1 (L298N)
GPIO 27 - Motor IN2 (L298N) 
GPIO 22 - Motor PWM Enable
GPIO 20 - Cooling Fan Control
```

### Optional Components
- **USB Microphone** (voice input)
- **Rear Camera** (/dev/video1 - backup)
- **LED strips** (visual feedback)
- **Ultrasonic sensors** (collision avoidance)

## 📦 Installation

### 1. System Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv git cmake pkg-config
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y espeak espeak-data alsa-utils
sudo apt install -y pigpio python3-pigpio

# Enable pigpio daemon
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Enable camera (if using CSI camera)
sudo raspi-config  # Enable camera interface
```

### 2. Install BUD-EE

```bash
# Clone repository
git clone <repository-url>
cd budee_core

# Create virtual environment
python3 -m venv budee_env
source budee_env/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x *.py
```

### 3. Audio Setup

```bash
# Test audio output
aplay /usr/share/sounds/alsa/Front_Left.wav

# Configure default audio device (if needed)
sudo nano /etc/asound.conf
```

## 🚀 Quick Start

### 1. Initial Calibration

**Important**: Run calibration before first use!

```bash
cd budee_core
python3 calibration_routine.py
```

Follow the on-screen instructions to calibrate:
- Servo steering angles
- Motor movement distances  
- Vision detection thresholds

### 2. Start BUD-EE System

```bash
# Full integrated system
python3 budee_main.py

# Or individual modules for testing
python3 vision_motor_fusion.py    # Vision + motor control
python3 mimic_engine.py          # Gesture mirroring  
python3 interaction_ritual.py    # Behavior patterns
python3 audio_control.py         # Audio system
```

### 3. Connect to Server (Optional)

```bash
# Start WebSocket client for server integration
python3 budee_websocket_client.py
```

## 🎮 Usage & Interaction

### Basic Interaction Flow

1. **Detection**: BUD-EE detects human presence via camera
2. **Engagement**: Plays greeting sound, moves forward slightly, activates fan
3. **Waiting**: Listens for human response (voice/gesture)
4. **Response**: Reacts based on interaction type:
   - **Positive**: Excited sounds, happy wiggling
   - **No response**: Multiple attempts, then disappointment sequence
   - **Gesture**: Mirrors human movements

### Gesture Commands

- **Head Tilt Left/Right**: BUD-EE tilts servo left/right
- **Hand Wave**: Excited wiggle response + trill sound
- **Hand Raise**: Acknowledgment tilt + greeting sound
- **Approach/Retreat**: BUD-EE follows/backs away
- **Body Lean**: Mirrors lean direction

### Emotional States

BUD-EE expresses emotions through movement, sound, and behavior:

- **😊 Happy**: Energetic movements, positive sounds
- **😢 Sad**: Slow movements, low-pitched sounds  
- **😰 Fear**: Defensive posture, retreat behaviors
- **🤔 Curious**: Investigative movements, alert posture
- **😤 Frustrated**: Sharp movements, disappointed sounds
- **😴 Lonely**: Seeking behaviors, calling sounds

## ⚙️ Configuration

### Calibration Parameters

Edit `budee_calibration_map.json`:

```json
{
  "servo_map": {
    "-30": 1300,    // Left extreme PWM
    "0": 1500,      // Center position  
    "30": 1700      // Right extreme PWM
  },
  "motion_gain": {
    "baseline_box_area": 5400,     // Reference detection size
    "forward_threshold": 1.2,      // Move forward trigger
    "reverse_threshold": 0.8       // Move backward trigger
  },
  "motor_speed_map": {
    "low": 20,      // Conservative speed
    "normal": 40,   // Standard speed
    "fast": 80      // Maximum speed
  }
}
```

### Emotion Configuration

Modify emotion behaviors in `emotion_engine.py`:

```python
emotion_behaviors = {
    EmotionType.EXCITED: {
        "audio": ["excited", "happy"],
        "movement": "energetic", 
        "mimic_intensity": 1.5,
        "interaction_eagerness": 1.0
    }
}
```

## 🔌 Server Integration

### WebSocket Protocol

BUD-EE communicates with fusion AI servers via WebSocket:

```json
{
  "type": "emotion",
  "timestamp": 1234567890,
  "data": {
    "emotion": "excited",
    "intensity": 0.8,
    "duration": 30.0
  }
}
```

### Message Types

- **emotion**: Emotion state changes
- **servo**: Steering commands
- **motor_cmd**: Movement commands  
- **sound**: Audio playback
- **chat**: AI conversation
- **status**: System status updates

### Server URL Configuration

```python
config = {
    "server_url": "ws://your-server:8000/ws/vehicle"
}
```

## 🧪 Testing & Development

### Individual Module Testing

```bash
# Test vision system
python3 vision_motor_fusion.py

# Test gesture recognition  
python3 mimic_engine.py

# Test audio system
python3 audio_control.py

# Test emotion engine
python3 emotion_engine.py

# Test interaction patterns
python3 interaction_ritual.py

# Test server communication
python3 budee_websocket_client.py
```

### Debug Mode

Enable debug visualization:

```python
# In budee_main.py
config = {
    "debug_mode": True  # Shows camera feed with detections
}
```

### Safety Testing

```python
# Test emergency stop
budee.emergency_stop()

# Test motor limits
budee.vision_motor.manual_control(angle=30, speed=50, direction='forward', duration=1.0)
```

## 🛡️ Safety Features

### Hardware Safety
- **Speed Limits**: Maximum motor speeds capped
- **Angle Limits**: Servo angles restricted to safe range
- **Timeout Protection**: Auto-stop after movement duration
- **Emergency Stop**: Immediate halt of all systems

### Software Safety  
- **Rate Limiting**: Prevents command flooding
- **Input Validation**: Sanitizes all control inputs
- **Error Recovery**: Graceful handling of failures
- **Collision Avoidance**: Visual-based obstacle detection

### Protected Operations
- System file access restricted
- GPIO operations validated
- Network commands filtered
- Audio levels limited

## 📊 System Monitoring

### Real-time Stats

```python
# Get system statistics
stats = budee.get_system_stats()
print(f"Uptime: {stats['uptime']:.1f}s")
print(f"Emotion: {stats['emotion']['emotion']}")
print(f"Interactions: {stats['interactions']}")
```

### Log Analysis

```bash
# View system logs
tail -f /var/log/budee.log

# Check GPIO usage
sudo pigpio
```

### Performance Metrics
- Vision processing: ~30 FPS
- Emotion updates: 5 second intervals  
- Audio latency: <100ms
- WebSocket ping: <50ms

## 🔧 Troubleshooting

### Common Issues

**Camera Not Detected**
```bash
# Check camera connection
lsusb | grep -i camera
ls /dev/video*

# Test camera access
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.read()[0])"
```

**Audio Problems**
```bash
# Test audio output
aplay /usr/share/sounds/alsa/Front_Left.wav

# Check audio devices
aplay -l
```

**GPIO Errors**
```bash
# Check pigpio daemon
sudo systemctl status pigpiod

# Restart pigpio
sudo systemctl restart pigpiod
```

**WebSocket Connection Failed**
```bash
# Test server connectivity
ping your-server-ip
telnet your-server-ip 8000
```

### System Recovery

```bash
# Soft reset
sudo systemctl restart budee

# Hard reset (emergency)
sudo pkill -f python3
sudo systemctl restart pigpiod
```

## 🎯 Advanced Features

### Custom Gestures

Add new gesture recognition:

```python
# In mimic_engine.py
def detect_custom_gesture(self, landmarks):
    # Your gesture detection logic
    if custom_condition:
        return GestureType.CUSTOM_GESTURE
```

### Behavior Modification

Create new interaction patterns:

```python
# In interaction_ritual.py  
def custom_interaction_sequence(self):
    # Your custom behavior
    self.execute_movement({"action": "custom", "params": {}})
    self.play_audio_with_fan("custom_sound.wav")
```

### AI Integration

Connect to different AI backends:

```python
# Custom WebSocket handlers
async def handle_custom_message(self, data):
    # Process custom AI commands
    pass
```

## 📁 File Structure

```
budee_core/
├── budee_main.py                 # Main system coordinator
├── vision_motor_fusion.py        # Vision + motor control
├── calibration_routine.py        # Auto-calibration system
├── interaction_ritual.py         # Behavior patterns
├── mimic_engine.py              # Gesture mirroring
├── audio_control.py             # Audio + fan control
├── budee_websocket_client.py    # Server communication
├── emotion_engine.py            # Emotional AI
├── budee_calibration_map.json   # Calibration data
├── requirements.txt             # Dependencies
├── README.md                    # This file
└── sounds/                      # Audio files
    ├── excited/
    ├── greeting/
    ├── disappointed/
    └── ...
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include unit tests for new features
- Test on actual hardware before submitting
- Update documentation for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenCV** - Computer vision framework
- **Mediapipe** - Human pose detection
- **pigpio** - Raspberry Pi GPIO control  
- **pygame** - Audio processing
- **websockets** - Real-time communication

---

**Built with ❤️ for the future of embodied AI**

For support, questions, or collaboration opportunities, please open an issue or contact the development team.

🤖 **BUD-EE**: Where artificial intelligence meets physical presence! 