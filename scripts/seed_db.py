"""Initialize database with seed data."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.database import init_db
from backend.models import Base

def main():
    """Initialize database tables."""
    print("Initializing database...")
    try:
        init_db()
        print("Database tables created successfully.")
        
        # Optional: Create admin user
        # from backend.services.database import get_db_context
        # from backend.models.user import User
        # 
        # with get_db_context() as db:
        #     admin = User(
        #         email="admin@resumeai.com",
        #         username="admin",
        #         hashed_password="hashed_password_here",
        #         is_active=True,
        #         is_verified=True
        #     )
        #     db.add(admin)
        #     print("Admin user created.")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()