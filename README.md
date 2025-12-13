# JSI Test - FastAPI Backend

## Overview
This project implements a FastAPI backend solution for the JSI Engineering Applicant Test. Refer to "JSI Engineering Applicant Test-Backend.pdf" for detailed project requirements and specifications.

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd jsi_test
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

## Running the Application

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

Access the interactive Swagger UI documentation at `http://localhost:8000/docs`

## Testing

Run tests with pytest:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=.
```

## Project Structure
```
jsi_test/
├── app/
│   ├── api.py                  # HTTP endpoints
│   ├── main.py                 # App startup + wiring
│   ├── parser.py               # Normalization logic
│   └── repository.py           # In-memory data store
│
├── resources/                  # data files
│   ├── Chats.txt
│   ├── Emails.txt
│   └── Sms.txt
│
├── tests/                      # python tests
│   ├── conftest.py             # pytest configuration
│   ├── tests/test_get_types.py # full test coverage for GetTypes
│   └── test_time_filter.py     # full test coverage for TimeFilter
│
├── requirements.txt # required dependencies
└── README.md   # This file
```

## API Documentation
Interactive Swagger UI documentation is available at `/docs` when the server is running.

## API Endpoints
GET - /GetTypes
POST - /TimeFilter

We do not know what the data might look like other than that there is a 'DateTime' field that represents the time the communication was recorded.
This request format was chosen because we know that those fields are required to make a proper TimeFilter request. If any of those fields are wrong, we get back a 400 HTTP response.

Example Request body with datetimes in ISO format- 
{
  "DataTypes": ["Chats", "Emails"],
  "FromTime": "2021-01-01",
  "ToTime": "2021-01-03"
}

Example Response - 
[
    {
        "Application": "Facebook",
        "From": "john@yahoo.com",
        "To": "Susan Smith",
        "DateTime": "1-1-2021 9:00",
        "Text": "Hi did you call me earlier?",
        "id": 0,
        "communicationType": "Chats",
        "time": "2021-01-01T09:00:00"
    }
]