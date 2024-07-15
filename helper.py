from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask
from app import login  # Import the login function from app.py

# Initialize Flask app and set up app context
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

def debug_login():
    test_password = "abhi"
    hashed_test_password = generate_password_hash(test_password)
    print(f"Test password: {test_password}")
    print(f"Hashed test password: {hashed_test_password}")

    # Manually push an application context for testing purposes
    with app.app_context():
        # Call the login function from app.py
        result = login("muski@example.com", test_password)

        # Should print True if login successful
        if result:
            print("Login successful")
        else:
            print("Login failed")

if __name__ == "__main__":
    debug_login()
