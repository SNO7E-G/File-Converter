# File Converter API Documentation

This document provides detailed information about the File Converter API endpoints, request/response formats, and authentication requirements.

## Base URL

The base URL for all API endpoints is:

```
http://localhost:8000/api
```

For production environments:

```
https://api.fileconverter-app.com/api
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Most endpoints require authorization.

### Headers

Include the following header in your requests:

```
Authorization: Bearer <your_token>
```

### Getting a Token

To obtain an authentication token:

1. Register a new user account or log in to an existing account.
2. The response will include a `token` and a `refreshToken`.
3. Store these tokens securely.
4. Include the `token` in the Authorization header for subsequent requests.

### Token Expiration and Refresh

Access tokens expire after 1 hour. When an access token expires, use the refresh token to obtain a new one:

```http
POST /api/auth/refresh
Content-Type: application/json
Authorization: Bearer <your_refresh_token>
```

## Error Handling

The API returns appropriate HTTP status codes for different scenarios:

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Server Error` - Internal server error

Error responses follow this format:

```json
{
  "error": "Error message",
  "details": {
    "field": ["Error details"]
  },
  "status": 400
}
```

## Rate Limiting

API endpoints are subject to rate limiting:

- Free tier: 100 requests per hour
- Premium tier: 500 requests per hour
- Enterprise tier: 2000 requests per hour

## API Endpoints

### Authentication

#### Register a new user

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "example_user",
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 123,
    "username": "example_user",
    "email": "user@example.com",
    "tier": "free",
    "created_at": "2023-10-25T12:00:00Z",
    "updated_at": "2023-10-25T12:00:00Z"
  }
}
```

#### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 123,
    "username": "example_user",
    "email": "user@example.com",
    "tier": "free",
    "created_at": "2023-10-25T12:00:00Z",
    "updated_at": "2023-10-25T12:00:00Z"
  }
}
```

### Conversions

#### Create a new conversion

```http
POST /api/conversions
Content-Type: multipart/form-data
Authorization: Bearer <your_token>

file: [file data]
target_format: "pdf"
options: {"quality": "high", "compress": true}
```

**Response:**

```json
{
  "id": 456,
  "user_id": 123,
  "source_format": "docx",
  "target_format": "pdf",
  "source_filename": "document.docx",
  "target_filename": "document.pdf",
  "status": "pending",
  "created_at": "2023-10-25T12:30:00Z",
  "updated_at": "2023-10-25T12:30:00Z"
}
```

#### List user's conversions

```http
GET /api/conversions?page=1&limit=10&status=completed
Authorization: Bearer <your_token>
```

**Response:**

```json
{
  "conversions": [
    {
      "id": 456,
      "user_id": 123,
      "source_format": "docx",
      "target_format": "pdf",
      "source_filename": "document.docx",
      "target_filename": "document.pdf",
      "status": "completed",
      "created_at": "2023-10-25T12:30:00Z",
      "updated_at": "2023-10-25T12:31:00Z",
      "completed_at": "2023-10-25T12:31:00Z",
      "file_size": 245678,
      "result_file_size": 198765,
      "conversion_time": 12
    },
    // Additional conversions...
  ],
  "total": 42,
  "pages": 5,
  "current_page": 1
}
```

#### Get conversion details

```http
GET /api/conversions/456
Authorization: Bearer <your_token>
```

**Response:**

```json
{
  "id": 456,
  "user_id": 123,
  "source_format": "docx",
  "target_format": "pdf",
  "source_filename": "document.docx",
  "target_filename": "document.pdf",
  "status": "completed",
  "created_at": "2023-10-25T12:30:00Z",
  "updated_at": "2023-10-25T12:31:00Z",
  "completed_at": "2023-10-25T12:31:00Z",
  "file_size": 245678,
  "result_file_size": 198765,
  "conversion_time": 12,
  "settings": {
    "quality": "high",
    "compress": true
  },
  "download_url": "https://api.fileconverter-app.com/api/conversions/456/download"
}
```

#### Download a converted file

```http
GET /api/conversions/456/download
Authorization: Bearer <your_token>
```

**Response:**

`File data with appropriate Content-Type and Content-Disposition headers`

#### Delete a conversion

```http
DELETE /api/conversions/456
Authorization: Bearer <your_token>
```

**Response:**

```json
{
  "message": "Conversion deleted successfully"
}
```

### Templates

#### Create a new template

```http
POST /api/templates
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "name": "High Quality PDF",
  "description": "PDF conversion with high quality settings",
  "source_format": "docx",
  "target_format": "pdf",
  "settings": {
    "quality": "high",
    "compress": true,
    "preserve_links": true
  }
}
```

**Response:**

```json
{
  "id": 789,
  "user_id": 123,
  "name": "High Quality PDF",
  "description": "PDF conversion with high quality settings",
  "source_format": "docx",
  "target_format": "pdf",
  "settings": {
    "quality": "high",
    "compress": true,
    "preserve_links": true
  },
  "created_at": "2023-10-25T14:00:00Z",
  "updated_at": "2023-10-25T14:00:00Z",
  "used_count": 0
}
```

#### List user's templates

```http
GET /api/templates
Authorization: Bearer <your_token>
```

**Response:**

```json
{
  "templates": [
    {
      "id": 789,
      "user_id": 123,
      "name": "High Quality PDF",
      "description": "PDF conversion with high quality settings",
      "source_format": "docx",
      "target_format": "pdf",
      "settings": {
        "quality": "high",
        "compress": true,
        "preserve_links": true
      },
      "created_at": "2023-10-25T14:00:00Z",
      "updated_at": "2023-10-25T14:00:00Z",
      "used_count": 5
    },
    // Additional templates...
  ],
  "total": 3
}
```

#### Update a template

```http
PUT /api/templates/789
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "name": "High Quality PDF v2",
  "description": "Updated PDF conversion with enhanced settings",
  "settings": {
    "quality": "ultra",
    "compress": true,
    "preserve_links": true,
    "add_bookmarks": true
  }
}
```

**Response:**

```json
{
  "id": 789,
  "user_id": 123,
  "name": "High Quality PDF v2",
  "description": "Updated PDF conversion with enhanced settings",
  "source_format": "docx",
  "target_format": "pdf",
  "settings": {
    "quality": "ultra",
    "compress": true,
    "preserve_links": true,
    "add_bookmarks": true
  },
  "created_at": "2023-10-25T14:00:00Z",
  "updated_at": "2023-10-25T15:30:00Z",
  "used_count": 5
}
```

#### Delete a template

```http
DELETE /api/templates/789
Authorization: Bearer <your_token>
```

**Response:**

```json
{
  "message": "Template deleted successfully"
}
```

### Statistics

#### Get user's conversion statistics

```http
GET /api/statistics
Authorization: Bearer <your_token>
```

**Response:**

```json
{
  "conversions_today": 12,
  "total_conversions": 156,
  "conversions_by_date": {
    "2023-10-24": 8,
    "2023-10-25": 12
  },
  "conversions_by_format": {
    "pdf": 75,
    "docx": 45,
    "jpg": 36
  },
  "source_formats": {
    "docx": 65,
    "jpg": 50,
    "png": 41
  },
  "target_formats": {
    "pdf": 75,
    "jpg": 36,
    "docx": 45
  },
  "conversions_by_status": {
    "completed": 150,
    "failed": 6
  },
  "peak_usage_hours": {
    "10": 25,
    "14": 32,
    "16": 28
  },
  "most_used_format": "pdf"
}
```

## Supported Formats

The API supports various file formats for conversion. Here's a list of supported source formats and their available target formats:

### Document Formats

- **PDF**: Can be converted to DOCX, JPG, PNG, HTML, TXT
- **DOCX**: Can be converted to PDF, TXT, HTML, EPUB, RTF
- **TXT**: Can be converted to PDF, DOCX, HTML, RTF
- **RTF**: Can be converted to PDF, DOCX, TXT, HTML

### Image Formats

- **JPG/JPEG**: Can be converted to PNG, WEBP, PDF, SVG, GIF
- **PNG**: Can be converted to JPG, WEBP, PDF, SVG, GIF
- **GIF**: Can be converted to JPG, PNG, WEBP, MP4
- **SVG**: Can be converted to PNG, JPG, PDF

### Audio Formats

- **MP3**: Can be converted to WAV, OGG, FLAC, AAC
- **WAV**: Can be converted to MP3, OGG, FLAC, AAC
- **FLAC**: Can be converted to MP3, WAV, OGG, AAC
- **OGG**: Can be converted to MP3, WAV, FLAC, AAC

### Video Formats

- **MP4**: Can be converted to MKV, AVI, WEBM, GIF
- **MKV**: Can be converted to MP4, AVI, WEBM
- **AVI**: Can be converted to MP4, MKV, WEBM
- **WEBM**: Can be converted to MP4, MKV, AVI

## Webhook Notifications

The API supports webhook notifications for conversion status updates:

```http
POST /api/conversions
Content-Type: multipart/form-data
Authorization: Bearer <your_token>

file: [file data]
target_format: "pdf"
webhook_url: "https://example.com/webhook"
```

When the conversion status changes, the API will send a POST request to the specified webhook URL with the following payload:

```json
{
  "conversion_id": 456,
  "status": "completed",
  "source_filename": "document.docx",
  "target_filename": "document.pdf",
  "updated_at": "2023-10-25T12:31:00Z"
}
```

## Scheduled Conversions

To schedule a conversion for later processing:

```http
POST /api/conversions
Content-Type: multipart/form-data
Authorization: Bearer <your_token>

file: [file data]
target_format: "pdf"
scheduled_time: "2023-10-26T08:00:00Z"
```

**Response:**

```json
{
  "id": 457,
  "user_id": 123,
  "source_format": "docx",
  "target_format": "pdf",
  "source_filename": "document.docx",
  "target_filename": "document.pdf",
  "status": "scheduled",
  "scheduled_at": "2023-10-26T08:00:00Z",
  "created_at": "2023-10-25T12:30:00Z",
  "updated_at": "2023-10-25T12:30:00Z"
}
```

## Sharing Conversions

### Share a conversion with another user

```http
POST /api/conversions/456/share
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "shared_with_email": "colleague@example.com",
  "permission": "view"
}
```

**Response:**

```json
{
  "id": 101,
  "conversion_id": 456,
  "shared_by": {
    "id": 123,
    "username": "example_user",
    "email": "user@example.com"
  },
  "shared_with": {
    "id": 124,
    "username": "colleague",
    "email": "colleague@example.com"
  },
  "permission": "view",
  "created_at": "2023-10-25T16:00:00Z",
  "updated_at": "2023-10-25T16:00:00Z"
}
```

### List shared conversions

```http
GET /api/shared
Authorization: Bearer <your_token>
```

**Response:**

```json
{
  "shared_conversions": [
    {
      "id": 101,
      "conversion_id": 456,
      "shared_by": {
        "id": 123,
        "username": "example_user",
        "email": "user@example.com"
      },
      "shared_with": {
        "id": 124,
        "username": "colleague",
        "email": "colleague@example.com"
      },
      "permission": "view",
      "created_at": "2023-10-25T16:00:00Z",
      "updated_at": "2023-10-25T16:00:00Z",
      "conversion": {
        "id": 456,
        "source_filename": "document.docx",
        "target_filename": "document.pdf",
        "status": "completed",
        "created_at": "2023-10-25T12:30:00Z"
      }
    },
    // Additional shared conversions...
  ],
  "total": 5
}
```

## Usage Limits

API usage is limited based on the user's subscription tier:

### Free Tier
- 5 conversions per day
- 100MB maximum file size
- 100 requests per hour
- Basic conversion options only

### Premium Tier
- 100 conversions per day
- 1GB maximum file size
- 500 requests per hour
- Advanced conversion options
- Scheduled conversions
- Batch processing

### Enterprise Tier
- Unlimited conversions
- 5GB maximum file size
- 2000 requests per hour
- All conversion options
- Priority processing
- Webhook integrations
- API key access

## Changelog

### v1.1.0 (2023-11-15)
- Added support for WEBP image format
- Improved PDF to DOCX conversion quality
- Added webhook notifications

### v1.0.0 (2023-10-01)
- Initial API release

---

&copy; 2023-2024 Mahmoud Ashraf (SNO7E). All Rights Reserved. 