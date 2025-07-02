import cv2, time, pickle
import numpy as np
import face_recognition


def enroll(tolerance: float = 0.6, frames_per_pose: int = 5):
    """
    Đăng ký gương mặt với 5 tư thế và lưu xuống DB.
    - user_name        : tên/ID để lưu
    - tolerance        : ngưỡng so khớp (dành để gộp các vector tương tự)
    - frames_per_pose  : số frame sẽ chụp cho mỗi tư thế
    Kết quả: tạo FaceProfile (name, encoding pickled)
    """

    directions = [
        ("NHIN THANG",   (0, 0)),
        ("QUAY TRAI",    (-30, 0)),
        ("QUAY PHAI",    (30, 0)),
        ("NGANG LEN",    (0, -20)),
        ("CUI XUONG",    (0, 20)),
    ]

    cap = cv2.VideoCapture(0)
    encodings = []

    for label, _ in directions:
        collected = 0
        start = time.time()
        while collected < frames_per_pose:
            ret, frame = cap.read()
            if not ret:
                continue

            # Hiển thị hướng dẫn
            cv2.putText(frame, f"HAY {label}", (30, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Enroll", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC = hủy
                cap.release()
                cv2.destroyAllWindows()
                print("Huỷ bỏ đăng ký")
                return

            # Cứ 1s kiểm tra lấy 1 frame
            if time.time() - start > 1:
                start = time.time()
                locs = face_recognition.face_locations(frame)
                if len(locs) != 1:
                    continue
                enc = face_recognition.face_encodings(frame, locs)[0]
                encodings.append(enc)
                collected += 1
                print(f"  + Đã lấy {collected}/{frames_per_pose} frame cho tư thế {label}")

    cap.release()
    cv2.destroyAllWindows()

    #Gộp vector rất giống nhau
    filtered = []
    for v in encodings:
        if not any(face_recognition.face_distance([u], v)[0] < tolerance for u in filtered):
            filtered.append(v)

    #Tính mean để ra “vector đại diện”
    rep = np.mean(filtered, axis=0)
    return rep

