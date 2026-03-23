import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from src.core.config import settings
from src.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def create_sample_tables():
    logger.info("Initializing database with sample tables")
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                price DECIMAL(10, 2),
                stock_quantity INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER,
                total_amount DECIMAL(10, 2),
                sale_date DATE,
                customer_name VARCHAR(255)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE,
                phone VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.commit()
        logger.info("Sample tables created successfully")
        
        conn.execute(text("""
            INSERT INTO products (name, category, price, stock_quantity)
            VALUES 
                ('Laptop Pro', 'Electronics', 1299.99, 50),
                ('Wireless Mouse', 'Electronics', 29.99, 200),
                ('Office Chair', 'Furniture', 249.99, 30),
                ('Desk Lamp', 'Furniture', 39.99, 100),
                ('USB-C Cable', 'Accessories', 12.99, 500)
            ON CONFLICT DO NOTHING
        """))
        
        conn.execute(text("""
            INSERT INTO customers (name, email, phone)
            VALUES 
                ('John Doe', 'john@example.com', '555-0101'),
                ('Jane Smith', 'jane@example.com', '555-0102'),
                ('Bob Johnson', 'bob@example.com', '555-0103')
            ON CONFLICT DO NOTHING
        """))
        
        conn.commit()
        logger.info("Sample data inserted successfully")
    
    logger.info("Database initialization complete")


if __name__ == "__main__":
    try:
        create_sample_tables()
        print("\n✓ Database initialized successfully!")
        print(f"  Database URL: {settings.DATABASE_URL}")
        print("\nSample tables created:")
        print("  - products")
        print("  - sales")
        print("  - customers")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        print(f"\n✗ Error: {str(e)}")
        print("\nMake sure PostgreSQL is running and the connection details are correct.")
        sys.exit(1)
