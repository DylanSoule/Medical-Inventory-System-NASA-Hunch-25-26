import cv2
import os
import sys
import numpy as np
import time
import insightface

# -----------------------------
# LOAD INSIGHTFACE MODEL
# -----------------------------
app = insightface.app.FaceAnalysis(name="buffalo_l", providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))  # bigger size = better accuracy

# -----------------------------
# HELPER: normalize embeddings
# -----------------------------
def normalize(emb):
    return emb / np.linalg.norm(emb)

# -----------------------------
# HELPER: distance -> confidence
# -----------------------------
def distance_to_confidence(dist, max_dist=2.0):
    return max(0.0, min(1.0, 1.0 - dist / max_dist))

# -----------------------------
# LOAD REFERENCE IMAGES
# -----------------------------
ref_dir = "references"
if not os.path.exists(ref_dir):
    print(f"Reference folder '{ref_dir}' not found!")
    sys.exit(1)

known_embeddings = []
known_labels = []

for filename in os.listdir(ref_dir):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        path = os.path.join(ref_dir, filename)
        img = cv2.imread(path)
        if img is None:
            print(f"Warning: Could not read {path}")
            continue
        faces = app.get(img)
        if len(faces) == 0:
            print(f"Warning: No face detected in {filename}")
            continue

        embedding = normalize(faces[0].embedding)
        label = os.path.splitext(filename)[0]
        known_embeddings.append(embedding)
        known_labels.append(label)
        print(f"Loaded reference for: {label}")

if not known_embeddings:
    print("No valid reference faces loaded. Exiting.")
    sys.exit(1)

# -----------------------------
# PARAMETERS
# -----------------------------
THRESHOLD = 0.9

# -----------------------------
# START WEBCAM
# -----------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam")
    sys.exit(1)

print("Press 'q' to quit.")

# FPS counter setup
frame_count = 0
start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    frame_count += 1

    # Run recognition on *every* frame
    faces = app.get(frame)
    for face in faces:
        emb = normalize(face.embedding)
        distances = [np.linalg.norm(emb - ref_emb) for ref_emb in known_embeddings]
        min_dist = min(distances)
        best_match = known_labels[distances.index(min_dist)]
        confidence = distance_to_confidence(min_dist)

        box = face.bbox.astype(int)
        if min_dist <= THRESHOLD:
            color = (0, 255, 0)
            text = f"{best_match} ✅ ({confidence*100:.1f}%)"
        else:
            color = (0, 0, 255)
            text = f"Unknown ❌ ({confidence*100:.1f}%)"

        cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
        cv2.putText(frame, text, (box[0], box[1]-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # FPS calculation
    elapsed_time = time.time() - start_time
    fps = frame_count / elapsed_time
    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    cv2.imshow("Face Recognition", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

# -----------------------------
# CLEANUP
# -----------------------------
cap.release()
cv2.destroyAllWindows()
print("Webcam closed cleanly ✅")
