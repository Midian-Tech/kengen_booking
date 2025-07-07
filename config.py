import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:bazuu254!0758@localhost/kengen'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
