import logging
import os
from contextlib import contextmanager

# Suppress OpenCV warnings BEFORE importing cv2
os.environ['OPENCV_LOG_LEVEL'] = 'SILENT'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'

import cv2
import re
import numpy as np
import time
import threading
import queue
import insightface
import gc  # Garbage collection

logging.getLogger("insightface").setLevel(logging.ERROR)
logging.getLogger("onnxruntime").setLevel(logging.ERROR)

def _initialize_camera_robust():
    """Try multiple methods to initialize camera"""
    
    # Method 1: Try different backends first (often more reliable)
    backends = [
        (cv2.CAP_V4L2, "V4L2"),           # Default Linux backend - try first
        (cv2.CAP_GSTREAMER, "GStreamer"), # Often works better on Linux
        (cv2.CAP_ANY, "ANY")              # Let OpenCV choose
        # Note: Removed FFMPEG as it's primarily for video files, not live cameras
    ]
    
    for backend, name in backends:
        try:
            cap = cv2.VideoCapture(0, backend)
            if cap.isOpened():
                # Give the camera a moment to initialize
                time.sleep(0.2)  # Reduced wait time
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Set optimal settings
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    return cap
                else:
                    cap.release()
        except Exception:
            # Silently continue to next backend
            pass
    
    # Method 2: Try different camera indices (fallback)
    for camera_index in [0, 1, 2]:
        try:
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                # Give the camera a moment to initialize
                time.sleep(0.2)
                # Test if we can actually read a frame
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Set optimal settings
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    return cap
                else:
                    cap.release()
        except Exception:
            # Silently continue to next camera index
            pass
    
    return None

# Global model and app cache
app = None
reference_embeddings = None
preloading_complete = False
camera_ready = False
global_camera = None

# Context manager to silence native output
@contextmanager
def suppress_native_output():
    try:
        orig_stdout_fd = os.dup(1)
        orig_stderr_fd = os.dup(2)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(orig_stdout_fd, 1)
        os.dup2(orig_stderr_fd, 2)
        os.close(devnull)
        os.close(orig_stdout_fd)
        os.close(orig_stderr_fd)


def preload_everything():
    """Preload model, reference embeddings, and camera in background"""
    global app, reference_embeddings, preloading_complete, camera_ready, global_camera
    
    try:

        
        # Load InsightFace model
        with suppress_native_output():
            app = insightface.app.FaceAnalysis(name="buffalo_sc", providers=['CPUExecutionProvider'])
            app.prepare(ctx_id=0, det_size=(320, 320))

        
        # Load reference embeddings
        def normalize(emb):
            return emb / np.linalg.norm(emb)
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        ref_dir = os.path.join(project_root, "assets", "references")
        
        reference_embeddings = {}
        
        for filename in os.listdir(ref_dir):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                path = os.path.join(ref_dir, filename)
                img = cv2.imread(path)
                if img is None:
                    continue

                faces = app.get(img)
                if len(faces) == 0:
                    continue

                embedding = normalize(faces[0].embedding)
                label = os.path.splitext(filename)[0]
                label = re.sub(r'\d+$', '', label)
                label = re.sub(r'[^A-Za-z0-9_\-]', '_', label)
                label = label.capitalize()  # Capitalize first character

                if label not in reference_embeddings:
                    reference_embeddings[label] = []
                reference_embeddings[label].append(embedding)

        for label in reference_embeddings:
            reference_embeddings[label] = np.array(reference_embeddings[label])

        
        # Pre-initialize camera 
        global_camera = _initialize_camera_robust()
        if global_camera is not None and global_camera.isOpened():
            camera_ready = True
        else:
            camera_ready = False
        
        preloading_complete = True

        return True
        
    except FileNotFoundError as e:
        print(f"Preloading failed: {e}")
        if "references" in str(e):
            return 3  # Reference folder error
        return False
    except Exception as e:
        print(f"Preloading failed: {e}")
        return False


def reinitialize_camera():
    """Reinitialize the camera when it becomes available again"""
    global global_camera, camera_ready
    try:
        # Clean up old camera reference
        if global_camera is not None:
            global_camera.release()
        
        # Try to create new camera connection using robust method
        global_camera = _initialize_camera_robust()
        if global_camera is not None and global_camera.isOpened():
            camera_ready = True
            return True
        else:
            global_camera = None
            camera_ready = False
            return False
    except Exception as e:
        print(f"Camera reinitialization error: {e}")
        global_camera = None
        camera_ready = False
        return False

def cleanup_camera():
    """Cleanup the global camera"""
    global global_camera, camera_ready
    try:
        if global_camera is not None and global_camera.isOpened():
            global_camera.release()
            global_camera = None
            camera_ready = False

    except Exception as e:
        print(f"Error releasing camera: {e}")


def safe_exit(cap=None):
    """Close the camera safely (headless mode)."""
    if cap is not None and cap.isOpened():
        cap.release()
    print("Camera safely closed.")


def quick_detect():
    """Ultra-fast detection using preloaded model and camera"""
    global app, reference_embeddings, preloading_complete, camera_ready, global_camera  # pylint: disable=global-variable-not-assigned
    
    if not preloading_complete:
        print("System not ready, please wait...")
        return []
    
    if not camera_ready:
        if reinitialize_camera():
            print("Camera reconnected")
        else:
            print("Camera reinitialization failed")
            return 4  # Return camera error code

    result = _run_detection_with_preloaded_camera()
    
    # If camera error occurred, try to reinitialize for next time
    if result == 4:
        reinitialize_camera()
    
    return result


def main():
    global app, reference_embeddings, preloading_complete  # pylint: disable=global-variable-not-assigned

    # If not preloaded, do it now (slower)
    if not preloading_complete:
        print("Preloading not complete, initializing now...")
        if not preload_everything():
            return 3
    
    return _run_detection()


def _run_detection_with_preloaded_camera():
    """Ultra-fast detection using preloaded camera"""
    global app, reference_embeddings, global_camera  # pylint: disable=global-variable-not-assigned
    
    def normalize(emb):
        return emb / np.linalg.norm(emb)

    def distance_to_confidence(dist, max_dist=2.0):
        return max(0.0, min(1.0, 1.0 - dist / max_dist))
    
    THRESHOLD = 1

    def recognize_face(face_embedding):
        best_match = None
        best_score = float("inf")
        for label, embeddings in reference_embeddings.items():
            distances = np.linalg.norm(embeddings - face_embedding, axis=1)
            score = np.min(distances)
            if score < best_score:
                best_score = score
                best_match = label
        if best_score < THRESHOLD:
            return best_match, best_score
        else:
            return "Unknown", best_score

    # Use pre-initialized camera - but check if it's still connected
    cap = global_camera
    if not cap.isOpened():
        print("Pre-initialized camera not available")
        return 4
    
    # Test if camera is actually working by trying to read a frame
    test_ret, test_frame = cap.read()
    if not test_ret:
        print("Camera disconnected or not working")
        return 4

    # Threading for processing
    frame_queue = queue.Queue(maxsize=1)
    result_queue = queue.Queue(maxsize=1)
    stop_event = threading.Event()

    detected_names = set()
    known_face_detected = False

    def recognition_worker():
        while not stop_event.is_set():
            if frame_queue.empty():
                time.sleep(0.01)
                continue
            frame = frame_queue.get()
            faces = app.get(frame)
            results = []
            for face in faces:
                emb = normalize(face.embedding)
                name, dist = recognize_face(emb)
                confidence = distance_to_confidence(dist)
                box = face.bbox.astype(int)
                results.append((box, name, confidence))
            if not result_queue.empty():
                try:
                    result_queue.get_nowait()
                except Exception:
                    pass
            result_queue.put(results)
            time.sleep(0.02)

    thread = threading.Thread(target=recognition_worker, daemon=True)
    thread.start()
    


    frame_count = 0
    last_results = []

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame from webcam - camera disconnected.")
                return 4  # Return camera error code

            frame_count += 1

            if frame_count % 1 == 0 and frame_queue.empty():
                frame_queue.put(frame.copy())

            if not result_queue.empty():
                last_results = result_queue.get()

            # Process detection results (headless - no visual display)
            for box, name, confidence in last_results:
                if name != "Unknown" and name not in detected_names:
                    detected_names.add(name)
                    print(f"Person detected: {name}")
                    known_face_detected = True

            # Clean up memory periodically
            if frame_count % 200 == 0:
                gc.collect()

            # Exit when face detected
            if known_face_detected:
                stop_event.set()
                break

            # Small delay to prevent excessive CPU usage
            time.sleep(0.01)

    except Exception as e:
        print(f"Error during webcam processing: {e}")
    finally:
        # Ensure thread is properly stopped
        stop_event.set()
        if thread.is_alive():
            thread.join(timeout=1.0)
        
        # Don't release the camera - keep it for next use
    
    return list(detected_names)


def _run_detection():
    """Core detection logic using preloaded data"""
    global app, reference_embeddings  # pylint: disable=global-variable-not-assigned
    
    # -----------------------------
    # HELPER FUNCTIONS
    # -----------------------------
    def normalize(emb):
        return emb / np.linalg.norm(emb)

    def distance_to_confidence(dist, max_dist=2.0):
        return max(0.0, min(1.0, 1.0 - dist / max_dist))

    THRESHOLD = 1

    def recognize_face(face_embedding):
        best_match = None
        best_score = float("inf")
        for label, embeddings in reference_embeddings.items():
            distances = np.linalg.norm(embeddings - face_embedding, axis=1)
            score = np.min(distances)
            if score < best_score:
                best_score = score
                best_match = label
        if best_score < THRESHOLD:
            return best_match, best_score
        else:
            return "Unknown", best_score

    # -----------------------------
    # THREADING SETUP
    # -----------------------------
    frame_queue = queue.Queue(maxsize=1)
    result_queue = queue.Queue(maxsize=1)
    stop_event = threading.Event()

    detected_names = set()
    known_face_detected = False

    def recognition_worker():
        while not stop_event.is_set():
            if frame_queue.empty():
                time.sleep(0.01)
                continue
            frame = frame_queue.get()
            faces = app.get(frame)
            results = []
            for face in faces:
                emb = normalize(face.embedding)
                name, dist = recognize_face(emb)
                confidence = distance_to_confidence(dist)
                box = face.bbox.astype(int)
                results.append((box, name, confidence))
            if not result_queue.empty():
                try:
                    result_queue.get_nowait()
                except Exception:
                    pass
            result_queue.put(results)
            time.sleep(0.02)

    # -----------------------------
    # START WEBCAM & THREAD
    # -----------------------------
    cap = _initialize_camera_robust()
    if cap is None or not cap.isOpened():
        if cap is not None:
            safe_exit(cap)
        print("Webcam could not be opened with any method.")
        return 4

    thread = threading.Thread(target=recognition_worker, daemon=True)
    thread.start()
    

    frame_count = 0
    last_results = []

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame from webcam - camera disconnected.")
                safe_exit(cap)
                return 4  # Return camera error code

            frame_count += 1

            if frame_count % 1 == 0 and frame_queue.empty():
                frame_queue.put(frame.copy())

            if not result_queue.empty():
                last_results = result_queue.get()

            # Process detection results (headless - no visual display)
            for box, name, confidence in last_results:
                if name != "Unknown" and name not in detected_names:
                    detected_names.add(name)
                    print(f"Person detected: {name}")
                    known_face_detected = True

            # Clean up memory periodically
            if frame_count % 200 == 0:
                gc.collect()

            # Exit when face detected
            if known_face_detected:
                stop_event.set()
                break

            # Small delay to prevent excessive CPU usage
            time.sleep(0.01)

    except Exception as e:
        print(f"Error during webcam processing: {e}")
    finally:
        # Ensure thread is properly stopped
        stop_event.set()
        if thread.is_alive():
            thread.join(timeout=1.0)

    safe_exit(cap)
    return list(detected_names)


if __name__ == "__main__":
    try:
        detected = main()
        print("Program finished. People seen:", detected)
    except Exception as e:
        print(f"Error in facial recognition: {e}")
