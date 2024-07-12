from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.secret_key = "__privatekey__"
app.config['STATIC_URL_PATH'] = '/static'
app.config['STATIC_FOLDER'] = 'static'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# SQLAlchemy database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)

    def __init__(self, name, email, password, age, height, weight):
        self.name = name
        self.email = email
        self.password = password
        self.age = age
        self.height = height
        self.weight = weight

# Route for the form page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle login
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

# Route to handle registration
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

# Route for the info page
@app.route('/info')
def info():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        return render_template('info.html', user=user)
    else:
        return redirect(url_for('index'))

# Route for guest info page
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


if __name__ == '__main__':
    app.run(debug=True)
