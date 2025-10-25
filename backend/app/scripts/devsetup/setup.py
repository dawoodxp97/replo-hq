import sys
import os

# Ensure 'backend' is on sys.path so 'app' package is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from app.db.session import engine, Base
from app.models import user, tutorials # 1. IMPORTANT: Import ALL your model files here

def reset_database():
    """
    Drops all tables and recreates them.
    A destructive operation for development only.
    """
    print("--- WARNING: ABOUT TO DROP ALL DATABASE TABLES ---")
    user_input = input("Are you sure you want to continue? (yes/no): ")
    
    if user_input.lower() != 'yes':
        print("Operation cancelled.")
        return

    print("Dropping all database tables...")
    try:
        # Drops all tables associated with Base.metadata
        Base.metadata.drop_all(bind=engine)
        print("Tables dropped successfully.")
        
        print("Creating all database tables...")
        # Creates all tables associated with Base.metadata
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")
        
        print("--- Database has been reset! Dev Setup Complete ---")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    reset_database()
