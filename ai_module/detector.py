import cv2
import face_recognition
import pickle
import requests
import os
from datetime import datetime

# Load dữ liệu khuôn mặt
with open("ai_module/encodings.pkl", "rb") as f:
    known_encodings, known_names = pickle.load(f)

# Thư mục lưu ảnh điểm danh
photo_dir = "static/attendance_photos"
os.makedirs(photo_dir, exist_ok=True)

# Mở camera
video = cv2.VideoCapture(0)
if not video.isOpened():
    print("🚫 Không thể mở webcam.")
    exit()

detected_names = set()

try:
    while True:
        ret, frame = video.read()
        if not ret:
            print("❌ Không đọc được frame từ camera.")
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, faces)

        for face_encoding, face_loc in zip(encodings, faces):
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                matched_idx = matches.index(True)
                name = known_names[matched_idx]

                if name not in detected_names:
                    detected_names.add(name)

                    now = datetime.now()
                    date_str = now.strftime("%Y-%m-%d")
                    time_str = now.strftime("%H:%M:%S")
                    status = "Đúng giờ" if now.hour < 8 else "Trễ"

                    filename = f"{name}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
                    save_path = os.path.join(photo_dir, filename)
                    cv2.imwrite(save_path, frame)
                    image_path = save_path.replace("\\", "/")

                    print(f"✅ Nhận diện: {name} lúc {time_str} - {status}")
                    print(f"🖼️ Đã lưu ảnh: {image_path}")

                    try:
                        response = requests.post("http://127.0.0.1:5000/api/mark_attendance", json={
                            "student_id": name,
                            "date": date_str,
                            "time": time_str,
                            "status": status,
                            "image_path": image_path
                        })

                        if response.status_code == 200:
                            print("📤 Gửi điểm danh thành công.")
                        else:
                            print("⚠️ Gửi điểm danh thất bại:", response.text)

                    except Exception as e:
                        print("🚫 Lỗi khi gửi dữ liệu về Flask:", e)

            # Vẽ khung và tên
            top, right, bottom, left = face_loc
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

        cv2.imshow("📷 Camera - Nhấn Q để thoát", frame)
        if cv2.waitKey(10) & 0xFF == ord("q"):
            print("👋 Đã nhấn Q – thoát điểm danh.")
            break

finally:
    video.release()
    cv2.destroyAllWindows()
    os._exit(0)  # cưỡng bức thoát hoàn toàn nếu treo
