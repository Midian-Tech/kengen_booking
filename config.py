# config.py

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:bazuu254!0758@localhost/kengen'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email Config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'midiantech59@gmail.com'
    MAIL_PASSWORD = 'wulk nunn kbqe aooq'  # Gmail App Password
    MAIL_DEFAULT_SENDER = 'midiantech59@gmail.com'
    ADMIN_EMAIL = 'nyamburalillian412@gmail.com'

