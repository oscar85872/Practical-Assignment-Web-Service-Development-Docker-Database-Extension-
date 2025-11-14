# Personal Expense Tracker API - Complete Documentation

## Project Overview
A Flask-based REST API for personal finance management that tracks expenses and income using PostgreSQL database. This project extends a previous CSV-based implementation to a full database-driven web service with Docker containerization.

## Team Role
- Oscar Manuel Hurtado Talavera - Backend Developer

## Prerequisites & Installation

### System Requirements
- Python 3.9 or higher
- PostgreSQL database
- Docker (for containerized deployment)

### Python Dependencies
pip install Flask psycopg2-binary pydantic

### Environment Configuration
Configure these environment variables or use default values:
- DB_HOST: Database host address (default: 'localhost')
- DB_PORT: Database port (default: '5432')
- DB_NAME: Database name (default: 'expensesdb')
- DB_USER: Database username (default: 'postgres')
- DB_PASSWORD: Database password (default: 'postgres')
- FLASK_DEBUG: Enable debug mode (default: '0')

## Database Schema

### Table: expenses

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-incrementing unique identifier |
| amount | DECIMAL(10,2) | NOT NULL | Monetary amount (max 10 digits, 2 decimal places) |
| description | VARCHAR(255) | NOT NULL | Transaction description (max 255 characters) |
| category | VARCHAR(50) | NOT NULL | Expense/income category |
| date | DATE | NOT NULL | Transaction date |
| type | VARCHAR(10) | CHECK (type IN ('expense', 'income')) NOT NULL | Transaction type |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |

### Database Indexes
- idx_expenses_date: Optimizes date-based queries
- idx_expenses_category: Optimizes category-based filtering
- idx_expenses_type: Optimizes type-based filtering

## API Endpoints

### 1. Health Check & Status
GET / - Returns API welcome message
GET /api/status - Returns detailed API and database connection status

### 2. Expense Management
POST /api/expenses - Add new expense/income record
Headers: 
  X-API-Key: OMHT2409 (required)
  Content-Type: application/json
Request Body:
{
  "amount": 150.50,
  "description": "Groceries",
  "category": "food",
  "date": "2024-01-15",
  "type": "expense"
}

GET /api/expenses/list - Retrieve all expenses with optional filtering
Query Parameters (optional):
  start_date: Filter from date (YYYY-MM-DD)
  end_date: Filter to date (YYYY-MM-DD)
  category: Filter by category
  type: Filter by type (expense/income)
  api_key: API key (alternative to header)

DELETE /api/expenses/<expense_id> - Delete specific expense record

### 3. Financial Reports
GET /api/summary/months - Get monthly income and expense summaries
Query Parameters:
  year: Year to summarize (default: current year)

## Data Validation

### Valid Categories
food, transport, entertainment, bills, shopping, health, education, income, other

### Valid Types
expense, income

### Validation Rules
- Amount must be positive decimal
- Date must be ISO format (YYYY-MM-DD)
- Category must be from predefined list
- Type must be 'expense' or 'income'

## Authentication
All protected endpoints require API key authentication via:
- X-API-Key header, OR
- api_key query parameter

Valid API Key: OMHT2409

## Quick Start Guide

### Method 1: Direct Execution
1. Install dependencies: pip install Flask psycopg2-binary pydantic
2. Set up PostgreSQL database
3. Configure environment variables
4. Run: python main_api2.py
5. Access: http://127.0.0.1:5000

### Method 2: Docker Deployment
1. Build and run: docker-compose up --build
2. Access: http://localhost:5000

## Database Features
- Automatic table creation on startup
- Optimized indexes for performance
- PostgreSQL with psycopg2 adapter
- Data persistence with Docker volumes

## Example Usage

### Add Expense via curl:
curl -X POST http://localhost:5000/api/expenses \
  -H "X-API-Key: OMHT2409" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 75.25,
    "description": "Dinner",
    "category": "food",
    "date": "2024-01-15",
    "type": "expense"
  }'

### List Expenses:
curl "http://localhost:5000/api/expenses/list?api_key=OMHT2409"

### Get Monthly Summary:
curl "http://localhost:5000/api/summary/months?year=2024&api_key=OMHT2409"

## Error Handling
Standard HTTP status codes returned:
- 200: Success
- 400: Bad request (validation errors)
- 401: Unauthorized (invalid/missing API key)
- 404: Not found
- 500: Internal server error

## Project Evolution
This version extends the original CSV-based implementation to include:
- PostgreSQL database integration
- Docker containerization
- Enhanced validation with Pydantic
- RESTful API design
- Automated database initialization
- Comprehensive error handling

##Examples of endpoints

-http://127.0.0.1:5000/
<img width="493" height="136" alt="image" src="https://github.com/user-attachments/assets/16fd9584-8d9d-4859-9c9b-229abca8be03" />

-http://127.0.0.1:5000/api/status
<img width="650" height="207" alt="image" src="https://github.com/user-attachments/assets/9f589acd-9cfa-4d0f-9995-ac0823b0f75c" />

-http://127.0.0.1:5000/api/expenses/list?api_key=OMHT2409
<img width="659" height="1202" alt="image" src="https://github.com/user-attachments/assets/9612dce4-476d-4e0f-b12b-ca00e5182d38" />

-http://localhost:5000/api/summary/months?api_key=OMHT2409
<img width="379" height="1185" alt="image" src="https://github.com/user-attachments/assets/c13ab64f-cf8a-41cf-8edb-ad8c9a0da038" />

-Python programs were used to add and remove expenses (add_expense and delete_expense)

add_expense

<img width="1238" height="668" alt="image" src="https://github.com/user-attachments/assets/f1f1224e-fdd5-45e3-8835-2ff719b8d5c8" />
<img width="596" height="291" alt="image" src="https://github.com/user-attachments/assets/b53da2a0-8092-4eee-956b-cf6de7157033" />

delete_expense (when you delete an expense, its ID is also deleted)

<img width="1125" height="293" alt="image" src="https://github.com/user-attachments/assets/ad376046-7349-442c-977c-f4d4944507bd" />
<img width="689" height="474" alt="image" src="https://github.com/user-attachments/assets/6505686b-c2e2-492b-ae18-14398fa7cce0" />










