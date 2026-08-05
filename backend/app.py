from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, jsonify 
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError, IntegrityError
import sys
import os
from datetime import datetime
import mysql.connector

app = Flask(__name__)

# Secret key for session signing
app.secret_key = "your-secret-key"

# MySQL connection configurations
DB_HOST     = "localhost"
DB_USER     = "your_mysql_username"
DB_PASSWORD = "your_mysql_password"
DB_NAME     = "smsam_database"

# Database Agnostic Connection Strategy
mysql_available = False
try:
    
    # Quick probe to see if MySQL is running and credentials are valid
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        connection_timeout=2
    )
    if conn.is_connected():
        mysql_available = True
        conn.close()
except Exception as exc:
    print(f"[SMSAM] [INFO] MySQL check failed: {exc}. Falling back to SQLite.")

if mysql_available:
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    )
    # Prevent MySQL "gone away" errors on long-idle connections
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
    }
    print("[SMSAM] Connected to MySQL successfully.")
else:
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance', 'smsam.db'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    print(f"[SMSAM] Using local SQLite database at: {db_path}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    """
    Stores all user accounts.
    permissions: comma-separated list of sensor keys
                 e.g. 'temperature,humidity,motion,distance,camera,ldr'
    """
    __tablename__ = 'users'

    id          = db.Column(db.Integer, primary_key=True)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    password    = db.Column(db.String(120), nullable=False)  
    name        = db.Column(db.String(120), nullable=False)
    role        = db.Column(db.String(20),  default='user')
    permissions = db.Column(db.String(500), default='temperature,humidity')

    def get_permissions_list(self):
        """Return the permissions field as a Python list."""
        if self.permissions:
            return [p.strip() for p in self.permissions.split(',') if p.strip()]
        return []

    def __repr__(self):
        return f"<User {self.email} | role={self.role}>"

class UltrasonicData(db.Model):
    __tablename__ = 'ultrasonic_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    distance_cm = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "distance_cm": self.distance_cm,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if self.timestamp else None,
        }

class LdrData(db.Model):
    """
    Stores readings from the LDR (Light Dependent Resistor).
    Maps to:  ldr_data table
    Schema:   id INT PK  |  light_intensity FLOAT  |  timestamp DATETIME
    """
    __tablename__ = 'ldr_data'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    light_intensity = db.Column(db.Float, nullable=False)
    timestamp       = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id"             : self.id,
            "light_intensity": self.light_intensity,
            "timestamp"      : self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                               if self.timestamp else None,
        }

    def __repr__(self):
        return f"<LdrData id={self.id} light_intensity={self.light_intensity}>"


class PirData(db.Model):
    """
    Stores readings from the PIR (Passive Infrared) motion sensor.
    Maps to:  pir_data table
    Schema:   id INT PK  |  motion_detected BOOLEAN  |  timestamp DATETIME
    """
    __tablename__ = 'pir_data'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    motion_detected = db.Column(db.Boolean, nullable=False)
    timestamp       = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id"             : self.id,
            "motion_detected": self.motion_detected,
            "timestamp"      : self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                               if self.timestamp else None,
        }

    def __repr__(self):
        return f"<PirData id={self.id} motion_detected={self.motion_detected}>"


class Dht22Data(db.Model):
    """
    Stores temperature + humidity readings from the DHT22 sensor.
    Maps to:  dht22_data table
    Schema:   id INT PK  |  temperature FLOAT  |  humidity FLOAT  |  timestamp DATETIME
    """
    __tablename__ = 'dht22_data'

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    temperature = db.Column(db.Float, nullable=False)
    humidity    = db.Column(db.Float, nullable=False)
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id"         : self.id,
            "temperature": self.temperature,
            "humidity"   : self.humidity,
            "timestamp"  : self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                           if self.timestamp else None,
        }

    def __repr__(self):
        return f"<Dht22Data id={self.id} temp={self.temperature} hum={self.humidity}>"



# Default users to seed when the database is first created.

DEFAULT_USERS = [
    {
        "email": "admin@example.com",
        "password": "change_me",
        "name": "Administrator",
        "role": "admin",
        "permissions": "temperature,humidity,motion,distance,camera,ldr",
    },
    {
        "email"      : "loel@example.com",
        "password"   : "demo_password",
        "name"       : "Loel",
        "role"       : "user",
        "permissions": "camera",
    },
    {
        "email"      : "rhema@example.com",
        "password"   : "demo_password",
        "name"       : "Rhema",
        "role"       : "user",
        "permissions": "distance",
    },
    {
        "email"      : "karabelo@example.com",
        "password"   : "demo_password",
        "name"       : "Karabelo",
        "role"       : "user",
        "permissions": "motion",
    },
    {
        "email"      : "lebo@example.com",
        "password"   : "demo_password",
        "name"       : "Lebo",
        "role"       : "user",
        "permissions": "ldr",
    },
    {
        "email"      : "revonia@example.com",
        "password"   : "demo_password",
        "name"       : "Revonia",
        "role"       : "user",
        "permissions": "temperature,humidity",
    },
]


def initialise_database():
    """
    Called once at startup inside the application context.
    1. Attempts to connect to the database and creates tables if they don't exist.
    2. Seeds default users only when they are absent (idempotent).
    """
    try:
        db.create_all()
        print("[SMSAM] [SUCCESS] Database tables verified/created successfully.")
    except Exception as exc:
        print(f"\n[SMSAM] [ERROR] Could not initialize the database: {exc}\n")
        sys.exit(1)

    # Seed default users (skip if already present) 
    inserted = 0
    for user_data in DEFAULT_USERS:
        exists = User.query.filter_by(email=user_data["email"]).first()
        if not exists:
            new_user = User(
                email       = user_data["email"],
                password    = user_data["password"],
                name        = user_data["name"],
                role        = user_data["role"],
                permissions = user_data["permissions"],
            )
            db.session.add(new_user)
            inserted += 1

    if inserted:
        try:
            db.session.commit()
            print(f"[SMSAM] [SUCCESS] Seeded {inserted} default user(s).")
        except IntegrityError:
            db.session.rollback()
            print("[SMSAM] [WARNING] Seed skipped — integrity error (users may already exist).")
    else:
        print("[SMSAM] [SUCCESS] Default users already present. No seeding required.")


with app.app_context():
    initialise_database()


def get_current_user():
    """Return the logged-in User object, or None."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


def login_required(f):
    """Simple login guard — redirect to /login if no active session."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            session.pop('user_id', None)
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated


def permission_required(permission_key):
    """
    Decorator that checks whether the logged-in user holds a specific
    permission. Returns 403 Forbidden if the check fails.
    """
    from functools import wraps

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                return redirect(url_for('login'))
            permissions = set(user.get_permissions_list())
            if permission_key not in permissions:
                return (
                    "<h2 style='font-family:sans-serif;text-align:center;"
                    "margin-top:10vh;color:#dc2626'>403 — Access Denied</h2>"
                    "<p style='text-align:center;font-family:sans-serif;"
                    "color:#64748b'>You do not have permission to view this page.</p>",
                    403,
                )
            return f(*args, **kwargs)

        return decorated

    return decorator


# Dashboard / Home 
@app.route('/')
@login_required
def index():
    user = get_current_user()
    return render_template(
        'index.html',
        user=user,
        permissions=user.get_permissions_list(),
    )


# Authentication 
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Already logged in → go to dashboard
    if session.get('user_id'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.')
            return render_template('login.html')

        try:
            user = User.query.filter_by(email=email).first()
        except OperationalError:
            flash('Database connection error. Please try again later.')
            return render_template('login.html')


        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password. Please try again.')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        email       = request.form.get('email', '').strip()
        password    = request.form.get('password', '')
        role        = request.form.get('role', 'user')
        permissions = request.form.getlist('permissions') 

        #  Basic validation 
        if not name or not email or not password:
            flash('All fields are required.')
            return redirect(url_for('signup'))

        #  Duplicate-email check 
        try:
            existing = User.query.filter_by(email=email).first()
        except OperationalError:
            flash('Database connection error. Please try again later.')
            return redirect(url_for('signup'))

        if existing:
            flash('That email address is already registered. Please sign in.')
            return redirect(url_for('signup'))

        #  Create new user 
        new_user = User(
            name        = name,
            email       = email,
            password    = password,             
            role        = role,
            permissions = ','.join(permissions),   # e.g. 'temperature,humidity'
        )

        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('That email address is already registered.')
            return redirect(url_for('signup'))
        except OperationalError:
            db.session.rollback()
            flash('Database error during account creation. Please try again.')
            return redirect(url_for('signup'))

        flash('Account created successfully! Please sign in.')
        return redirect(url_for('login'))

    return render_template('signup.html')


# Info Pages 
@app.route('/about')
@login_required
def about():
    user = get_current_user()
    return render_template('about.html', user=user)


#  Sensor Dashboard Routes 
@app.route('/temperature')
@login_required
@permission_required('temperature')
def temperature():
    user = get_current_user()
    return render_template('temperature_new.html', user=user)


@app.route('/humidity')
@login_required
@permission_required('humidity')
def humidity():
    user = get_current_user()
    return render_template('humidity_new.html', user=user)


@app.route('/motion')
@login_required
@permission_required('motion')
def motion():
    user = get_current_user()
    try:
        latest = PirData.query.order_by(PirData.id.desc()).first()
        latest_data = latest.to_dict() if latest else {"id": None, "motion_detected": False, "timestamp": None}
        
        # Get the last 8 events where motion was detected
        recent = PirData.query.filter_by(motion_detected=True).order_by(PirData.timestamp.desc()).limit(8).all()
        recent_detections = [r.to_dict() for r in recent]
    except Exception as exc:
        print(f"[SMSAM] [WARNING] Failed to query PIR history: {exc}")
        latest_data = {"id": None, "motion_detected": False, "timestamp": None}
        recent_detections = []
        
    return render_template('motion_new.html', user=user, latest_data=latest_data, recent_detections=recent_detections)


@app.route('/distance')
@login_required
@permission_required('distance')
def distance():
    user = get_current_user()
    return render_template('distance_new.html', user=user)


@app.route('/camera')
@login_required
@permission_required('camera')
def camera():
    user = get_current_user()
    return render_template('camera.html', user=user)


@app.route('/ldr')
@login_required
@permission_required('ldr')
def ldr():
    user = get_current_user()
    return render_template('ldr_new.html', user=user)


@app.route('/api/logs')
@login_required
def api_logs():
    """
    Returns the last 30 sensor events across all tables the logged-in user
    has permission to see, merged and sorted newest-first.
    Each entry:  { type, icon, message, timestamp }
    """
    user = get_current_user()
    perms = set(user.get_permissions_list())
    events = []

    try:
        if 'temperature' in perms or 'humidity' in perms:
            rows = Dht22Data.query.order_by(Dht22Data.timestamp.desc()).limit(10).all()
            for r in rows:
                ts = r.timestamp.strftime('%H:%M:%S') if r.timestamp else '—'
                events.append({
                    'type': 'dht22',
                    'icon': '🌡️',
                    'message': f'DHT22 — Temp: {r.temperature:.1f}°C  Humidity: {r.humidity:.1f}%',
                    'timestamp': ts,
                    'sort_ts': r.timestamp.isoformat() if r.timestamp else ''
                })

        if 'motion' in perms:
            rows = PirData.query.order_by(PirData.timestamp.desc()).limit(10).all()
            for r in rows:
                ts = r.timestamp.strftime('%H:%M:%S') if r.timestamp else '—'
                state = 'MOTION DETECTED' if r.motion_detected else 'Cleared'
                icon = '🚨' if r.motion_detected else '✅'
                events.append({
                    'type': 'pir',
                    'icon': icon,
                    'message': f'PIR — {state}',
                    'timestamp': ts,
                    'sort_ts': r.timestamp.isoformat() if r.timestamp else ''
                })

        if 'distance' in perms:
            rows = UltrasonicData.query.order_by(UltrasonicData.timestamp.desc()).limit(10).all()
            for r in rows:
                ts = r.timestamp.strftime('%H:%M:%S') if r.timestamp else '—'
                warn = ' ⚠️ BREACH' if r.distance_cm < 20 else ''
                events.append({
                    'type': 'ultrasonic',
                    'icon': '📡',
                    'message': f'Ultrasonic — {r.distance_cm:.1f} cm{warn}',
                    'timestamp': ts,
                    'sort_ts': r.timestamp.isoformat() if r.timestamp else ''
                })

        if 'ldr' in perms:
            rows = LdrData.query.order_by(LdrData.timestamp.desc()).limit(10).all()
            for r in rows:
                ts = r.timestamp.strftime('%H:%M:%S') if r.timestamp else '—'
                events.append({
                    'type': 'ldr',
                    'icon': '☀️',
                    'message': f'LDR — Light Intensity: {r.light_intensity:.1f}%',
                    'timestamp': ts,
                    'sort_ts': r.timestamp.isoformat() if r.timestamp else ''
                })

        # Sort newest first and take top 30
        events.sort(key=lambda x: x['sort_ts'], reverse=True)
        for e in events:
            del e['sort_ts']
        events = events[:30]

    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500

    return jsonify({'status': 'ok', 'logs': events})

@app.route('/api/sensor/ultrasonic', methods=['POST'])
def api_ultrasonic_post():
    payload = request.get_json(silent=True)

    if not payload:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    raw_value = payload.get("distance_cm")

    if raw_value is None:
        return jsonify({"status": "error", "message": "Missing distance_cm"}), 400

    try:
        distance = float(raw_value)
    except:
        return jsonify({"status": "error", "message": "Invalid number"}), 400

    if not (0 <= distance <= 500):
        return jsonify({"status": "error", "message": "Out of range"}), 400

    try:
        reading = UltrasonicData(distance_cm=distance)
        db.session.add(reading)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({
        "status": "ok",
        "distance_cm": distance,
        "id": reading.id
    }), 200

@app.route('/api/sensor/ultrasonic/latest', methods=['GET'])
def api_ultrasonic_latest():
    latest = UltrasonicData.query.order_by(UltrasonicData.id.desc()).first()

    if not latest:
        return jsonify({
            "status": "no_data",
            "data": {
                "id": None,
                "distance_cm": 0,
                "timestamp": None
            }
        }), 200

    return jsonify({
        "status": "ok",
        "data": latest.to_dict()
    }), 200


@app.route('/api/sensor/ldr', methods=['POST'])
def api_ldr_post():
    """
    ESP32 sends:
        POST /api/sensor/ldr
        Content-Type: application/json
        { "light_level": 73.4 }

    Stores value as light_intensity in ldr_data table.
    Accepts both key names: 'light_level' (Arduino) and 'light_intensity' (direct).

    Returns:
        200  { "status": "ok",    "id": <int>, "light_intensity": <float> }
        400  { "status": "error", "message": "..." }
        500  { "status": "error", "message": "..." }
    """
    payload = request.get_json(silent=True)

    if not payload:
        return jsonify({
            "status" : "error",
            "message": "Request body must be valid JSON."
        }), 400

    # Accept both key names for compatibility
    raw_value = payload.get("light_level")
    if raw_value is None:
        raw_value = payload.get("light_intensity")

    if raw_value is None:
        return jsonify({
            "status" : "error",
            "message": "Missing required field: 'light_level'."
        }), 400

    try:
        intensity = float(raw_value)
    except (TypeError, ValueError):
        return jsonify({
            "status" : "error",
            "message": f"Invalid value for 'light_level': '{raw_value}'. Must be a number."
        }), 400

    if not (0 <= intensity <= 100):
        return jsonify({
            "status" : "error",
            "message": f"Value out of expected range (0–100): {intensity}"
        }), 400

    try:
        reading = LdrData(light_intensity=intensity)
        db.session.add(reading)
        db.session.commit()
    except OperationalError as exc:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Database error: {str(exc)}"}), 500
    except Exception as exc:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Unexpected error: {str(exc)}"}), 500

    return jsonify({
        "status"         : "ok",
        "id"             : reading.id,
        "light_intensity": reading.light_intensity,
        "timestamp"      : reading.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    }), 200

@app.route('/api/sensor/ldr/latest', methods=['GET'])
def api_ldr_latest():
    """
    Returns the most recent LDR row from MySQL.
    Safe default of 0 when table is empty.
    """
    try:
        latest = LdrData.query.order_by(LdrData.id.desc()).first()
    except OperationalError as exc:
        return jsonify({"status": "error", "message": f"Database error: {str(exc)}"}), 500

    if not latest:
        return jsonify({
            "status": "no_data",
            "data"  : {"id": None, "light_intensity": 0, "timestamp": None}
        }), 200

    return jsonify({"status": "ok", "data": latest.to_dict()}), 200


@app.route('/api/sensor/motion', methods=['POST'])
def api_motion_post():
    """
    ESP32 sends:
        POST /api/sensor/motion
        Content-Type: application/json
        { "motion_detected": true }

    Stores in pir_data table.  Accepts boolean or integer (1/0).

    Returns:
        200  { "status": "ok",    "id": <int>, "motion_detected": <bool> }
        400  { "status": "error", "message": "..." }
        500  { "status": "error", "message": "..." }
    """
    payload = request.get_json(silent=True)

    if not payload:
        return jsonify({
            "status" : "error",
            "message": "Request body must be valid JSON."
        }), 400

    if "motion_detected" not in payload:
        return jsonify({
            "status" : "error",
            "message": "Missing required field: 'motion_detected'."
        }), 400

    raw = payload["motion_detected"]

    # Accept JSON boolean true/false or Arduino integer 1/0
    if isinstance(raw, bool):
        detected = raw
    elif isinstance(raw, int) and raw in (0, 1):
        detected = bool(raw)
    else:
        return jsonify({
            "status" : "error",
            "message": f"Invalid value for 'motion_detected': '{raw}'. Must be true/false or 1/0."
        }), 400

    try:
        reading = PirData(motion_detected=detected)
        db.session.add(reading)
        db.session.commit()
    except OperationalError as exc:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Database error: {str(exc)}"}), 500
    except Exception as exc:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Unexpected error: {str(exc)}"}), 500

    return jsonify({
        "status"         : "ok",
        "id"             : reading.id,
        "motion_detected": reading.motion_detected,
        "timestamp"      : reading.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    }), 200

@app.route('/api/sensor/motion/latest', methods=['GET'])
def api_motion_latest():
    """
    Returns the most recent PIR row from MySQL.
    Safe default of motion_detected:false when table is empty.
    """
    try:
        latest = PirData.query.order_by(PirData.id.desc()).first()
    except OperationalError as exc:
        return jsonify({"status": "error", "message": f"Database error: {str(exc)}"}), 500

    if not latest:
        return jsonify({
            "status": "no_data",
            "data"  : {"id": None, "motion_detected": False, "timestamp": None}
        }), 200

    return jsonify({"status": "ok", "data": latest.to_dict()}), 200


@app.route('/api/sensor/dht22', methods=['POST'])
def api_dht22_post():
    """
    ESP32 sends:
        POST /api/sensor/dht22
        Content-Type: application/json
        { "temperature": 24.5, "humidity": 61.2 }

    Stores both values as one row in dht22_data.

    Returns:
        200  { "status": "ok", "id": <int>, "temperature": <float>, "humidity": <float> }
        400  { "status": "error", "message": "..." }
        500  { "status": "error", "message": "..." }
    """
    payload = request.get_json(silent=True)

    if not payload:
        return jsonify({
            "status" : "error",
            "message": "Request body must be valid JSON."
        }), 400

    raw_temp = payload.get("temperature")
    raw_hum  = payload.get("humidity")

    # Report ALL missing fields in one response
    missing = []
    if raw_temp is None: missing.append("'temperature'")
    if raw_hum  is None: missing.append("'humidity'")
    if missing:
        return jsonify({
            "status" : "error",
            "message": f"Missing required field(s): {', '.join(missing)}."
        }), 400

    try:
        temperature = float(raw_temp)
        humidity    = float(raw_hum)
    except (TypeError, ValueError):
        return jsonify({
            "status" : "error",
            "message": "Both 'temperature' and 'humidity' must be numeric."
        }), 400

    # DHT22 operating ranges per datasheet
    if not (-40 <= temperature <= 80):
        return jsonify({
            "status" : "error",
            "message": f"Temperature out of DHT22 range (-40 to 80°C): {temperature}"
        }), 400

    if not (0 <= humidity <= 100):
        return jsonify({
            "status" : "error",
            "message": f"Humidity out of range (0–100%): {humidity}"
        }), 400

    try:
        reading = Dht22Data(temperature=temperature, humidity=humidity)
        db.session.add(reading)
        db.session.commit()
    except OperationalError as exc:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Database error: {str(exc)}"}), 500
    except Exception as exc:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Unexpected error: {str(exc)}"}), 500

    return jsonify({
        "status"     : "ok",
        "id"         : reading.id,
        "temperature": reading.temperature,
        "humidity"   : reading.humidity,
        "timestamp"  : reading.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    }), 200

@app.route('/api/sensor/dht22/latest', methods=['GET'])
def api_dht22_latest():
    """
    Returns the most recent DHT22 row from MySQL.
    Both temperature.html AND humidity.html poll this single endpoint —
    each page reads only the field it needs from the response.

    Returns:
        200  { "status": "ok",      "data": { id, temperature, humidity, timestamp } }
        200  { "status": "no_data", "data": { id:null, temperature:0, humidity:0, timestamp:null } }
        500  { "status": "error",   "message": "..." }
    """
    try:
        latest = Dht22Data.query.order_by(Dht22Data.id.desc()).first()
    except OperationalError as exc:
        return jsonify({"status": "error", "message": f"Database error: {str(exc)}"}), 500

    if not latest:
        return jsonify({
            "status": "no_data",
            "data"  : {"id": None, "temperature": 0, "humidity": 0, "timestamp": None}
        }), 200

    return jsonify({"status": "ok", "data": latest.to_dict()}), 200



@app.route('/analytics')
@login_required
def analytics():
    """Renders the central analytics page containing generated Seaborn/Matplotlib graphs."""
    user = get_current_user()
    
    # Generate latest graphs and pull metrics
    from analytics_manager import generate_analytics_report
    try:
        metrics = generate_analytics_report(db.engine, 'static/images/graphs/')
        graphs_generated = True
    except Exception as e:
        print(f"[SMSAM Analytics] Error: {e}")
        metrics = {}
        graphs_generated = False
        
    return render_template(
        'analytics.html',
        user=user,
        metrics=metrics,
        permissions=user.get_permissions_list(),
        graphs_generated=graphs_generated
    )


@app.route('/api/analytics/refresh', methods=['POST'])
@login_required
def api_analytics_refresh():
    """API endpoint to manually force graph regeneration."""
    from analytics_manager import generate_analytics_report
    try:
        generate_analytics_report(db.engine, 'static/images/graphs/')
        return jsonify({"status": "ok", "message": "Graphs refreshed successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)