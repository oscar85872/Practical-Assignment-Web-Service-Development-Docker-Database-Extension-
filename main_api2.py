from flask import Flask, request, jsonify
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from pydantic import BaseModel, ValidationError, validator
from typing import Literal
from decimal import Decimal
from functools import wraps
import time
import sys

# === NUEVA FUNCIÓN PARA ESPERAR Y CREAR LA TABLA ===
def wait_for_db_and_create_table():
    """Wait for database to be ready and create table if needed"""
    max_retries = 20
    retry_delay = 3
    
    print("🚀 Starting database initialization...")
    
    for attempt in range(max_retries):
        connection = None
        try:
            print(f"📡 Attempting database connection ({attempt + 1}/{max_retries})...")
            connection = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'expensesdb'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres')
            )
            cursor = connection.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'expenses'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                print("🔄 Creating 'expenses' table...")
                cursor.execute('''
                    CREATE TABLE expenses (
                        id SERIAL PRIMARY KEY,
                        amount DECIMAL(10,2) NOT NULL,
                        description VARCHAR(255) NOT NULL,
                        category VARCHAR(50) NOT NULL,
                        date DATE NOT NULL,
                        type VARCHAR(10) CHECK (type IN ('expense', 'income')) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('CREATE INDEX idx_expenses_date ON expenses(date)')
                cursor.execute('CREATE INDEX idx_expenses_category ON expenses(category)')
                cursor.execute('CREATE INDEX idx_expenses_type ON expenses(type)')
                
                connection.commit()
                print("✅ 'expenses' table created successfully!")
            else:
                print("✅ 'expenses' table already exists")
            
            # Verify we can actually query the table
            cursor.execute("SELECT 1 FROM expenses LIMIT 1")
            print("✅ Database is ready and table is accessible!")
            return True
            
        except psycopg2.OperationalError as e:
            print(f"⏳ Database not ready yet: {e}")
            if attempt < max_retries - 1:
                print(f"🕒 Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
        except Exception as e:
            print(f"⚠️ Database error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        finally:
            if connection:
                cursor.close()
                connection.close()
    
    print("❌ FATAL: Failed to initialize database after multiple attempts")
    return False

# === INICIALIZAR BASE DE DATOS ANTES DE CREAR LA APP FLASK ===
if not wait_for_db_and_create_table():
    print("❌ Exiting: Database initialization failed")
    sys.exit(1)

# === AHORA CREAMOS LA APP FLASK ===
app = Flask(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'expensesdb'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

VALID_API_KEYS = ["OMHT2409"]
CATEGORIES = ['food', 'transport', 'entertainment', 'bills', 'shopping', 'health', 'education', 'income', 'other']

# === ELIMINA la función create_table_if_not_exists original ===
# Ya no la necesitamos porque usamos wait_for_db_and_create_table

# ... EL RESTO DE TU CÓDIGO PERMANECE EXACTAMENTE IGUAL ...
# [todo el resto de tu código sin cambios]


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API Key required'}), 401
        
        if api_key not in VALID_API_KEYS:
            return jsonify({'error': 'Invalid API Key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

class ExpenseBase(BaseModel):
    amount: Decimal
    description: str
    category: str
    date: str
    type: Literal['expense', 'income']

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

    @validator('category')
    def category_must_be_valid(cls, v):
        if v not in CATEGORIES:
            raise ValueError(f'Invalid category. Options: {", ".join(CATEGORIES)}')
        return v

    @validator('date')
    def date_must_be_valid(cls, v):
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError('Date must be in ISO format (YYYY-MM-DD)')
        return v

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    id: int

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

def get_db_connection():
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        return connection
    except Exception as ex:
        print(f'Database connection error: {ex}')
        return None

def save_expense(data: ExpenseCreate):
    connection = get_db_connection()
    if connection is None:
        raise Exception("No database connection")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('''
                INSERT INTO expenses (amount, description, category, date, type)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, amount, description, category, date, type
            ''', (
                float(data.amount),
                data.description,
                data.category,
                data.date,
                data.type
            ))
            expense = cursor.fetchone()
            connection.commit()
            
            return ExpenseResponse(
                id=expense[0],
                amount=Decimal(str(expense[1])),
                description=expense[2],
                category=expense[3],
                date=expense[4].isoformat(),
                type=expense[5]
            )
    except Exception as e:
        connection.rollback()
        raise Exception(f"Error saving record: {str(e)}")
    finally:
        connection.close()

def get_expenses_from_db(filters=None):
    connection = get_db_connection()
    if connection is None:
        raise Exception("No database connection")
    
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = 'SELECT * FROM expenses WHERE 1=1'
            params = []
            
            if filters:
                if filters.get('start_date'):
                    query += ' AND date >= %s'
                    params.append(filters['start_date'])
                if filters.get('end_date'):
                    query += ' AND date <= %s'
                    params.append(filters['end_date'])
                if filters.get('category'):
                    query += ' AND category = %s'
                    params.append(filters['category'])
                if filters.get('type'):
                    query += ' AND type = %s'
                    params.append(filters['type'])
            
            query += ' ORDER BY date DESC, id DESC'
            cursor.execute(query, params)
            expenses = cursor.fetchall()
            
            for expense in expenses:
                expense['amount'] = Decimal(str(expense['amount']))
                expense['date'] = expense['date'].isoformat()
                expense['id'] = int(expense['id'])
                
            return expenses
    except Exception as e:
        raise Exception(f"Error getting records: {str(e)}")
    finally:
        connection.close()

def get_monthly_summaries_from_db(year):
    connection = get_db_connection()
    if connection is None:
        raise Exception("No database connection")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT 
                    EXTRACT(MONTH FROM date) as month,
                    category,
                    SUM(amount) as total
                FROM expenses 
                WHERE type = 'income' AND EXTRACT(YEAR FROM date) = %s
                GROUP BY EXTRACT(MONTH FROM date), category
                ORDER BY month
            ''', (year,))
            income_results = cursor.fetchall()
            
            cursor.execute('''
                SELECT 
                    EXTRACT(MONTH FROM date) as month,
                    category,
                    SUM(amount) as total
                FROM expenses 
                WHERE type = 'expense' AND EXTRACT(YEAR FROM date) = %s
                GROUP BY EXTRACT(MONTH FROM date), category
                ORDER BY month
            ''', (year,))
            expense_results = cursor.fetchall()
            
            return income_results, expense_results
    except Exception as e:
        raise Exception(f"Error getting summaries: {str(e)}")
    finally:
        connection.close()

def delete_expense_from_db(expense_id):
    connection = get_db_connection()
    if connection is None:
        raise Exception("No database connection")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM expenses WHERE id = %s', (expense_id,))
            connection.commit()
            return cursor.rowcount > 0
    except Exception as e:
        connection.rollback()
        raise Exception(f"Error deleting record: {str(e)}")
    finally:
        connection.close()

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

app.json_encoder = DecimalEncoder

@app.route('/')
def home():
    return jsonify({
        'message': 'Personal Expense Tracker API'   
    })

@app.route('/api/status', methods=['GET'])
def status_check():
    connection = get_db_connection()
    db_connected = connection is not None
    
    if connection:
        connection.close()
    
    return jsonify({
        'status': 'working',
        'message': 'Personal Expense Tracker API is running',
        'database_connected': db_connected,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/expenses', methods=['POST'])
@require_api_key
def add_expense():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        if 'amount' in data:
            data['amount'] = Decimal(str(data['amount']))
        
        expense_data = ExpenseCreate(**data)
        
        expense = save_expense(expense_data)
        
        return jsonify({
            'message': 'Expense/Income added successfully',
            'expense': expense.dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except Exception as e:
        return jsonify({'error': f'Error saving expense: {str(e)}'}), 500

@app.route('/api/expenses/list', methods=['GET'])
@require_api_key
def get_expenses():
    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({'error': 'No database connection'}), 500
        
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = 'SELECT * FROM expenses WHERE 1=1'
            params = []
            
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            category = request.args.get('category')
            expense_type = request.args.get('type')
            
            if start_date:
                query += ' AND date >= %s'
                params.append(start_date)
            if end_date:
                query += ' AND date <= %s'
                params.append(end_date)
            if category:
                query += ' AND category = %s'
                params.append(category)
            if expense_type:
                query += ' AND type = %s'
                params.append(expense_type)
            
            query += ' ORDER BY id ASC'
            
            cursor.execute(query, params)
            expenses = cursor.fetchall()
            
            for expense in expenses:
                expense['amount'] = Decimal(str(expense['amount']))
                expense['date'] = expense['date'].isoformat()
                expense['id'] = int(expense['id'])
        
        connection.close()
        
        return jsonify({
            'count': len(expenses),
            'expenses': expenses
        }), 200
        
    except Exception as e:
        if 'connection' in locals():
            connection.close()
        return jsonify({'error': f'Error reading expenses: {str(e)}'}), 500

@app.route('/api/summary/months', methods=['GET'])
@require_api_key
def get_monthly_summaries():
    try:
        year = request.args.get('year', str(datetime.now().year))
        
        try:
            year = int(year)
        except ValueError:
            return jsonify({'error': 'Year must be a valid number'}), 400
        
        income_results, expense_results = get_monthly_summaries_from_db(year)
        
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        
        monthly_data = {}
        
        for month_num, category, total in income_results:
            month_name = month_names[int(month_num)]
            if month_name not in monthly_data:
                monthly_data[month_name] = {
                    'income': {},
                    'expenses_by_category': {},
                    'total_expenses': Decimal('0.0'),
                    'total_income': Decimal('0.0'),
                    'balance': Decimal('0.0')
                }
            amount = Decimal(str(total))
            monthly_data[month_name]['income'][category] = amount
            monthly_data[month_name]['total_income'] += amount
        
        for month_num, category, total in expense_results:
            month_name = month_names[int(month_num)]
            if month_name not in monthly_data:
                monthly_data[month_name] = {
                    'income': {},
                    'expenses_by_category': {},
                    'total_expenses': Decimal('0.0'),
                    'total_income': Decimal('0.0'),
                    'balance': Decimal('0.0')
                }
            amount = Decimal(str(total))
            monthly_data[month_name]['expenses_by_category'][category] = amount
            monthly_data[month_name]['total_expenses'] += amount
        
        for month_name, data in monthly_data.items():
            data['income'] = {k: round(v, 2) for k, v in data['income'].items()}
            data['expenses_by_category'] = {k: round(v, 2) for k, v in data['expenses_by_category'].items()}
            data['total_expenses'] = round(data['total_expenses'], 2)
            data['total_income'] = round(data['total_income'], 2)
            data['balance'] = round(data['total_income'] - data['total_expenses'], 2)
        
        sorted_summaries = dict(sorted(
            monthly_data.items(),
            key=lambda x: list(month_names.keys())[list(month_names.values()).index(x[0])]
        ))
        
        return jsonify({
            'monthly_summaries': sorted_summaries
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error generating monthly summaries: {str(e)}'}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@require_api_key
def delete_expense(expense_id):
    try:
        success = delete_expense_from_db(expense_id)
        if not success:
            return jsonify({'error': 'Expense not found'}), 404
        
        return jsonify({'message': 'Expense deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Error deleting expense: {str(e)}'}), 500

if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)