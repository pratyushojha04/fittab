import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.secret_key = "__privatekey__"
app.config['STATIC_URL_PATH'] = '/static'
app.config['STATIC_FOLDER'] = 'static'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
        self.password = password
        self.age = age
        self.height = height
        self.weight = weight
        self.profile_picture = profile_picture

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email, password=password).first()
    if user:
        session['user_id'] = user.id
        return '', 200
    else:
        return '', 401

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    age = request.form['age']
    height = request.form['height']
    weight = request.form['weight']

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

@app.route('/Various Excercises')
def excerise():
    return render_template('exercise.html')

if __name__ == '__main__':
    app.run(debug=True)
