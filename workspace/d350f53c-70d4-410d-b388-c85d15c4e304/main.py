import os
import sys
sys.path.insert(0, './')
from app import app

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app.run()