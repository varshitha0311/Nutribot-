# app.py - FINAL FIXED VERSION WITH AUTHENTICATION CONTEXT
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os

app = Flask(__name__)
app.secret_key = "foodai_super_secret_key_2026"

# ====================== DATABASE ======================
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",           # ← Change if needed
        database="food_classification",
        port=3306
    )

# ====================== MODEL ======================
device = torch.device('cpu')
model = models.vgg16(weights=None)
model.classifier = nn.Sequential(
    nn.Linear(25088, 2048), nn.ReLU(True), nn.Dropout(0.5),
    nn.Linear(2048, 512),   nn.ReLU(True), nn.Dropout(0.5),
    nn.Linear(512, 12)
)
model.load_state_dict(torch.load('saved_models/best_model.pth', map_location=device))
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

CLASS_NAMES = ['apple_pie', 'cannoli', 'cheese_plate', 'cheesecake', 'chicken_wings',
               'chocolate_cake', 'deviled_eggs', 'donuts', 'french_fries', 'frozen_yogurt',
               'ice_cream', 'macarons']

NUTRITION = {
    "apple_pie": "345 calories, Fat 12.5g, Carbs 37.1g, Protein 2.4g. Limit these to only special occasions...",
    "cannoli": "254 calories, Fat 11.04g, Carbs 28.84g, Protein 8.7g...",
    "cheesecake": "321 Calories/100g, Fat 22.5g, Carbs 25.5g, Protein 5.5g...",
    "cheese_plate": "380 Calories/100g, Fat 27.8g, Carbs 5.38g, Protein 26.93g...",
    "chicken_wings": "288 calories/100g, Fat 19.3g, Carbs 0g, Protein 26.64g...",
    "chocolate_cake": "367 calories/100g, Fat 16.4g, Carbs 54.6g, Protein 4.1g...",
    "deviled_eggs": "201 Calories/100g, Fat 16.23g, Carbs 1.35g, Protein 11.57g...",
    "donuts": "452 Calories/100g, Fat 22.85g, Carbs 47g, Protein 5.7g...",
    "french_fries": "312 Calories/100g, Fat 14.06g, Carbs 35.66g, Protein 3.48g...",
    "frozen_yogurt": "159 Calories/100g, Fat 1.47g, Carbs 19.62g, Protein 4.7g...",
    "ice_cream": "207 Calories/100g, Fat 10.72g, Carbs 24.4g, Protein 3.52g...",
    "macarons": "404 Calories/100g, Fat 22.30g, Carbs 49.70, Protein 8.80g..."
}

# ====================== HELPER FUNCTION ======================
def add_auth_context(template, **kwargs):
    """Add authentication context to all templates"""
    kwargs['logged_in'] = 'user' in session
    kwargs['username'] = session.get('user', '')
    return render_template(template, **kwargs)

# ====================== ROUTES ======================

@app.route('/')
def home():
    return add_auth_context('home.html')

@app.route('/about')
def about():
    return add_auth_context('about.html')

@app.route('/algo')
def algo():
    return add_auth_context('algo.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        password = generate_password_hash(request.form['password'])

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, full_name, email, phone, password) VALUES (%s, %s, %s, %s, %s)",
                           (username, full_name, email, phone, password))
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect('/login')
        except mysql.connector.IntegrityError:
            flash("Email or Username already exists!", "danger")
        except Exception as e:
            flash(f"Registration error: {str(e)}", "danger")
        finally:
            cursor.close()
            conn.close()
    
    # Check if user is already logged in
    if 'user' in session:
        return redirect('/predict')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']
            session['email'] = user['email']
            session['user_id'] = user['id']
            flash("Login successful!", "success")
            return redirect('/predict')
        flash("Invalid email or password", "danger")
    
    # Check if user is already logged in
    if 'user' in session:
        return redirect('/predict')
    
    return render_template('login.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'user' not in session:
        flash("Please login to access the prediction feature", "warning")
        return redirect('/login')

    if request.method == 'POST':
        if 'image' not in request.files or request.files['image'].filename == '':
            flash("Please upload an image", "danger")
            return redirect('/predict')

        file = request.files['image']
        filepath = os.path.join('uploads', file.filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(filepath)

        try:
            img = Image.open(filepath).convert('RGB')
            tensor = transform(img).unsqueeze(0)

            with torch.no_grad():
                output = model(tensor)
                pred_idx = torch.argmax(output, dim=1).item()
                pred_class = CLASS_NAMES[pred_idx]

            nutrition_info = NUTRITION.get(pred_class, "Nutrition data coming soon...")
            
            # Calculate confidence
            probabilities = torch.nn.functional.softmax(output[0], dim=0)
            confidence = f"{probabilities[pred_idx].item() * 100:.2f}%"

            os.remove(filepath)   # cleanup

            return render_template('result.html',
                                   logged_in=True,
                                   username=session['user'],
                                   food_class=pred_class.replace('_', ' ').title(),
                                   nutrition=nutrition_info,
                                   confidence=confidence)
        except Exception as e:
            flash(f"Error processing image: {str(e)}", "danger")
            if os.path.exists(filepath):
                os.remove(filepath)
            return redirect('/predict')

    return render_template('predict.html', logged_in=True, username=session['user'])

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully", "info")
    return redirect('/')

if __name__ == '__main__':
    # Create uploads directory if it doesn't exist
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, port=5000)