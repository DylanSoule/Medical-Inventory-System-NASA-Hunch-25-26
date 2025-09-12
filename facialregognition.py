from deepface import DeepFace
import sys

# -----------------------------
# CUSTOM THRESHOLD
# -----------------------------
CUSTOM_THRESHOLD = 0.65  # lower = stricter, higher = more lenient

# -----------------------------
# CHECK ARGUMENTS
# -----------------------------
if len(sys.argv) < 3:
    print("Usage: python face_thinyg.py <image1> <image2>")
    sys.exit(1)

img1 = sys.argv[1]
img2 = sys.argv[2]

# -----------------------------
# COMPARE FACES
# -----------------------------
result = DeepFace.verify(
    img1, img2,
    detector_backend="opencv",  # dlib-free
    enforce_detection=False
)

distance = result['distance']

# -----------------------------
# PRINT FRIENDLY OUTPUT
# -----------------------------
if distance <= CUSTOM_THRESHOLD:
    print(f"SAME PERSON ✅  (distance: {distance:.3f} ≤ threshold: {CUSTOM_THRESHOLD})")
else:
    print(f"DIFFERENT PEOPLE ❌  (distance: {distance:.3f} > threshold: {CUSTOM_THRESHOLD})")

# Optional: print all details
# print(result)
