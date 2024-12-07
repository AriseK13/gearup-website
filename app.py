import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'b2e8a1f2b5f33b4811c9aa184b6a28c7'  # Required for session management

# Initialize Firebase Admin SDK
cred = credentials.Certificate("gearup-df833-firebase-adminsdk-htilc-a7a47865bf.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# Temporary hardcoded credentials (admin account)
TEMP_EMAIL = "admin@gmail.com"
TEMP_PASSWORD = "admin123"


@app.route('/')
def index():
    # Redirect to login page if not logged in
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the credentials match the temporary admin account
        if email == TEMP_EMAIL and password == TEMP_PASSWORD:
            # Set session management for admin login
            session['logged_in'] = True
            session['email'] = email
            return redirect(url_for('home'))
        
        try:
            # Simulate Firebase Authentication
            user = auth.get_user_by_email(email)
            # Add session management for authenticated users
            session['logged_in'] = True
            session['email'] = email
            return redirect(url_for('home'))
        except Exception as e:
            return render_template('login.html', error="Invalid credentials. Please try again.")
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('email', None)
    return redirect(url_for('login'))



@app.route('/home')
def home():
    # Check login status before rendering the home page
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    if session.get('email') != TEMP_EMAIL:
        return redirect(url_for('login'))  # or render a 403 page for unauthorized users
    
    return render_template('admin.html')


# Get all users from buyers or sellers collection
@app.route('/users/<collection>', methods=['GET'])
def get_users(collection):
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({"error": "Unauthorized access"}), 401
    try:
        if collection not in ['buyers', 'sellers']:
            return jsonify({"error": "Invalid collection name"}), 400

        # Fetch users from the specified Firestore collection
        users_ref = db.collection(collection)
        users = [doc.to_dict() | {"id": doc.id} for doc in users_ref.stream()]
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Disable a user (update isDisabled field)
@app.route('/disable-user/<collection>/<user_id>', methods=['POST'])
def disable_user(collection, user_id):
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({"error": "Unauthorized access"}), 401
    try:
        if collection not in ['buyers', 'sellers']:
            return jsonify({"error": "Invalid collection name"}), 400

        # Update the 'isDisabled' field in Firestore
        user_ref = db.collection(collection).document(user_id)
        user_ref.update({"isDisabled": True})
        return jsonify({"message": f"User {user_id} disabled successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Delete a user from Firestore and Firebase Authentication
@app.route('/delete-user/<collection>/<user_id>', methods=['DELETE'])
def delete_user(collection, user_id):
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({"error": "Unauthorized access"}), 401
    try:
        if collection not in ['buyers', 'sellers']:
            return jsonify({"error": "Invalid collection name"}), 400

        # Fetch user document from Firestore
        user_ref = db.collection(collection).document(user_id)
        user_data = user_ref.get().to_dict()

        if user_data:
            # Delete user from Firebase Authentication if authId exists
            auth_id = user_data.get("authId")
            if auth_id:
                auth.delete_user(auth_id)

            # Delete user document from Firestore
            user_ref.delete()

            return jsonify({"message": f"User {user_id} deleted successfully."}), 200
        else:
            return jsonify({"error": "User not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=8080)
