from app import create_app, db
from app.models import User  # Import your models here

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ Database initialized!")
