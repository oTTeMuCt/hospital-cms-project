import sys
print(f"Python: {sys.executable}")
print(f"Path: {sys.path}")
try:
    import dotenv
    print(f"dotenv: {dotenv.__file__}")
except ImportError:
    print("dotenv: NOT FOUND")