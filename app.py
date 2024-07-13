# app.py
import os
import cv2
from flask import Flask, render_template, Response, redirect, url_for, session, flash, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dumbel_curl_script import PoseDetector
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.secret_key = os.getenv("SECRET_KEY", "__privatekey__")
app.config['STATIC_URL_PATH'] = '/static'
app.config['STATIC_FOLDER'] = 'static'
app.config['UPLOAD_FOLDER'] = os.path.join(app.config['STATIC_FOLDER'], 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True

db = SQLAlchemy(app)
migrate = Migrate(app, db)

pose_detector = PoseDetector()

# Create the uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    profile_picture = db.Column(db.String(100), nullable=True)

    def __init__(self, name, email, password, age, height, weight, profile_picture=None):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)
        self.age = age
        self.height = height
        self.weight = weight
        self.profile_picture = profile_picture
        

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', back_populates='workouts')
    def __init__(self, date, exercise, sets, reps, weight=None):
        self.date = date
        self.exercise = exercise
        self.sets = sets
        self.reps = reps
        self.weight = weight

    def to_dict(self):
        return {
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'exercise': self.exercise,
            'sets': self.sets,
            'reps': self.reps,
            'weight': self.weight
        }

User.workouts = db.relationship('Workout', order_by=Workout.id, back_populates='user')




@app.route('/workouts', methods=['GET', 'POST'])
def workouts():
    if 'user_id' in session:
        user_id = session['user_id']

        if request.method == 'POST':
            exercise = request.form['exercise']
            sets = request.form['sets']
            reps = request.form['reps']
            weight = request.form['weight'] if request.form['weight'] else None
            
            new_workout = Workout(user_id=user_id, exercise=exercise, sets=sets, reps=reps, weight=weight)
            db.session.add(new_workout)
            db.session.commit()
            
            flash('Workout logged successfully')
            return redirect(url_for('workouts'))

        user = User.query.filter_by(id=user_id).first()
        workout_objects = Workout.query.filter_by(user_id=user_id).all()
        workouts = [workout.to_dict() for workout in workout_objects]
        return render_template('workouts.html', user=user, workouts=workouts)
    else:
        return redirect(url_for('index'))



@app.route('/download_csv', methods=['POST'])
def download_csv():
    csv_data = request.form['csv_data']

    # Create a response with CSV as a file attachment
    output = io.StringIO()
    output.write(csv_data)
    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=workout_history.csv"}
    )




@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        return redirect(url_for('info'))
    else:
        flash('Invalid email or password')
        return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    age = request.form['age']
    height = request.form['height']
    weight = request.form['weight']
    if User.query.filter_by(email=email).first():
        flash('Email already registered')
        return redirect(url_for('index'))

    new_user = User(name=name, email=email, password=password, age=age, height=height, weight=weight)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/info')
def info():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        return render_template('info.html', user=user)
    else:
        return redirect(url_for('index'))

@app.route('/guest_info')
def guest_info():
    return render_template('info.html', user=None)

@app.route('/profile')
def profile():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        return render_template('profile.html', user=user)
    else:
        return redirect(url_for('index'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        user.name = request.form['name']
        user.email = request.form['email']
        user.age = request.form['age']
        user.height = request.form['height']
        user.weight = request.form['weight']
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                user.profile_picture = filename

        db.session.commit()
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('index'))

@app.route('/diet')
def diet():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        return render_template('diet.html', user=user)
    else:
        return redirect(url_for('index'))

@app.route('/exercise')
def exercise():
    return render_template('exercise.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames():
    camera = cv2.VideoCapture(0)  
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            frame = pose_detector.process_frame(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/generate_pdf')
def generate_pdf():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        bmi = round(user.weight / ((user.height / 100) ** 2), 2)

        # Create a file-like buffer to receive PDF data
        buffer = io.BytesIO()

        # Create the PDF object, using the buffer as its "file."
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Draw the user data on the PDF
        pdf.drawString(100, height - 100, f"Name: {user.name}")
        pdf.drawString(100, height - 120, f"Email: {user.email}")
        pdf.drawString(100, height - 140, f"Age: {user.age}")
        pdf.drawString(100, height - 160, f"Height: {user.height} cm")
        pdf.drawString(100, height - 180, f"Weight: {user.weight} kg")
        pdf.drawString(100, height - 200, f"BMI: {bmi}")

        # Determine BMI status
        if bmi < 19:
            bmi_status = "Underweight"
            diet_suggestions = [
                "Eat more frequently. Have 5-6 small meals throughout the day.",
                "Include nutrient-rich foods in your diet, such as whole grains, lean proteins, and healthy fats.",
                "Drink high-calorie smoothies and shakes.",
                "Snack on nuts, seeds, and dried fruits.",
                "Stay hydrated and avoid skipping meals."
            ]
        elif bmi >= 19 and bmi <= 25:
            bmi_status = "Normal"
            diet_suggestions = [
                "Maintain a balanced diet with a variety of foods from all food groups.",
                "Eat plenty of fruits and vegetables.",
                "Include lean proteins, whole grains, and healthy fats in your meals.",
                "Stay hydrated by drinking plenty of water.",
                "Avoid sugary drinks and excessive junk food."
            ]
        else:
            bmi_status = "Overweight"
            diet_suggestions = [
                "Eat more fruits and vegetables.",
                "Choose whole grains over refined grains.",
                "Include lean proteins, such as chicken, fish, beans, and legumes.",
                "Avoid sugary drinks and opt for water or herbal teas.",
                "Reduce your intake of high-calorie, low-nutrient foods.",
                "Practice portion control and avoid eating late at night."
            ]

        pdf.drawString(100, height - 220, f"BMI Status: {bmi_status}")
        pdf.drawString(100, height - 240, "Diet Suggestions:")

        y = height - 260
        for suggestion in diet_suggestions:
            pdf.drawString(120, y, f"- {suggestion}")
            y -= 20

        # Close the PDF object cleanly
        pdf.showPage()
        pdf.save()

        # Get the value of the BytesIO buffer and write it to the response
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name='diet_plan.pdf', mimetype='application/pdf')
    else:
        return redirect(url_for('index'))


# Add a new route for the nearest gym
# Add a new route for the nearest gym
@app.route('/nearest_gym')
def nearest_gym():
    api_key = ''
    return render_template('nearest_gym.html', api_key=api_key)


if __name__ == '__main__':
    app.run(debug=True)
