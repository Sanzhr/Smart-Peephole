This is a smart security system that uses real-time face recognition to control door access. The system integrates with Telegram to notify the admin when an unknown person attempts to enter, and gives remote control options such as opening the door, adding the person to the database, or deleting faces from the database.

Features)
- Real-time face recognition using OpenCV and `face_recognition`
- Automatic door opening for recognized faces via serial communication
- Captures photo and notifies admin via Telegram when face is unknown
- Admin can:
  - Open the door remotely
  - Add the person to the face database
  - Delete faces from the database via Telegram
- Supports storing and managing multiple known faces
- Robust and easy-to-extend
  
Hardware)
- ESP32, Arduino, or similar microcontroller (connected via serial)
- Camera (webcam or USB camera)

Python Libraries)
Install using `pip install -r requirements.txt` or individually:
- `opencv-python`
- `face_recognition`
- `pyTelegramBotAPI`
- `pyserial`
- `requests`

Telegram Bot)
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram user ID or group chat ID
- 
Configurations)
BOT_TOKEN = 'your_bot_token_here'
CHAT_ID = 'your_telegram_chat_id_here'
SERIAL_PORT = 'COM3' (or '/dev/ttyUSB0' for Linux)

Face Database Setup)
The system uses a folder called known_faces/ to store the face database.
Each subfolder inside known_faces/ represents one person. The name of the folder is treated as the person's name.
For example=>
known_faces/
├── Alice/
│   ├── Alice_1.jpg
│   └── Alice_2.jpg
├── Bob/
│   └── bob_face.jpg

You can add one or more clear photos of each person in their respective folder. During runtime, the system will load these faces and recognize them automatically.

Notes)
1)Ensure good lighting and clear face images for better recognition accuracy.
2)You can improve performance by resizing frames in the code.
3)For deployment, consider using a Raspberry Pi or Jetson Nano with USB camera and GPIO relay.

Telegram Commands)
You can control the system via Telegram bot. When an unknown face is detected, the bot sends a photo and shows buttons like:
✅ Open Door – remotely open the door
➕ Add to Database – add the person to the known faces
🗑️ Delete Face – remove someone from the database

...
