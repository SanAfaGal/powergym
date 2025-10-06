# Face Recognition API - Quick Reference

## Base URL
```
http://localhost:8000/api/v1/face
```

## Authentication
All endpoints require JWT Bearer token:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints Summary

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| POST | `/register` | Register new face | ✅ |
| POST | `/authenticate` | Authenticate by face | ✅ |
| POST | `/compare` | Compare two faces | ✅ |
| PUT | `/update` | Update existing face | ✅ |
| DELETE | `/{customer_id}` | Delete face biometric | ✅ |

## Request/Response Formats

### 1. Register Face
```http
POST /api/v1/face/register
Content-Type: application/json

{
  "customer_id": "uuid",
  "image_base64": "base64_string"
}

→ 201 Created
{
  "success": true,
  "message": "Face registered successfully",
  "biometric_id": "uuid",
  "customer_id": "uuid"
}
```

### 2. Authenticate Face
```http
POST /api/v1/face/authenticate
Content-Type: application/json

{
  "image_base64": "base64_string"
}

→ 200 OK
{
  "success": true,
  "message": "Face authenticated successfully",
  "customer_id": "uuid",
  "customer_info": { ... },
  "confidence": 0.95
}
```

### 3. Compare Faces
```http
POST /api/v1/face/compare
Content-Type: application/json

{
  "image_base64_1": "base64_string",
  "image_base64_2": "base64_string"
}

→ 200 OK
{
  "success": true,
  "message": "Faces compared successfully",
  "match": true,
  "distance": 0.35,
  "confidence": 0.95
}
```

### 4. Update Face
```http
PUT /api/v1/face/update
Content-Type: application/json

{
  "customer_id": "uuid",
  "image_base64": "base64_string"
}

→ 200 OK
{
  "success": true,
  "message": "Face updated successfully",
  "biometric_id": "uuid",
  "customer_id": "uuid"
}
```

### 5. Delete Face
```http
DELETE /api/v1/face/{customer_id}

→ 200 OK
{
  "success": true,
  "message": "Face biometric deleted successfully"
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created (registration) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (no match or invalid token) |
| 404 | Not Found (customer doesn't exist) |
| 500 | Internal Server Error |

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "No face detected" | Image has no visible face | Use clear, front-facing photo |
| "Multiple faces detected" | Image has >1 face | Use single-person photo |
| "Invalid image format" | Wrong file type | Use JPG, JPEG, or PNG |
| "Image size exceeds maximum" | File too large | Reduce to <5MB |
| "Customer not found" | Invalid customer_id | Verify customer exists |
| "No matching face found" | Face not registered | Register face first |
| "Customer is not active" | Customer deactivated | Reactivate customer |

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `FACE_RECOGNITION_MODEL` | `"hog"` | Detection model (hog/cnn) |
| `FACE_RECOGNITION_TOLERANCE` | `0.6` | Matching threshold (0.0-1.0) |
| `MAX_IMAGE_SIZE_MB` | `5` | Max upload size (MB) |
| `ALLOWED_IMAGE_FORMATS` | `["jpg","jpeg","png"]` | Accepted formats |

## Image Requirements

- **Format**: JPG, JPEG, or PNG
- **Size**: Maximum 5MB
- **Content**: Single face, front-facing
- **Quality**: Minimum 640x480 resolution
- **Lighting**: Well-lit, minimal shadows
- **Encoding**: Base64 string (with or without data URI prefix)

## Response Fields

### Registration/Update Response
- `success` (bool): Operation status
- `message` (string): Human-readable message
- `biometric_id` (uuid): ID of stored biometric
- `customer_id` (uuid): Customer identifier

### Authentication Response
- `success` (bool): Authentication status
- `message` (string): Result message
- `customer_id` (uuid): Matched customer
- `customer_info` (object): Full customer details
- `confidence` (float): Match confidence (0.0-1.0)

### Comparison Response
- `success` (bool): Operation status
- `message` (string): Result message
- `match` (bool): Whether faces match
- `distance` (float): Euclidean distance
- `confidence` (float): Match confidence (0.0-1.0)

## Confidence Scores

| Score | Interpretation |
|-------|----------------|
| 0.95-1.0 | Excellent match |
| 0.85-0.94 | Good match |
| 0.70-0.84 | Fair match |
| 0.60-0.69 | Weak match (default threshold) |
| <0.60 | No match |

## Tolerance Settings

| Tolerance | Use Case |
|-----------|----------|
| 0.4-0.5 | High security (strict) |
| 0.6 | Standard (default) |
| 0.7-0.8 | Lenient (varied conditions) |

## Performance Notes

- **HOG Model**: ~200ms per detection, CPU-friendly
- **CNN Model**: ~2s per detection, more accurate, GPU recommended
- **Storage**: ~2KB embedding + ~5-10KB thumbnail per face
- **Concurrent Requests**: Supports multiple simultaneous authentications

## Security Best Practices

1. ✅ Always use HTTPS in production
2. ✅ Implement rate limiting (e.g., 10 requests/minute)
3. ✅ Log all authentication attempts
4. ✅ Monitor for brute-force patterns
5. ✅ Rotate JWT tokens regularly
6. ✅ Validate customer status before operations
7. ✅ Use audit trails for biometric access
8. ✅ Implement timeout for inactive sessions

## Quick Test with cURL

```bash
# 1. Login
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=changeme123" \
  | jq -r '.access_token')

# 2. Register face
curl -X POST "http://localhost:8000/api/v1/face/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_id\": \"YOUR_CUSTOMER_ID\",
    \"image_base64\": \"$(base64 -w 0 face.jpg)\"
  }"

# 3. Authenticate
curl -X POST "http://localhost:8000/api/v1/face/authenticate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"image_base64\": \"$(base64 -w 0 face.jpg)\"
  }"
```

## Interactive API Documentation

- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

## Support & Troubleshooting

1. Check server logs for detailed errors
2. Verify Supabase connection in `.env`
3. Ensure customer exists and is active
4. Test with high-quality face images
5. Adjust tolerance if needed
6. Monitor system resources (CPU/memory)

## Database Tables

Face biometrics stored in `client_biometrics`:
- Uses vector similarity search (pgvector)
- One active biometric per customer
- Automatic CASCADE delete with customer
- Row-level security enabled

## Migration Files

- `20251004175841_create_enums_and_tables.sql` - Initial schema
- `20251005171308_create_client_biometrics_table.sql` - Biometrics table with vector support
