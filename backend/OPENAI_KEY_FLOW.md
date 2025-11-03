# OpenAI API Key Management Flow

## Overview

Users can add/update their OpenAI API key through the profile settings endpoint. The key is stored in the database and used for tutorial generation.

## Flow

### 1. Adding/Updating the Key

**Endpoint**: `PUT /api/settings/profile`

**Request Body** (`ProfileSettingsUpdate`):

```json
{
  "openai_api_key": "sk-proj-xxxxxxxxxxxxxxxxxxxxx" // User's OpenAI API key string
}
```

**Processing** (`backend/app/routers/settings.py`, lines 98-112):

- ✅ Accepts `openai_api_key` as a string from the request
- ✅ Validates the key format (must start with "sk-")
- ✅ Stores the key string in `settings.openai_api_key` (database column)
- ✅ Allows empty string `""` to clear/remove the key (sets to `NULL`)

**Database Storage** (`backend/app/models/user_settings.py`, line 55):

```python
openai_api_key = Column(String, nullable=True)  # Stores the actual key string
```

### 2. Response

**Response** (`ProfileSettingsResponse`):

```json
{
  "openai_api_key_configured": true // Boolean indicating if key exists
}
```

**Important**: The actual key is NEVER returned in the response for security reasons. Only a boolean indicating if it's configured.

### 3. Using the Key

**Location**: `backend/app/workers/analysis_worker.py`

**Function**: `generate_tutorial()` (lines 541-551)

- Retrieves user's OpenAI API key from database
- Uses it for all GPT-4 API calls
- Raises error if key is not configured

## Key Points

1. ✅ **Key is stored as STRING** in database (`UserSettings.openai_api_key`)
2. ✅ **Key is accepted as STRING** in update request (`ProfileSettingsUpdate.openai_api_key`)
3. ✅ **Key is validated** (must start with "sk-")
4. ✅ **Key can be removed** (send empty string `""`)
5. ✅ **Key is never returned** in API responses (security)
6. ✅ **Key is used from database** during tutorial generation

## Example Usage

### Add/Update Key:

```bash
curl -X PUT /api/settings/profile \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "openai_api_key": "sk-proj-xxxxxxxxxxxxxxxxxxxxx"
  }'
```

### Remove Key:

```bash
curl -X PUT /api/settings/profile \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "openai_api_key": ""
  }'
```

### Check if Key is Configured:

```bash
curl -X GET /api/settings/profile \
  -H "Authorization: Bearer <token>"
```

Response:

```json
{
  "openai_api_key_configured": true
}
```
