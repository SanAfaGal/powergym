# Face Recognition System for Customer Authentication

## Quick Start

This FastAPI backend now includes a complete face recognition system for customer authentication using the `face_recognition` library (dlib-based).

### Features

✅ **Register Customer Face** - Store facial biometric data
✅ **Authenticate Customer** - Verify identity by face
✅ **Compare Faces** - Direct comparison of two face images
✅ **Update Face** - Replace existing biometric data
✅ **Delete Face** - Deactivate biometric data

## File Structure

```
project/
├── app/
│   ├── api/v1/endpoints/
│   │   └── face_recognition.py        # API endpoints
│   ├── models/
│   │   └── face_recognition.py        # Request/response models
│   └── services/
│       └── face_recognition_service.py # Core logic
├── pyproject.toml                      # Dependencies (updated)
├── .env.example                        # Configuration template
└── Documentation:
    ├── FACE_RECOGNITION_API.md         # Complete API documentation
    ├── API_QUICK_REFERENCE.md          # Quick reference card
    ├── USAGE_EXAMPLE.md                # Code examples (Python/JS)
    ├── IMPLEMENTATION_SUMMARY.md       # Technical details
    └── SECURITY_CONSIDERATIONS.md      # Security guide
```

## Installation

Dependencies are already added to `pyproject.toml`. The system will install:

- `face-recognition>=1.3.0` - Face detection and recognition
- `opencv-python-headless>=4.10.0` - Image processing
- `pillow>=11.0.0` - Image manipulation
- `numpy>=2.0.0` - Numerical operations

## Configuration

Add to your `.env` file:

```env
# Face Recognition Settings
FACE_RECOGNITION_MODEL="hog"            # or "cnn" for better accuracy
FACE_RECOGNITION_TOLERANCE=0.6          # 0.4-0.7 (lower = stricter)
MAX_IMAGE_SIZE_MB=5                     # Maximum upload size
ALLOWED_IMAGE_FORMATS=["jpg","jpeg","png"]
```

## API Endpoints

Base URL: `/api/v1/face`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/register` | POST | Register new face |
| `/authenticate` | POST | Authenticate by face |
| `/compare` | POST | Compare two faces |
| `/update` | PUT | Update existing face |
| `/{customer_id}` | DELETE | Delete face biometric |

All endpoints require JWT authentication.

## Quick Example

### 1. Login to get JWT token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=changeme123"
```

### 2. Register a customer's face

```bash
curl -X POST "http://localhost:8000/api/v1/face/register" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUSTOMER_UUID",
    "image_base64": "BASE64_ENCODED_IMAGE"
  }'
```

### 3. Authenticate with face

```bash
curl -X POST "http://localhost:8000/api/v1/face/authenticate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "BASE64_ENCODED_IMAGE"
  }'
```

## Image Requirements

- **Format**: JPG, JPEG, or PNG
- **Size**: Maximum 5MB
- **Content**: Single face, front-facing, well-lit
- **Resolution**: Minimum 640x480 recommended
- **Encoding**: Base64 string (with or without data URI prefix)

## Security Features

✅ JWT authentication on all endpoints
✅ File size and format validation
✅ Single face detection (rejects multiple/no faces)
✅ Secure embedding storage (one-way transformation)
✅ Image compression and thumbnails
✅ Row-level security (RLS) on database
✅ Soft deletes (audit trail preserved)

## Database

Face biometrics are stored in the existing `client_biometrics` table:

- Uses PostgreSQL vector extension (pgvector)
- 512-dimensional embeddings for similarity search
- HNSW index for fast vector queries
- One active biometric per customer
- Automatic CASCADE delete with customer

## Performance

- **HOG Model** (default): ~200ms per face detection, CPU-friendly
- **CNN Model**: ~2s per detection, more accurate, GPU recommended
- **Storage**: ~2KB embedding + ~5-10KB thumbnail per face
- **Accuracy**: 99.38% on LFW benchmark

## How It Works

1. **Image Submission**: Frontend sends base64-encoded face image
2. **Validation**: Server validates size, format, and face presence
3. **Encoding**: Extracts 128-dimensional face encoding using dlib
4. **Storage**: Expands to 512 dimensions and stores in vector database
5. **Authentication**: Compares new face against all stored embeddings
6. **Matching**: Returns best match if distance below tolerance threshold

## Documentation

- **[FACE_RECOGNITION_API.md](./FACE_RECOGNITION_API.md)** - Complete API reference with all endpoints, parameters, responses
- **[API_QUICK_REFERENCE.md](./API_QUICK_REFERENCE.md)** - Quick reference card for developers
- **[USAGE_EXAMPLE.md](./USAGE_EXAMPLE.md)** - Code examples in Python and JavaScript
- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - Technical implementation details
- **[SECURITY_CONSIDERATIONS.md](./SECURITY_CONSIDERATIONS.md)** - Security measures and best practices

## Interactive Documentation

When the server is running:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

## Workflow Example

```
1. Customer Registration
   └─> Create customer record (customers table)

2. Face Enrollment
   └─> POST /face/register
       └─> Extract face encoding
       └─> Store in client_biometrics table

3. Authentication
   └─> POST /face/authenticate
       └─> Extract encoding from new image
       └─> Search all stored encodings
       └─> Return best match + confidence

4. Update (if needed)
   └─> PUT /face/update
       └─> Deactivate old biometric
       └─> Register new biometric
```

## Tolerance Configuration

The `FACE_RECOGNITION_TOLERANCE` setting controls matching strictness:

- **0.4-0.5**: High security, strict matching (fewer false positives)
- **0.6** (default): Balanced security and usability
- **0.7-0.8**: Lenient, handles varied lighting (more false positives)

## Error Handling

Common errors and solutions:

| Error | Solution |
|-------|----------|
| "No face detected" | Use clear, front-facing photo |
| "Multiple faces detected" | Use single-person photo |
| "Invalid image format" | Use JPG, JPEG, or PNG |
| "Image size exceeds maximum" | Reduce image size below 5MB |
| "Customer not found" | Verify customer exists in database |
| "No matching face found" | Face not registered or tolerance too strict |

## Production Recommendations

Before deploying to production:

1. ✅ Enable HTTPS/TLS
2. ✅ Implement rate limiting (10 requests/minute recommended)
3. ✅ Set up audit logging for biometric access
4. ✅ Configure monitoring and alerts
5. ✅ Review privacy compliance (GDPR, CCPA, BIPA)
6. ✅ Consider liveness detection for anti-spoofing
7. ✅ Set up regular backups
8. ✅ Document incident response procedures

See **SECURITY_CONSIDERATIONS.md** for detailed security guidance.

## Support

For technical details:
- Review the implementation files in `app/services/face_recognition_service.py`
- Check API endpoint code in `app/api/v1/endpoints/face_recognition.py`
- Read the comprehensive documentation files

For debugging:
- Check FastAPI logs for detailed error messages
- Verify Supabase connection in `.env`
- Ensure customer exists and is active
- Test with high-quality images
- Adjust tolerance if needed

## Testing

Recommended test coverage:

1. **Unit Tests**:
   - Image validation (size, format, face detection)
   - Embedding extraction and expansion
   - Distance calculation and matching

2. **Integration Tests**:
   - Full registration workflow
   - Authentication with various faces
   - Update and delete operations
   - Error handling

3. **Security Tests**:
   - Token validation
   - Input sanitization
   - SQL injection prevention
   - Rate limiting (if implemented)

## Notes

- This system is for **customer authentication**, not user authentication
- Customers are stored in the `customers` table
- Users (administrators) are stored in the `users` table
- Face biometrics link to customers, not users
- All operations require user JWT authentication to perform

## Technology Stack

- **Face Recognition**: dlib-based face_recognition library
- **Database**: Supabase (PostgreSQL with pgvector)
- **Backend**: FastAPI + Python 3.11+
- **Storage**: Vector embeddings (512-dim) + compressed JPEG
- **Security**: JWT authentication + RLS

## License

This implementation follows the license of the parent project.

## Contributing

When making changes:
1. Update tests to cover new functionality
2. Update relevant documentation files
3. Follow existing code patterns and conventions
4. Ensure backward compatibility
5. Test security implications

## Changelog

### v1.0.0 (2025-10-05)
- Initial implementation
- 5 API endpoints (register, authenticate, compare, update, delete)
- Face recognition using dlib
- Vector storage with pgvector
- Comprehensive documentation
- Security measures implemented
