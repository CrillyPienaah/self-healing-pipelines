from src.db.database import engine
from src.db.models import Base

print('🗄️  Creating database tables...')
Base.metadata.create_all(bind=engine)
print(' All tables created successfully!')

# Show created tables
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'\n📊 Created {len(tables)} tables:')
for table in tables:
    print(f'  - {table}')
