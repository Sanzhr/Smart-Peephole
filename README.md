# Smart Peephole – Face Recognition Security System

## Description
This project implements a smart security system for door access control using real-time face recognition.

The system detects and recognizes faces using a camera. If a known person is identified, access is granted automatically by activating a servo motor (simulated door lock).  

If an unknown person is detected, the system captures an image and sends it to the user via Telegram, allowing remote decision-making.

The project combines computer vision, embedded systems, and remote control via messaging platform.

## Features
- Real-time face recognition using OpenCV and face_recognition
- Automatic door unlocking for authorized users
- Detection of unknown лица with image capture
- Telegram bot integration for remote control
- Interactive decision system via Telegram:
  - Open door remotely
  - Add new person to database
  - Delete person from database
- Dynamic face database management

## System Workflow
1. Camera captures video stream
2. Face is detected and compared with known database
3. If face is recognized:
   - Servo motor activates (door opens)
4. If face is unknown:
   - Photo is captured
   - Notification is sent via Telegram
   - User chooses action:
     - Open door
     - Add to database
     - Ignore or delete

## Technologies Used
- Python
- OpenCV
- face_recognition
- Telegram Bot API (pyTelegramBotAPI)
- Serial communication

## Hardware
- Arduino / ESP32 (servo motor control)
- Servo motor (door simulation)
- Webcam or USB camera
- PC running Python script

## Face Database
Faces are stored in the `known_faces/` directory.

Structure example:
