import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load Image
image = cv2.imread("2.jpg")
original = image.copy()

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Blur to reduce noise
blur = cv2.GaussianBlur(gray, (5, 5), 0)

# Threshold to isolate particles
_, thresh = cv2.threshold(blur, 200, 255, cv2.THRESH_BINARY)

# Edge detection
edges = cv2.Canny(thresh, 50, 150)

# Find contours
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

count = 0

for contour in contours:
    area = cv2.contourArea(contour)
    
    # Ignore very small noise
    if area > 50:
        count += 1
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(original, (x, y), (x+w, y+h), (0,255,0), 2)

print("Detected Microplastic Count:", count)

# Show output
plt.figure(figsize=(10,5))
plt.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
plt.title("Detected Microplastics")
plt.axis("off")
plt.show()
