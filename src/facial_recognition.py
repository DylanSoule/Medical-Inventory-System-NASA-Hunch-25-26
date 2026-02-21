import logging
import os
from contextlib import contextmanager
from enum import Enum

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
import sys

model_pack_name = 'buffalo_sc'
insightface.app.FaceAnalysis(name=model_pack_name)

logging.getLogger("insightface").setLevel(logging.ERROR)
logging.getLogger("onnxruntime").setLevel(logging.ERROR)


# Error codes as Enum for better error handling
class FaceRecognitionError(Enum):
    """Error codes for face recognition operations"""
    SUCCESS = (0, "Success")
    MODEL_LOAD_FAILED = (1, "Failed to load face recognition model")
    REFERENCE_FOLDER_ERROR = (2, "Reference folder not found or cannot be accessed")
    PRELOAD_FAILED = (3, "Preloading initialization failed")
    CAMERA_ERROR = (4, "Camera initialization or connection error")
    CAMERA_DISCONNECTED = (5, "Camera disconnected during operation")
    FRAME_CAPTURE_FAILED = (6, "Failed to capture frame from camera")
    UNKNOWN_ERROR = (99, "Unknown error occurred")
    
    def __init__(self, code, message):
        self.code = code
        self.message = message
    
    def __str__(self):
        return f"[ERROR {self.code}] {self.message}"
    
    def __repr__(self):
        return f"FaceRecognitionError.{self.name}"

def _initialize_camera_robust():
    """Try multiple methods to initialize camera (Windows & Linux compatible)
    Optimized for USB webcams on Windows"""
    import time
    
    # Platform-specific backends
    if sys.platform.startswith('win'):
        # Windows: DSHOW is best for USB webcams
        backends = [
            (cv2.CAP_DSHOW, "DSHOW"),
            (cv2.CAP_ANY, "ANY"),
        ]
    else:
        # Linux: V4L2, GStreamer, then ANY
        backends = [
            (cv2.CAP_V4L2, "V4L2"),
            (cv2.CAP_GSTREAMER, "GStreamer"),
            (cv2.CAP_ANY, "ANY")
        ]
    
    for backend, name in backends:
        try:
            print(f"[DEBUG] Trying {name} backend for USB webcam...")
            cap = cv2.VideoCapture(0, backend)
            
            # Critical: Give USB webcam time to initialize and warm up
            time.sleep(1.0)
            
            if cap.isOpened():
                # Flush the buffer - USB webcams buffer old frames
                for _ in range(5):
                    cap.read()
                    time.sleep(0.1)
                
                # Now try to capture a fresh frame
                ret, frame = cap.read()
                
                if ret and frame is not None and frame.size > 0:
                    # Optimize USB webcam settings for Windows
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Single frame buffer
                    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)   # Enable autofocus
                    
                    # Small delay to apply settings
                    time.sleep(0.2)
                    
                    print(f"[SUCCESS] USB Webcam initialized with {name} backend")
                    return cap
                else:
                    print(f"[DEBUG] {name}: Failed to capture frame")
                    cap.release()
        except Exception as e:
            print(f"[DEBUG] {name} backend error: {str(e)}")
            pass
    
    # Fallback: Try different camera indices without backend specification
    print("[DEBUG] Trying fallback camera indices (0, 1, 2)...")
    for camera_index in [0, 1, 2]:
        try:
            cap = cv2.VideoCapture(camera_index)
            time.sleep(1.0)
            
            if cap.isOpened():
                # Flush buffer
                for _ in range(5):
                    cap.read()
                    time.sleep(0.1)
                
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                    time.sleep(0.2)
                    
                    print(f"[SUCCESS] USB Webcam initialized at index {camera_index}")
                    return cap
                else:
                    cap.release()
        except Exception as e:
            print(f"[DEBUG] Camera index {camera_index} error: {str(e)}")
            pass
    
    print("[ERROR] Failed to initialize USB webcam on Windows")
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
        print("[INFO] Starting preload...")
        
        # Step 1: Load InsightFace model
        print("[INFO] Loading InsightFace model...")
        try:
            with suppress_native_output():
                app = insightface.app.FaceAnalysis(name=model_pack_name)
                app.prepare(ctx_id=0)
        except OSError as e:
            if "WinError 1" in str(e) or "Incorrect function" in str(e):
                print("[WARN] Windows ONNX Runtime provider error (harmless), retrying...")
                app = insightface.app.FaceAnalysis(name=model_pack_name)
                app.prepare(ctx_id=0)
            else:
                raise
        
        print("[INFO] InsightFace model loaded successfully")
        
        # Step 2: Load reference embeddings
        print("[INFO] Loading reference embeddings...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        ref_dir = os.path.join(project_root, "assets", "references")
        
        if not os.path.exists(ref_dir):
            print(f"[ERROR] Reference folder not found: {ref_dir}")
            return FaceRecognitionError.REFERENCE_FOLDER_ERROR
        
        reference_embeddings = {}
        for ref_file in os.listdir(ref_dir):
            if ref_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                try:
                    ref_path = os.path.join(ref_dir, ref_file)
                    ref_img = cv2.imread(ref_path)
                    if ref_img is None:
                        print(f"[WARN] Could not read reference image: {ref_file}")
                        continue
                    
                    faces = app.get(ref_img)
                    if len(faces) > 0:
                        embedding = faces[0].embedding
                        # NORMALIZE the reference embedding
                        embedding = embedding / np.linalg.norm(embedding)
                        name = os.path.splitext(ref_file)[0]
                        reference_embeddings[name] = embedding
                        print(f"[INFO] Loaded reference: {name}")
                    else:
                        print(f"[WARN] No face detected in reference image: {ref_file}")
                except Exception as e:
                    print(f"[ERROR] Failed to load reference {ref_file}: {str(e)}")
        
        if not reference_embeddings:
            print("[ERROR] No reference embeddings loaded")
            return FaceRecognitionError.REFERENCE_FOLDER_ERROR
        
        print(f"[INFO] Loaded {len(reference_embeddings)} reference embeddings")
        
        # Step 3: Initialize camera
        print("[INFO] Initializing camera...")
        import time
        camera_start = time.time()
        
        global_camera = _initialize_camera_robust()
        
        if global_camera is None:
            print("[ERROR] Camera initialization failed")
            return FaceRecognitionError.CAMERA_ERROR
        
        camera_ready = True
        print(f"[INFO] Camera ready in {time.time() - camera_start:.2f}s")
        
        preloading_complete = True
        print("[SUCCESS] Preloading complete!")
        return FaceRecognitionError.SUCCESS
        
    except FileNotFoundError as e:
        print(f"[ERROR] File not found during preload: {str(e)}")
        return FaceRecognitionError.REFERENCE_FOLDER_ERROR
    except Exception as e:
        print(f"[ERROR] Unexpected error during preload: {str(e)}")
        import traceback
        traceback.print_exc()
        return FaceRecognitionError.UNKNOWN_ERROR


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
            print(f"Camera reinitialization failed: {FaceRecognitionError.CAMERA_ERROR}")
            return FaceRecognitionError.CAMERA_ERROR

    result = _run_detection_with_preloaded_camera()
    
    # If camera error occurred, try to reinitialize for next time
    if isinstance(result, FaceRecognitionError) and result == FaceRecognitionError.CAMERA_ERROR:
        reinitialize_camera()
    
    return result


def main():
    global app, reference_embeddings, preloading_complete  # pylint: disable=global-variable-not-assigned

    # If not preloaded, do it now (slower)
    if not preloading_complete:
        print("Preloading not complete, initializing now...")
        result = preload_everything()
        if result != FaceRecognitionError.SUCCESS:
            print(result)
            return result
    
    return _run_detection()


def _run_detection_with_preloaded_camera():
    """Ultra-fast detection using preloaded camera"""
    global app, reference_embeddings, global_camera  # pylint: disable=global-variable-not-assigned
    
    def normalize(emb):
        return emb / np.linalg.norm(emb)

    def distance_to_confidence(dist, max_dist=2.0):
        return max(0.0, min(1.0, 1.0 - dist / max_dist))
    
    THRESHOLD = 1

    def recognize_face(face_embedding, threshold=1.0):
        """Recognize a face by comparing embedding to references
        
        Args:
            face_embedding: numpy array of face embedding (normalized 1D)
            threshold: distance threshold for recognition (lower = stricter)
                   For normalized embeddings, typically 0.5-1.5
        
        Returns:
            tuple: (name, distance) or (None, None) if no match
        """
        global reference_embeddings
    
        if reference_embeddings is None or len(reference_embeddings) == 0:
            print("[WARN] No reference embeddings loaded")
            return None, None
    
        if face_embedding is None:
            print("[WARN] Invalid face embedding")
            return None, None
    
        try:
            # Ensure face_embedding is 1D array (should already be normalized by caller)
            face_embedding = np.asarray(face_embedding).flatten()
            
            # Convert reference embeddings dictionary to list of arrays
            names = list(reference_embeddings.keys())
            
            # Calculate distance to each reference
            distances = []
            for name in names:
                ref_emb = np.asarray(reference_embeddings[name]).flatten()
                dist = np.linalg.norm(face_embedding - ref_emb)
                distances.append(dist)
            
            distances = np.array(distances)
            
            # Find closest match
            min_distance_idx = np.argmin(distances)
            min_distance = distances[min_distance_idx]
            
            # Check if match is within threshold
            if min_distance < threshold:
                matched_name = names[min_distance_idx]
                print(f"[INFO] Face recognized: {matched_name} (distance: {min_distance:.4f})")
                return matched_name, min_distance
            else:
                print(f"[INFO] Face not recognized (closest distance: {min_distance:.4f}, threshold: {threshold})")
                return None, min_distance
                
        except Exception as e:
            print(f"[ERROR] Error in recognize_face: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None

    # Use pre-initialized camera - but check if it's still connected
    cap = global_camera
    if not cap.isOpened():
        print(f"Pre-initialized camera not available: {FaceRecognitionError.CAMERA_ERROR}")
        return FaceRecognitionError.CAMERA_ERROR
    
    # Test if camera is actually working by trying to read a frame
    test_ret, test_frame = cap.read()
    if not test_ret:
        print(f"Camera disconnected or not working: {FaceRecognitionError.CAMERA_DISCONNECTED}")
        return FaceRecognitionError.CAMERA_DISCONNECTED

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
                print(f"Failed to grab frame from webcam: {FaceRecognitionError.FRAME_CAPTURE_FAILED}")
                return FaceRecognitionError.CAMERA_DISCONNECTED

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
        print(f"Webcam could not be opened: {FaceRecognitionError.CAMERA_ERROR}")
        return FaceRecognitionError.CAMERA_ERROR

    thread = threading.Thread(target=recognition_worker, daemon=True)
    thread.start()
    

    frame_count = 0
    last_results = []

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"Failed to grab frame from webcam: {FaceRecognitionError.FRAME_CAPTURE_FAILED}")
                safe_exit(cap)
                return FaceRecognitionError.CAMERA_DISCONNECTED

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
