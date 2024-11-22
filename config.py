import os

SECRET_KEY = os.urandom(24)
MONGO_URI = "mongodb://localhost:27017/cinema"
SESSION_TYPE = 'filesystem'
