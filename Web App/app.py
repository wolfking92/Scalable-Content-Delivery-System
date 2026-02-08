import os, datetime, mimetypes, boto3, rsa, multiprocessing
from functools import wraps
from flask import Flask, render_template, redirect, request, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from botocore.signers import CloudFrontSigner

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ================= AWS CONFIG =================
S3_BUCKET = "web-app-27-01-2026"
CLOUDFRONT_DOMAIN = "d3hqc2u1zrdf2p.cloudfront.net"
CLOUDFRONT_KEY_PAIR_ID = "K1E8F2X2HQLHHJ"
PRIVATE_KEY_PATH = "/home/ec2-user/web_app/keys/private_rsa_key.pem"

s3_client = boto3.client('s3')

# ================= DATABASE SETUP =================
basedir = os.path.abspath(os.path.dirname(__file__))
os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) 
    is_blocked = db.Column(db.Boolean, default=False)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    instructor_email = db.Column(db.String(150))
    videos = db.relationship('Video', backref='course', lazy=True, cascade='all, delete-orphan')

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    s3_key = db.Column(db.String(500), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

# ================= STRESS TEST LOGIC =================
stress_processes = []

def cpu_stress():
    """Infinite loop to consume CPU"""
    while True:
        pass

# ================= HELPERS =================
def rsa_signer(message):
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        private_key = rsa.PrivateKey.load_pkcs1(key_file.read())
    return rsa.sign(message, private_key, "SHA-1")

cf_signer = CloudFrontSigner(CLOUDFRONT_KEY_PAIR_ID, rsa_signer)

def generate_signed_url(object_key):
    url = f"https://{CLOUDFRONT_DOMAIN}/{object_key}"
    expire_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    return cf_signer.generate_presigned_url(url, date_less_than=expire_date)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ================= ROUTES =================
@app.route("/")
def home(): return redirect(url_for('dashboard')) if 'user_id' in session else redirect(url_for('login'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email, pwd = request.form.get('email'), request.form.get('password')
        if not User.query.filter_by(email=email).first():
            db.session.add(User(email=email, password=generate_password_hash(pwd), role='student'))
            db.session.commit()
            flash('Account created!', 'success')
            return redirect(url_for('login'))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            if not user.is_blocked:
                session.update({'user_id': user.id, 'email': user.email, 'role': user.role})
                return redirect(url_for('dashboard'))
        flash('Invalid login', 'error')
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/dashboard")
@login_required
def dashboard():
    role = session['role']
    is_stressing = len(stress_processes) > 0
    if role == 'admin':
        return render_template('admin_dash.html', users=User.query.all(), student_count=User.query.filter_by(role='student').count(), is_stressing=is_stressing)
    elif role == 'teacher':
        return render_template('instructor_dash.html', courses=Course.query.filter_by(instructor_email=session['email']).all())
    return render_template('student_dash.html', courses=Course.query.all())

# STRESS CONTROL ROUTES
@app.route("/admin/stress/start")
@login_required
def start_stress():
    if session['role'] == 'admin' and not stress_processes:
        for _ in range(multiprocessing.cpu_count()):
            p = multiprocessing.Process(target=cpu_stress)
            p.start()
            stress_processes.append(p)
        flash("CPU Stress Started (100% Load)", "success")
    return redirect(url_for('dashboard'))

@app.route("/admin/stress/stop")
@login_required
def stop_stress():
    if session['role'] == 'admin':
        while stress_processes:
            p = stress_processes.pop()
            p.terminate()
        flash("CPU Stress Stopped", "success")
    return redirect(url_for('dashboard'))

@app.route("/create_course", methods=["POST"])
@login_required
def create_course():
    if session['role'] == 'teacher':
        db.session.add(Course(title=request.form.get('title'), instructor_email=session['email']))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route("/teacher/course/<int:cid>")
@login_required
def teacher_course_view(cid):
    course = Course.query.get_or_404(cid)
    return render_template('teacher_course_detail.html', course=course)

@app.route("/upload/<int:cid>", methods=["POST"])
@login_required
def upload_video(cid):
    file = request.files.get('video_file')
    if file:
        filename = secure_filename(file.filename)
        s3_key = f"videos/{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        s3_client.upload_fileobj(file, S3_BUCKET, s3_key, ExtraArgs={'ContentType': mimetypes.guess_type(filename)[0] or 'video/mp4'})
        db.session.add(Video(title=request.form.get('video_title'), s3_key=s3_key, course_id=cid))
        db.session.commit()
    return redirect(url_for('teacher_course_view', cid=cid))

@app.route("/course/<int:cid>")
@login_required
def student_course_view(cid):
    course = Course.query.get_or_404(cid)
    for video in course.videos:
        video.url = generate_signed_url(video.s3_key)
    return render_template("student_course.html", course=course)

@app.route("/admin/create_teacher", methods=["POST"])
@login_required
def create_teacher():
    if session['role'] == 'admin':
        db.session.add(User(email=request.form.get('email'), password=generate_password_hash(request.form.get('password')), role='teacher'))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route("/admin/block/<int:user_id>")
@login_required
def block_user(user_id):
    if session['role'] == 'admin':
        user = User.query.get_or_404(user_id)
        user.is_blocked = not user.is_blocked
        db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@test.com').first():
            db.session.add(User(email='admin@test.com', password=generate_password_hash('admin123'), role='admin'))
            db.session.add(User(email='teacher@test.com', password=generate_password_hash('teacher123'), role='teacher'))
            db.session.add(User(email='student@test.com', password=generate_password_hash('student123'), role='student'))
            db.session.commit()
    app.run(host="0.0.0.0", port=5000, debug=True)