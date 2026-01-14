# JSI Test - FastAPI Backend

## Overview
FastAPI backend for the JSI Engineering Applicant Test. See `JSI Engineering Applicant Test-Backend.pdf` for requirements.

## Prerequisites
- Python 3.8+
- MongoDB 7+

## Installation
```bash
pip install -r requirements.txt
```

## Configuration
Create a `.env` file using `.env.example`:

```
JWT_SECRET="change-me"
MONGODB_URI="mongodb://localhost:27017"
MONGODB_DB="jsi_test"
RESOURCES_DIR="resources"
```

Notes:
- MongoDB must be running and reachable at `MONGODB_URI`.
- Records are loaded from `RESOURCES_DIR` on startup.

## Running
```bash
uvicorn app.main:app --reload
```

API base: `http://localhost:8000`  
Docs: `http://localhost:8000/docs`

## Testing
```bash
pytest
```

Coverage:
```bash
pytest --cov --cov-report=term-missing
```

Tests use a dedicated database suffix: `<MONGODB_DB>_test`.

## API

### POST `/Login`
Request:
```json
{
  "Username": "admin",
  "Password": "admin-password"
}
```
Response:
```json
{
  "access_token": "jwt-token"
}
```

### GET `/GetTypes`
Response:
```json
["Chats", "Emails", "Sms"]
```

### POST `/TimeFilter`  (login required)
Request:
```json
{
  "DataTypes": ["Chats", "Emails"],
  "FromTime": "2021-01-01T08:00",
  "ToTime": "2021-12-31T10:00"
}
```
Response:
```json
[
  {
    "Application": "Facebook",
    "From": "john@yahoo.com",
    "To": "Susan Smith",
    "Text": "Hi did you call me earlier?",
    "communicationType": "Chats",
    "time": "2021-01-01T09:00:00"
  }
]
```

### POST `/RegisterUser` (admin only)
Request:
```json
{
  "Username": "new-user",
  "Password": "new-password",
  "IsAdmin": false
}
```
Response:
```json
{
  "status": "created"
}
```

### POST `/ReconcileTypes` (admin only)
Response:
```json
[
  {"type": "Chats", "count": 120},
  {"type": "Emails", "count": 45}
]
```

## Auth
JWTs include `sub`, `iat`, and `exp` claims.
Tokens become invalid if `password_changed_at` is later than the token `iat`.

## Project Structure
```
jsi_test/
├── app/
│   ├── __init__.py
│   ├── _auth.py
│   ├── api.py
│   ├── csvparser.py
│   ├── main.py
│   └── repository.py
├── resources/
├── test_resources/
├── tests/
├── requirements.txt
└── README.md
```
