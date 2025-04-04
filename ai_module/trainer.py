# ai_module/trainer.py
import face_recognition
import os
import pickle

def encode_faces(base_path="static/uploads"):
    known_encodings = []
    known_names = []

    # Duyệt từng thư mục = từng sinh viên
    for student_folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, student_folder)

        if not os.path.isdir(folder_path):
            continue  # Bỏ qua file lẻ

        for filename in os.listdir(folder_path):
            if filename.endswith(".jpg") or filename.endswith(".png"):
                path = os.path.join(folder_path, filename)
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)

                if encodings:
                    known_encodings.append(encodings[0])
                    known_names.append(student_folder)  # MSSV là tên thư mục
                else:
                    print(f"❌ Không tìm thấy khuôn mặt trong {path}")

    # Lưu file encode
    with open("ai_module/encodings.pkl", "wb") as f:
        pickle.dump((known_encodings, known_names), f)

    print(f"✅ Đã encode xong {len(known_names)} khuôn mặt.")

if __name__ == "__main__":
    encode_faces()
