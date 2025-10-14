import cv2
import time
import os
import threading

def main(device_id=0, stop_event=None):
    """Non-blocking webcam loop. If stop_event is provided it will stop when set."""
    if stop_event is None:
        stop_event = threading.Event()

    os.makedirs("snapshots", exist_ok=True)
    cap = cv2.VideoCapture(device_id)
    if not cap.isOpened():
        print(f"Error: Could not open webcam (device {device_id}).")
        return

    frame_count = 0
    start_time = time.time()

    try:
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from webcam.")
                break

            frame_count += 1
            elapsed = max(1e-6, time.time() - start_time)
            fps = frame_count / elapsed
            cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

            cv2.imshow("Camera", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                stop_event.set()
                break
            if key == ord('s'):
                ts = int(time.time())
                filename = os.path.join("snapshots", f"snapshot_{ts}.jpg")
                cv2.imwrite(filename, frame)
                print("Saved", filename)
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera closed.")

if __name__ == "__main__":
    main()