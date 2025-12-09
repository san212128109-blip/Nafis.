import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'secret123')
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/mn_daily_items')
    SESSION_TYPE = 'filesystem'
    ADMIN_USER = os.environ.get('ADMIN_USER', 'admin@mnitems.com')
    ADMIN_PASS = os.environ.get('ADMIN_PASS', 'admin123')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.getcwd(),'static','uploads'))
