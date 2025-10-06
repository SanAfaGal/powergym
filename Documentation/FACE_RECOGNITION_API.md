# Face Recognition API Documentation

## Overview

This API provides secure face recognition capabilities for customer authentication using the `face_recognition` library. All endpoints require JWT authentication.

## Security Features

- **Image validation**: Maximum 5MB size, supports JPG/JPEG/PNG formats
- **Single face detection**: Rejects images with no face or multiple faces
- **Secure storage**: Face embeddings stored as 512-dimensional vectors in Supabase
- **Active biometric management**: Only one active face biometric per customer
- **Compressed storage**: Images are compressed and thumbnails generated for efficiency

## Base URL

```
/api/v1/face
```

## Endpoints

### 1. Register Customer Face

**POST** `/register`

Register a new face biometric for an existing customer.

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "customer_id": "uuid-string",
  "image_base64": "base64-encoded-image-data"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Face registered successfully",
  "biometric_id": "uuid-string",
  "customer_id": "uuid-string"
}
```

**Errors:**
- 404: Customer not found
- 400: Customer not active, no face detected, multiple faces, or invalid image

---

### 2. Authenticate Customer Face

**POST** `/authenticate`

Authenticate a customer by comparing a face image against all registered faces.

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "image_base64": "base64-encoded-image-data"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Face authenticated successfully",
  "customer_id": "uuid-string",
  "customer_info": {
    "id": "uuid",
    "dni_number": "123456789",
    "first_name": "John",
    "last_name": "Doe",
    ...
  },
  "confidence": 0.95
}
```

**Errors:**
- 401: No matching face found
- 400: No face detected, multiple faces, or invalid image

---

### 3. Compare Two Faces

**POST** `/compare`

Compare two face images to determine if they match.

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "image_base64_1": "base64-encoded-image-data",
  "image_base64_2": "base64-encoded-image-data"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Faces compared successfully",
  "match": true,
  "distance": 0.35,
  "confidence": 0.95
}
```

**Errors:**
- 400: No face detected, multiple faces, or invalid image

---

### 4. Update Customer Face

**PUT** `/update`

Update an existing customer's face biometric (replaces the old one).

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "customer_id": "uuid-string",
  "image_base64": "base64-encoded-image-data"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Face updated successfully",
  "biometric_id": "uuid-string",
  "customer_id": "uuid-string"
}
```

**Errors:**
- 404: Customer not found
- 400: Customer not active, no face detected, multiple faces, or invalid image

---

### 5. Delete Customer Face

**DELETE** `/{customer_id}`

Deactivate a customer's face biometric.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Face biometric deleted successfully"
}
```

**Errors:**
- 404: Customer not found
- 400: Failed to deactivate face biometric

---

## Configuration

Environment variables (`.env` file):

```env
FACE_RECOGNITION_MODEL="hog"          # or "cnn" for better accuracy (slower)
FACE_RECOGNITION_TOLERANCE=0.6        # Lower = stricter matching (0.0-1.0)
MAX_IMAGE_SIZE_MB=5                   # Maximum image size in megabytes
ALLOWED_IMAGE_FORMATS=["jpg","jpeg","png"]
```

## Image Format

Images should be sent as Base64-encoded strings. The API accepts:

1. Raw base64: `"iVBORw0KGgoAAAANSUhEUg..."`
2. Data URI: `"data:image/jpeg;base64,/9j/4AAQSkZJRg..."`

## Performance Notes

- **Model Selection**:
  - `hog` (default): Fast, suitable for most use cases
  - `cnn`: More accurate but requires GPU for optimal performance

- **Tolerance**:
  - Default: 0.6
  - Lower values (0.4-0.5): Stricter matching, fewer false positives
  - Higher values (0.6-0.7): More lenient, better for varied lighting

## Security Best Practices

1. Always validate customer existence and active status before registration
2. Use HTTPS in production to protect image data in transit
3. Implement rate limiting to prevent brute-force attacks
4. Store original images compressed to minimize storage
5. Embeddings are irreversible - face cannot be reconstructed from embedding

## Database Schema

Face biometrics are stored in the `client_biometrics` table:

- `id`: UUID primary key
- `client_id`: Reference to customer
- `type`: 'face' (enum)
- `compressed_data`: Compressed JPEG image
- `thumbnail`: 150x150 thumbnail
- `embedding`: 512-dimensional vector for similarity search
- `is_active`: Only one active biometric per customer
- `meta_info`: Metadata (model version, encoding info)

## Example Usage (Python)

```python
import requests
import base64

# Read and encode image
with open("face.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

# Register face
response = requests.post(
    "http://localhost:8000/api/v1/face/register",
    headers={"Authorization": f"Bearer {jwt_token}"},
    json={
        "customer_id": "123e4567-e89b-12d3-a456-426614174000",
        "image_base64": image_base64
    }
)

print(response.json())

# Authenticate face
response = requests.post(
    "http://localhost:8000/api/v1/face/authenticate",
    headers={"Authorization": f"Bearer {jwt_token}"},
    json={"image_base64": image_base64}
)

print(response.json())
```

## Technical Details

- **Encoding Algorithm**: dlib's face recognition model (128-dimensional)
- **Storage Format**: Expanded to 512 dimensions for PostgreSQL vector compatibility
- **Similarity Metric**: Euclidean distance
- **Face Detection**: HOG (Histogram of Oriented Gradients) or CNN
- **Jitters**: 2 (improves encoding accuracy)
