import cv2
import os
import pickle
import numpy as np
import face_recognition
import telebot
import serial
import requests
import json
import threading
import time

KNOWN_FACES_DIR = r"C:\Users\user\Desktop\known_faces"
ENCODED_FACES_FILE = "face_data.dat"
BOT_TOKEN = "7523195818:AAF7a-cAOG70kGO2whsglPuMxyH_olknXkE"
CHAT_ID = "1599560625"
UNLOCK_THRESHOLD = 0.4
SERIAL_PORT = "COM5"
BAUD_RATE = 115200
DOOR_OPEN_DURATION = 3

bot = telebot.TeleBot(BOT_TOKEN)
pending_approval = False
last_notification_time = 0
notification_cooldown = 30  
known_encodings = []
known_names = []
waiting_for_name_input = False
last_unknown_image = ""

def init_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✅ Serial connected to {SERIAL_PORT}")
        return ser
    except serial.SerialException as e:
        print(f"❌ Couldn't open: {e}")
        return None

ser = init_serial()
if not ser:
    print("⚠️ Continuing without serial connection")

def encode_faces():
    global known_encodings, known_names
    
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True) #create folder if does not exist
    
    temp_encodings = []
    temp_names = []

    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(KNOWN_FACES_DIR, filename)
            image = cv2.imread(path)
            if image is None:
                print(f"⚠️ Ignored: {filename}")
                continue

            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb)
            
            if not encodings:
                print(f"❌ Face not found: {filename}")
                continue

            name = os.path.splitext(filename)[0]
            temp_encodings.append(encodings[0])
            temp_names.append(name)  #add faces to the list of encoded faces
            print(f"✅ Encoded: {name}")

    known_encodings = temp_encodings
    known_names = temp_names
    
    with open(ENCODED_FACES_FILE, "wb") as f:
        pickle.dump((known_encodings, known_names), f) #saves to fail

def load_encodings():
    global known_encodings, known_names
    if os.path.exists(ENCODED_FACES_FILE):
        with open(ENCODED_FACES_FILE, "rb") as f:
            known_encodings, known_names = pickle.load(f)
        print(f"📦 Loaded {len(known_names)} faces")

def add_new_face(image_path, name):
    global known_encodings, known_names
        
    base_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c in (' ', '_')]).rstrip()
    safe_name = base_name
    
    try:
        image = cv2.imread(image_path)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
            
        new_path = os.path.join(KNOWN_FACES_DIR, f"{safe_name}.jpg")
        cv2.imwrite(new_path, image)
        
        known_encodings.append(encodings[0])
        known_names.append(safe_name)
        
        with open(ENCODED_FACES_FILE, "wb") as f:
            pickle.dump((known_encodings, known_names), f)
            
        print(f"✅ Added new face: {safe_name}")
        return safe_name
        
    except Exception as e:
        print(f"Error adding face: {e}")
        return None

def delete_face_by_name(name_to_delete):
    global known_encodings, known_names

    if name_to_delete in known_names:
        index = known_names.index(name_to_delete)
        known_names.pop(index)
        known_encodings.pop(index)
        
        image_path = os.path.join(KNOWN_FACES_DIR, f"{name_to_delete}.jpg")
        if os.path.exists(image_path):
            os.remove(image_path)

        with open(ENCODED_FACES_FILE, "wb") as f: #updates database again after adding face
            pickle.dump((known_encodings, known_names), f)

        print(f"🗑️ Deleted face: {name_to_delete}")
        return True
    else:
        print("⚠️ Name not found in database")
        return False

def open_door():
    if ser is None:
        print("⚠️ No serial connection - simulating door open")
        return
        
    try:
        ser.write(b'OPEN\n')
        print("🚪 Door is opened")
        threading.Timer(DOOR_OPEN_DURATION, close_door).start()
    except Exception as e:
        print(f"Ошибка открытия двери: {e}")

def close_door():
    if ser is None:
        print("⚠️ No serial connection - simulating door close")
        return
        
    try:
        ser.write(b'CLOSE\n')
        print("🚪 Door is closed")
    except Exception as e:
        print(f"Ошибка закрытия двери: {e}")

def send_telegram_with_buttons(image_path):
    global pending_approval, last_notification_time
    
    current_time = time.time()
    if pending_approval and (current_time - last_notification_time < notification_cooldown):
        print("⏳ Notification cooldown")
        return False

    try:
        with open(image_path, "rb") as photo:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                files={"photo": photo},
                data={"chat_id": CHAT_ID, "caption": "❗ Unknown face"}
            )
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "✅ Open Door", "callback_data": "open_door"}],
                [{"text": "❌ Don't Open", "callback_data": "do_not_open"}],
                [{"text": "➕ Add to Database", "callback_data": "add_face"}],
                [{"text": "🗑️ Delete Face", "callback_data": "delete_face"}]
            ]
        }
        
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": "Select action:",
                "reply_markup": keyboard
            }
        )
        
        pending_approval = True
        last_notification_time = current_time
        return True
        
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def listen_for_bot_commands():
    global pending_approval, waiting_for_name_input, last_unknown_image
    
    last_update_id = 0
    
    while True:
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={"offset": last_update_id + 1, "timeout": 5}
            ).json()

            for update in response.get("result", []):
                last_update_id = update["update_id"]
                
                if "callback_query" in update:
                    data = update["callback_query"]["data"]
                    
                    if data == "open_door":
                        print("✅ Access granted by user")
                        open_door()
                        pending_approval = False
                        
                    elif data == "do_not_open":
                        print("⛔ Access denied by user")
                        pending_approval = False
                        
                    elif data == "add_face":
                        print("➕ Add face request")
                        pending_approval = False
                        waiting_for_name_input = True
                        bot.send_message(CHAT_ID, "Please enter the name for this face:")
                    
                    elif data == "delete_face":
                        bot.send_message(CHAT_ID, "Enter the name of the person to delete:")
                        waiting_for_name_input = "delete"

                elif "message" in update and waiting_for_name_input:
                    name = update["message"]["text"].strip()
                    if not name:
                        bot.send_message(CHAT_ID, "Name cannot be empty!")
                        continue

                    if waiting_for_name_input == True:
                        saved_name = add_new_face(last_unknown_image, name)
                        if saved_name:
                            bot.send_message(CHAT_ID, f"✅ Saved as: {saved_name}")
                        else:
                            bot.send_message(CHAT_ID, "❌ Failed to add face")
                        try:
                            os.remove(last_unknown_image)
                        except:
                            pass

                    elif waiting_for_name_input == "delete":
                        if delete_face_by_name(name):
                            bot.send_message(CHAT_ID, f"🗑️ {name} deleted successfully!")
                        else:
                            bot.send_message(CHAT_ID, f"❌ {name} not found!")

                    waiting_for_name_input = False
                        
        except Exception as e:
            print(f"Telegram error: {e}")
        time.sleep(1)

def recognize_faces():
    global last_unknown_image
    
    cap = cv2.VideoCapture(1)
    last_recognized_time = 0
    cooldown_period = 5
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
            
        current_time = time.time()
        
        if (pending_approval or 
            (current_time - last_recognized_time < cooldown_period) or
            waiting_for_name_input):
            
            if waiting_for_name_input:
                cv2.putText(frame, "Enter name in Telegram...", (20, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            cv2.imshow("Face Recognition", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue
            
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)
        face_encodings = face_recognition.face_encodings(rgb, face_locations)
        
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_encodings, face_encoding, UNLOCK_THRESHOLD)
            name = "Unknown"
            color = (0, 0, 255)
            message = "Access Denied"
            
            if True in matches:
                first_match_index = matches.index(True)
                name = known_names[first_match_index]
                color = (0, 255, 0)
                message = "Access Granted"
                last_recognized_time = current_time
                print(f"✅ Recognized: {name}")
                open_door()
            else:
                timestamp = int(time.time())
                last_unknown_image = f"unknown_{timestamp}.jpg"
                cv2.imwrite(last_unknown_image, frame)
                send_telegram_with_buttons(last_unknown_image)
                print("📨 Sent unknown face to Telegram")
            
        cv2.imshow("Face Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    load_encodings()
    threading.Thread(target=listen_for_bot_commands, daemon=True).start()
    recognize_faces()