from app.py import app
from app.tasks import celery

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000) 