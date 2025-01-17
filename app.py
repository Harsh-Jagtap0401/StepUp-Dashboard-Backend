from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import pandas as pd
from sqlalchemy import text
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
 
# Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Test_12345678",
    "database": "TestResultsDB",
}
 
class Config:
    SECRET_KEY = "your_secret_key"
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
 
# Initialize Flask app and extensions
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db = SQLAlchemy(app)
 
# Models
class Participant(db.Model):
    __tablename__ = 'Participants'
    ParticipantID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(255))
    Email = db.Column(db.String(255))
 
class Batch(db.Model):
    __tablename__ = 'Batches'
    BatchID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    BatchNo = db.Column(db.String(255))
 
class Subject(db.Model):
    __tablename__ = 'Subjects'
    SubjectID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SubjectName = db.Column(db.String(255))
 
class Level(db.Model):
    __tablename__ = 'Levels'
    LevelID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    LevelNo = db.Column(db.String(255))
 
class Attempt(db.Model):
    __tablename__ = 'Attempts'
    AttemptID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    AttemptNo = db.Column(db.String(255))
 
class TestResult(db.Model):
    __tablename__ = 'TestResults'
    TestResultID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ParticipantID = db.Column(db.Integer, db.ForeignKey('Participants.ParticipantID'))
    BatchID = db.Column(db.Integer, db.ForeignKey('Batches.BatchID'))
    SubjectID = db.Column(db.Integer, db.ForeignKey('Subjects.SubjectID'))
    LevelID = db.Column(db.Integer, db.ForeignKey('Levels.LevelID'))
    AttemptID = db.Column(db.Integer, db.ForeignKey('Attempts.AttemptID'))
    InviteTime = db.Column(db.DateTime)
    TestStatus = db.Column(db.String(255))
    SubmittedDate = db.Column(db.DateTime)
    LowestScore = db.Column(db.Float)
    HighestScore = db.Column(db.Float)
 
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))  # Increase the length to 255
 
# Function to extract details from the test name
def extract_details(test_name):
    # Define possible batches, levels, and subjects
    batches = ["Batch1", "Batch2", "Batch3", "Batch4", "Batch5"]
    levels = ["Level1", "Level2", "Level3", "Level4", "Level5"]
    subjects = [
        "Prompt Engineering",
        "Core Software Engineering Coding Skills",
        "Core Software Engineering",
        "NodeJS  for SE/SSE"
    ]
 
    # Extract batch
    batch_no = next((batch for batch in batches if batch in test_name), None)
 
    # Extract level
    level_no = next((level for level in levels if level in test_name), None)
 
    # Extract subject
    subject = next((subj for subj in subjects if subj in test_name), None)
 
    # Extract attempt
    attempt_no = next((part for part in test_name.split('_') if part.startswith("Attempt")), None)
 
    return batch_no, subject, level_no, attempt_no
 
# Function to convert string to datetime
def convert_to_datetime(date_str):
    return datetime.strptime(date_str, '%A, %b %d %Y at %I:%M %p').strftime('%Y-%m-%d %H:%M:%S')
 

# Route to upload and save data
@app.route('/admin/upload', methods=['POST'])
def upload_data():
    print("Received request to /upload")
    file = request.files['file']
    df = pd.read_excel(file, sheet_name=1)  # Read the second sheet
 
    # Print column names to verify they are correct
    print(df.columns)
 
    for index, row in df.iterrows():
        name = row['Name']
        email = row['Email']
        test_name = row['Test name']
        invite_time = convert_to_datetime(row['Invites Time'])
        test_status = row['Test Status']
       
        # Check if 'Submitted Date' exists and is not NaT
        if pd.notna(row['Submitted Date']):
            if isinstance(row['Submitted Date'], str):
                submitted_date = convert_to_datetime(row['Submitted Date'])
            else:
                submitted_date = row['Submitted Date'].strftime('%Y-%m-%d %H:%M:%S')
        else:
            submitted_date = None  # or set to a default value like '0000-00-00 00:00:00'
       
        lowest_score = row['Lowest Score']
        highest_score = row['Highest Score']
 
        batch_no, subject, level_no, attempt_no = extract_details(test_name)
 
        # Insert participant if not exists
        participant_query = text(f"SELECT ParticipantID FROM Participants WHERE Email = '{email}'")
        participant_result = db.session.execute(participant_query).fetchone()
        if participant_result:
            participant_id = participant_result[0]
        else:
            insert_participant = text(f"INSERT INTO Participants (Name, Email) VALUES ('{name}', '{email}')")
            db.session.execute(insert_participant)
            db.session.commit()
            participant_id = db.session.execute(participant_query).fetchone()[0]
 
        # Insert batch if not exists
        batch_query = text(f"SELECT BatchID FROM Batches WHERE BatchNo = '{batch_no}'")
        batch_result = db.session.execute(batch_query).fetchone()
        if batch_result:
            batch_id = batch_result[0]
        else:
            insert_batch = text(f"INSERT INTO Batches (BatchNo) VALUES ('{batch_no}')")
            db.session.execute(insert_batch)
            db.session.commit()
            batch_id = db.session.execute(batch_query).fetchone()[0]
 
        # Insert subject if not exists
        subject_query = text(f"SELECT SubjectID FROM Subjects WHERE SubjectName = '{subject}'")
        subject_result = db.session.execute(subject_query).fetchone()
        if subject_result:
            subject_id = subject_result[0]
        else:
            insert_subject = text(f"INSERT INTO Subjects (SubjectName) VALUES ('{subject}')")
            db.session.execute(insert_subject)
            db.session.commit()
            subject_id = db.session.execute(subject_query).fetchone()[0]
 
        # Insert level if not exists
        level_query = text(f"SELECT LevelID FROM Levels WHERE LevelNo = '{level_no}'")
        level_result = db.session.execute(level_query).fetchone()
        if level_result:
            level_id = level_result[0]
        else:
            insert_level = text(f"INSERT INTO Levels (LevelNo) VALUES ('{level_no}')")
            db.session.execute(insert_level)
            db.session.commit()
            level_id = db.session.execute(level_query).fetchone()[0]
 
        # Insert attempt if not exists
        attempt_query = text(f"SELECT AttemptID FROM Attempts WHERE AttemptNo = '{attempt_no}'")
        attempt_result = db.session.execute(attempt_query).fetchone()
        if attempt_result:
            attempt_id = attempt_result[0]
        else:
            insert_attempt = text(f"INSERT INTO Attempts (AttemptNo) VALUES ('{attempt_no}')")
            db.session.execute(insert_attempt)
            db.session.commit()
            attempt_id = db.session.execute(attempt_query).fetchone()[0]
 
        # Insert test result
        insert_test_result = text(f"""
            INSERT INTO TestResults (
                ParticipantID, BatchID, SubjectID, LevelID, AttemptID, InviteTime, TestStatus, SubmittedDate, LowestScore, HighestScore
            ) VALUES (
                {participant_id}, {batch_id}, {subject_id}, {level_id}, {attempt_id}, '{invite_time}', '{test_status}',
                {'NULL' if submitted_date is None else f"'{submitted_date}'"}, {lowest_score}, {highest_score}
            )
        """)
        db.session.execute(insert_test_result)
        db.session.commit()
 
    return jsonify({'message': 'Data uploaded successfully'}), 200

@app.route('/dashboard', methods=['GET'])
def dashboard():
    print("Received request to /dashboard")
    batch_filter = request.args.get('batch')
    level_filter = request.args.get('level')

    query = text("""
    SELECT 
        b.BatchNo, l.LevelNo,
        COUNT(CASE WHEN tr.TestStatus = 'Cleared CutOff' THEN 1 END) AS ClearedCutoffCount,
        COUNT(CASE WHEN tr.TestStatus = 'Failed CutOff' THEN 1 END) AS FailedCutoffCount,
        COUNT(CASE WHEN tr.TestStatus = 'InProgress' THEN 1 END) AS InProgressCount,
        COUNT(*) AS InvitedCount
    FROM 
        TestResults tr
    JOIN 
        Participants p ON tr.ParticipantID = p.ParticipantID
    JOIN 
        Batches b ON tr.BatchID = b.BatchID
    JOIN 
        Subjects s ON tr.SubjectID = s.SubjectID
    JOIN 
        Levels l ON tr.LevelID = l.LevelID
    JOIN 
        Attempts a ON tr.AttemptID = a.AttemptID
    WHERE 
        (:batch IS NULL OR b.BatchNo = :batch)
        AND (:level IS NULL OR l.LevelNo = :level)
    GROUP BY 
        b.BatchNo, l.LevelNo
    """)
    results = db.session.execute(query, {'batch': batch_filter, 'level': level_filter}).fetchall()

    data = []
    for row in results:
        data.append({
            'BatchNo': row.BatchNo,
            'LevelNo': row.LevelNo,
            'ClearedCutoffCount': row.ClearedCutoffCount,
            'FailedCutoffCount': row.FailedCutoffCount,
            'InProgressCount': row.InProgressCount,
            'InvitedCount': row.InvitedCount
        })

    return jsonify(data), 200

@app.route('/user/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    new_user = User(name=name, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Signup successful!'}), 201

@app.route('/user/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        user_details = {
            'name': user.name,
            'email': user.email,
            # Add any other details you want to return
        }
        return jsonify({'message': 'Login successful!', 'user': user_details}), 200

    return jsonify({'message': 'Invalid credentials!'}), 401

@app.route('/user/details', methods=['GET'])
def user_details():
    email = request.args.get('email')
    participant = Participant.query.filter_by(Email=email).first()

    if participant:
        query = text("""
        SELECT tr.InviteTime, tr.TestStatus, tr.SubmittedDate, tr.LowestScore, tr.HighestScore,
               b.BatchNo, l.LevelNo, s.SubjectName, a.AttemptNo
        FROM TestResults tr
        JOIN Batches b ON tr.BatchID = b.BatchID
        JOIN Levels l ON tr.LevelID = l.LevelID
        JOIN Subjects s ON tr.SubjectID = s.SubjectID
        JOIN Attempts a ON tr.AttemptID = a.AttemptID
        WHERE tr.ParticipantID = :participant_id
        """)
        results = db.session.execute(query, {'participant_id': participant.ParticipantID}).fetchall()

        test_results = []
        for row in results:
            test_results.append({
                'InviteTime': row.InviteTime,
                'TestStatus': row.TestStatus,
                'SubmittedDate': row.SubmittedDate,
                'LowestScore': row.LowestScore,
                'HighestScore': row.HighestScore,
                'BatchNo': row.BatchNo,
                'LevelNo': row.LevelNo,
                'SubjectName': row.SubjectName,
                'AttemptNo': row.AttemptNo
            })

        return jsonify({'participant': participant.Name, 'test_results': test_results}), 200

    return jsonify({'message': 'User not found!'}), 404

@app.route('/level-details', methods=['GET'])
def details():
    batch_no = request.args.get('batch')
    level_no = request.args.get('level')
    query = text("""
    SELECT
        COUNT(CASE WHEN tr.TestStatus = 'Cleared Cutoff' THEN 1 END) AS ClearedCutoffCount,
        COUNT(CASE WHEN tr.TestStatus = 'Failed Cutoff' THEN 1 END) AS FailedCutoffCount,
        COUNT(CASE WHEN tr.TestStatus = 'InProgress' THEN 1 END) AS InProgressCount,
        COUNT(*) AS TotalInvites,
        a.AttemptNo,
        s.SubjectName
    FROM
        TestResults tr
    JOIN
        Participants p ON tr.ParticipantID = p.ParticipantID
    JOIN
        Batches b ON tr.BatchID = b.BatchID
    JOIN
        Subjects s ON tr.SubjectID = s.SubjectID
    JOIN
        Levels l ON tr.LevelID = l.LevelID
    JOIN
        Attempts a ON tr.AttemptID = a.AttemptID
    WHERE
        b.BatchNo = :batch_no AND l.LevelNo = :level_no
    GROUP BY
        a.AttemptNo, s.SubjectName
    """)
    
    results = db.session.execute(query, {'batch_no': batch_no, 'level_no': level_no}).fetchall()
    data = []
    for row in results:
        data.append({
            'ClearedCutoffCount': row.ClearedCutoffCount,
            'FailedCutoffCount': row.FailedCutoffCount,
            'InProgressCount': row.InProgressCount,
            'TotalInvites': row.TotalInvites,
            'AttemptNo': row.AttemptNo,
            'SubjectName': row.SubjectName
        })
    return jsonify(data), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)