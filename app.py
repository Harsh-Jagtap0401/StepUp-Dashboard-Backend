from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import pandas as pd
from sqlalchemy import text
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
 
 
app = Flask(__name__)
CORS(app)  # Enable CORS
 
# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Test_12345678@localhost/TestResultsDB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
# Create the SQLAlchemy db instance
db = SQLAlchemy(app)

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
        "NodeJS  for SE/SSE",
        "ReactJS  for SE/SSE",
        "Angular For SE/SSE",
        "ReactJS-Leads"
 
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
 
# Route to serve the HTML form
@app.route('/')
def index():
    return render_template('upload.html')
 
# Route to upload and save data
@app.route('/upload', methods=['POST'])
def upload_data():
    file = request.files['file']
    df = pd.read_excel(file, sheet_name=1)  # Read the second sheet
   
    # Print column names to verify they are correct
    print(f"Columns in the uploaded file: {df.columns}")
   
    for index, row in df.iterrows():
        print(f"Processing row: {row['Name']}, {row['Email']}, {row['Test name']}, {row['Invites Time']}, {row['Test Status']}, {row['Submitted Date']}, {row['CN rating']}, {row['Primary Skill']}")
 
        name = row['Name']
        email = row['Email']
        primary_skill = row['Primary Skill']
        test_name = row['Test name']
        invite_time = convert_to_datetime(row['Invites Time'])
 
        # Check if 'Test Status' exists in the DataFrame columns
        if 'Test Status' in df.columns and pd.notna(row['Test Status']): 
            test_status = row['Test Status']
        else:
            test_status = 'NULL'  # or set to a default value like ''
       
        # Check if 'Submitted Date' exists and is not NaT
        if pd.notna(row['Submitted Date']):
            if isinstance(row['Submitted Date'], str):
                submitted_date = convert_to_datetime(row['Submitted Date'])
            else:
                submitted_date = row['Submitted Date'].strftime('%Y-%m-%d %H:%M:%S')
        else:
            submitted_date = 'NULL'  # or set to a default value like '0000-00-00 00:00:00'
       
        # Check if 'CN rating' exists and is not NaN
        if pd.notna(row['CN rating']):
            cn_rating = row['CN rating']
        else:
            cn_rating = 'NULL'
 
        # Check if 'Appeared in test' exists and is not NaN
        if 'Appeared in test' in df.columns and pd.notna(row['Appeared in test']):
            appeared_in_test = row['Appeared in test']
            appeared_in_test_value = True if appeared_in_test == 'Yes' else False
        else:
            appeared_in_test_value = False
 
        batch_no, subject, level_no, attempt_no = extract_details(test_name)
       
        # Insert participant if not exists
        participant_query = text(f"SELECT ParticipantID FROM Participants WHERE Email = '{email}'")
        participant_result = db.session.execute(participant_query).fetchone()
        if participant_result:
            participant_id = participant_result[0]
        else:
            insert_participant = text(f"INSERT INTO Participants (Name, Email, PrimarySkill) VALUES ('{name}', '{email}', '{primary_skill}')")
            db.session.execute(insert_participant)
            db.session.commit()  # Ensure commit
            participant_id = db.session.execute(participant_query).fetchone()[0]
 
        # Insert batch if not exists
        batch_query = text(f"SELECT BatchID FROM Batches WHERE BatchNo = '{batch_no}'")
        batch_result = db.session.execute(batch_query).fetchone()
        if batch_result:
            batch_id = batch_result[0]
        else:
            insert_batch = text(f"INSERT INTO Batches (BatchNo) VALUES ('{batch_no}')")
            db.session.execute(insert_batch)
            db.session.commit()  # Ensure commit
            batch_id = db.session.execute(batch_query).fetchone()[0]
 
        # Insert subject if not exists
        subject_query = text(f"SELECT SubjectID FROM Subjects WHERE SubjectName = '{subject}'")
        subject_result = db.session.execute(subject_query).fetchone()
        if subject_result:
            subject_id = subject_result[0]
        else:
            insert_subject = text(f"INSERT INTO Subjects (SubjectName) VALUES ('{subject}')")
            db.session.execute(insert_subject)
            db.session.commit()  # Ensure commit
            subject_id = db.session.execute(subject_query).fetchone()[0]
 
        # Insert level if not exists
        level_query = text(f"SELECT LevelID FROM Levels WHERE LevelNo = '{level_no}'")
        level_result = db.session.execute(level_query).fetchone()
        if level_result:
            level_id = level_result[0]
        else:
            insert_level = text(f"INSERT INTO Levels (LevelNo) VALUES ('{level_no}')")
            db.session.execute(insert_level)
            db.session.commit()  # Ensure commit
            level_id = db.session.execute(level_query).fetchone()[0]
 
        # Insert attempt if not exists
        attempt_query = text(f"SELECT AttemptID FROM Attempts WHERE AttemptNo = '{attempt_no}'")
        attempt_result = db.session.execute(attempt_query).fetchone()
        if attempt_result:
            attempt_id = attempt_result[0]
        else:
            insert_attempt = text(f"INSERT INTO Attempts (AttemptNo) VALUES ('{attempt_no}')")
            db.session.execute(insert_attempt)
            db.session.commit()  # Ensure commit
            attempt_id = db.session.execute(attempt_query).fetchone()[0]
 
        # Insert test result with AppearedInTest column
        insert_test_result = text(f"""
            INSERT INTO TestResults (
                ParticipantID, BatchID, SubjectID, LevelID, AttemptID, InviteTime, TestStatus, SubmittedDate, CNRating, AppearedInTest
            ) VALUES (
                {participant_id}, {batch_id}, {subject_id}, {level_id}, {attempt_id}, '{invite_time}', {'NULL' if test_status == 'NULL' else f"'{test_status}'"},
                {'NULL' if submitted_date == 'NULL' else f"'{submitted_date}'"}, {cn_rating}, {appeared_in_test_value}
            )
        """)
        db.session.execute(insert_test_result)
        db.session.commit()  # Ensure commit
 
    return jsonify({'message': 'Data uploaded successfully'}), 200
 
 
@app.route('/api/dashboard1', methods=['GET'])
def get_dashboard1_data():
    # Invite Count Query for Level 1
    invite_count_query_level1 = text("""
    SELECT
        b.BatchNo,
        l.LevelNo,
        COUNT(DISTINCT tr.ParticipantID) AS InviteCount
    FROM
        TestResults tr
    JOIN
        Levels l ON tr.LevelID = l.LevelID
    JOIN
        Batches b ON tr.BatchID = b.BatchID
    WHERE
        l.LevelNo = 'Level1'
    GROUP BY
        b.BatchNo, l.LevelNo
    ORDER BY
        b.BatchNo, l.LevelNo;
    """)
    invite_count_results_level1 = db.session.execute(invite_count_query_level1).fetchall()
 
    # Invite Count Query for Level 2
    invite_count_query_level2 = text("""
    SELECT
        b.BatchNo,
        l.LevelNo,
        COUNT(DISTINCT tr.ParticipantID) AS InviteCount
    FROM
        TestResults tr
    JOIN
        Levels l ON tr.LevelID = l.LevelID
    JOIN
        Batches b ON tr.BatchID = b.BatchID
    WHERE
        l.LevelNo = 'Level2'
    GROUP BY
        b.BatchNo, l.LevelNo
    ORDER BY
        b.BatchNo, l.LevelNo;
    """)
    invite_count_results_level2 = db.session.execute(invite_count_query_level2).fetchall()
 
    # Passed Count Query for Level 1
    passed_count_query_level1 = text("""
    SELECT
        b.BatchNo,
        COUNT(DISTINCT p.ParticipantID) AS ParticipantCount
    FROM
        Participants p
    JOIN
        TestResults tr ON p.ParticipantID = tr.ParticipantID
    JOIN
        Subjects s ON tr.SubjectID = s.SubjectID
    JOIN
        Levels l ON tr.LevelID = l.LevelID
    JOIN
        Attempts a ON tr.AttemptID = a.AttemptID
    JOIN
        Batches b ON tr.BatchID = b.BatchID
    WHERE
        l.LevelNo = 'Level1'
        AND tr.CNRating > 4.0
        AND p.ParticipantID IN (
            SELECT
                tr.ParticipantID
            FROM
                TestResults tr
            JOIN
                Subjects s ON tr.SubjectID = s.SubjectID
            JOIN
                Levels l ON tr.LevelID = l.LevelID
            WHERE
                l.LevelNo = 'Level1'
                AND tr.CNRating > 4.0
            GROUP BY
                tr.ParticipantID
            HAVING
                COUNT(DISTINCT s.SubjectID) = (
                    SELECT COUNT(DISTINCT SubjectID)
                    FROM Subjects
                    WHERE SubjectName IN ('Core Software Engineering', 'Prompt Engineering', 'Core Software Engineering Coding Skills')
                )
        )
    GROUP BY
        b.BatchNo
    ORDER BY
        b.BatchNo;
    """)
    passed_count_results_level1 = db.session.execute(passed_count_query_level1).fetchall()
 
    # Passed Count Query for Level 2
    passed_count_query_level2 = text("""
    SELECT
        b.BatchNo,
        COUNT(DISTINCT p.ParticipantID) AS ParticipantCount
    FROM
        Participants p
    JOIN
        TestResults tr ON p.ParticipantID = tr.ParticipantID
    JOIN
        Batches b ON tr.BatchID = b.BatchID
    JOIN
        Subjects s ON tr.SubjectID = s.SubjectID
    JOIN
        Levels l ON tr.LevelID = l.LevelID
    JOIN
        Attempts a ON tr.AttemptID = a.AttemptID
    WHERE
        l.LevelNo = 'Level2'
        AND tr.CNRating >= 4
    GROUP BY
        b.BatchNo
    ORDER BY
        b.BatchNo;
    """)
    passed_count_results_level2 = db.session.execute(passed_count_query_level2).fetchall()
 
    # Failed Count Query for Level 1
    failed_count_query_level1 = text("""
    SELECT
        b.BatchNo,
        COUNT(DISTINCT p.ParticipantID) AS ParticipantCount
    FROM
        Participants p
    JOIN
        TestResults tr ON p.ParticipantID = tr.ParticipantID
    JOIN
        Subjects s ON tr.SubjectID = s.SubjectID
    JOIN
        Levels l ON tr.LevelID = l.LevelID
    JOIN
        Attempts a ON tr.AttemptID = a.AttemptID
    JOIN
        Batches b ON tr.BatchID = b.BatchID
    WHERE
        l.LevelNo = 'Level1'
        AND tr.CNRating < 4.0
        AND a.AttemptNo = 'Attempt3'
    GROUP BY
        b.BatchNo
    ORDER BY
        b.BatchNo;
    """)
    failed_count_results_level1 = db.session.execute(failed_count_query_level1).fetchall()
 
    # Failed Count Query for Level 2
    failed_count_query_level2 = text("""
    SELECT
        b.BatchNo,
        COUNT(DISTINCT p.ParticipantID) AS ParticipantCount
    FROM
        Participants p
    JOIN
        TestResults tr ON p.ParticipantID = tr.ParticipantID
    JOIN
        Batches b ON tr.BatchID = b.BatchID
    JOIN
        Subjects s ON tr.SubjectID = s.SubjectID
    JOIN
        Levels l ON tr.LevelID = l.LevelID
    JOIN
        Attempts a ON tr.AttemptID = a.AttemptID
    WHERE
        l.LevelNo = 'Level2'
        AND a.AttemptNo = 'Attempt3'
        AND tr.CNRating < 4
    GROUP BY
        b.BatchNo
    ORDER BY
        b.BatchNo;
    """)
    failed_count_results_level2 = db.session.execute(failed_count_query_level2).fetchall()
 
    # In-Progress Count Query for Level 1
   
    in_progress_count_query_level1 = text("""
    SELECT
        b.BatchNo,
        l.LevelNo,
        COUNT(DISTINCT p.ParticipantID) AS InProgressCount
    FROM
        testresultsdb.testresults tr
    JOIN
        testresultsdb.participants p ON tr.ParticipantID = p.ParticipantID
    JOIN
        testresultsdb.subjects s ON tr.SubjectID = s.SubjectID
    JOIN
        testresultsdb.levels l ON tr.LevelID = l.LevelID
    JOIN
        testresultsdb.attempts a ON tr.AttemptID = a.AttemptID
    JOIN
        testresultsdb.batches b ON tr.BatchID = b.BatchID
    WHERE
        l.LevelNo = 'Level1'
        AND s.SubjectName IN ('Core Software Engineering', 'Prompt Engineering', 'Core Software Engineering Coding Skills')
        AND tr.AppearedInTest = 1
        AND p.Email NOT IN (
            -- Exclude Passed candidates
            SELECT
                p.Email
            FROM
                testresultsdb.testresults tr
            JOIN
                testresultsdb.participants p ON tr.ParticipantID = p.ParticipantID
            JOIN
                testresultsdb.subjects s ON tr.SubjectID = s.SubjectID
            JOIN
                testresultsdb.levels l ON tr.LevelID = l.LevelID
            JOIN
                testresultsdb.attempts a ON tr.AttemptID = a.AttemptID
            WHERE
                l.LevelNo = 'Level1'
                AND s.SubjectName IN ('Core Software Engineering', 'Prompt Engineering', 'Core Software Engineering Coding Skills')
                AND tr.CNRating >= 4
                AND tr.AppearedInTest = 1
            GROUP BY
                p.Email
            HAVING
                COUNT(DISTINCT s.SubjectName) = 3
        )
        AND p.Email NOT IN (
            -- Exclude Failed candidates
            SELECT
                p.Email
            FROM
                testresultsdb.testresults tr
            JOIN
                testresultsdb.participants p ON tr.ParticipantID = p.ParticipantID
            JOIN
                testresultsdb.subjects s ON tr.SubjectID = s.SubjectID
            JOIN
                testresultsdb.levels l ON tr.LevelID = l.LevelID
            JOIN
                testresultsdb.attempts a ON tr.AttemptID = a.AttemptID
            WHERE
                l.LevelNo = 'Level1'
                AND s.SubjectName IN ('Core Software Engineering', 'Prompt Engineering', 'Core Software Engineering Coding Skills')
                AND a.AttemptNo = 'Attempt3'
                AND tr.CNRating < 4
                AND tr.AppearedInTest = 1
        )
    GROUP BY
        b.BatchNo, l.LevelNo
    ORDER BY
        b.BatchNo, l.LevelNo;
""")
    in_progress_count_results_level1 = db.session.execute(in_progress_count_query_level1).fetchall()
 
    # In-Progress Count Query for Level 2
    in_progress_count_query_level2 = text("""
    SELECT
        b.BatchNo,
        COUNT(DISTINCT p.ParticipantID) AS ParticipantCount
    FROM
        Participants p
    JOIN
        TestResults tr ON p.ParticipantID = tr.ParticipantID
    JOIN
        Batches b ON tr.BatchID = b.BatchID
    JOIN
        Subjects s ON tr.SubjectID = s.SubjectID
    JOIN
        Levels l ON tr.LevelID = l.LevelID
    JOIN
        Attempts a ON tr.AttemptID = a.AttemptID
    WHERE
        l.LevelNo = 'Level2'
        AND p.ParticipantID NOT IN (
            SELECT ParticipantID
            FROM TestResults tr2
            JOIN Levels l2 ON tr2.LevelID = l2.LevelID
            JOIN Attempts a2 ON tr2.AttemptID = a2.AttemptID
            WHERE l2.LevelNo = 'Level2'
            AND (tr2.CNRating >= 4 OR (a2.AttemptNo = 'Attempt3' AND tr2.CNRating < 4))
        )
    GROUP BY
        b.BatchNo
    ORDER BY
        b.BatchNo;
    """)
    in_progress_count_results_level2 = db.session.execute(in_progress_count_query_level2).fetchall()
 
    # Combine results into a single JSON response
    response = {
        "level1": {
            "invite_count_lvl1": [dict(row._mapping) for row in invite_count_results_level1],
            "passed_count_lvl1": [dict(row._mapping) for row in passed_count_results_level1],
            "failed_count_lvl1": [dict(row._mapping) for row in failed_count_results_level1],
            "in_progress_count_lvl1": [dict(row._mapping) for row in in_progress_count_results_level1]
        },
        "level2": {
            "invite_count_lvl2": [dict(row._mapping) for row in invite_count_results_level2],
            "passed_count_lvl2": [dict(row._mapping) for row in passed_count_results_level2],
            "failed_count_lvl2": [dict(row._mapping) for row in failed_count_results_level2],
            "in_progress_count_lvl2": [dict(row._mapping) for row in in_progress_count_results_level2]
        }
    }
 
    return jsonify(response)


@app.route('/api/dashboard2', methods=['GET'])
def get_dashboard2_data():
    batch_number = request.args.get('batch_number')
    level_id = request.args.get('level_id')

    # Query to get the batch ID from the batch number
    batch_id_query = text("SELECT BatchID FROM Batches WHERE BatchNo = :batch_number")
    batch_id_result = db.session.execute(batch_id_query, {'batch_number': batch_number}).fetchone()

    if not batch_id_result:
        return jsonify({'message': 'Batch not found!'}), 404

    batch_id = batch_id_result.BatchID

    query = text("""
        SELECT
        ts.SubjectName,
        a.AttemptNo AS AttemptName,
        COUNT(DISTINCT tr.ParticipantID) AS TotalInvitations,
        SUM(CASE WHEN tr.AppearedInTest = 1 THEN 1 ELSE 0 END) AS TotalAppeared,
        SUM(CASE WHEN tr.CNRating >= 4.0 THEN 1 ELSE 0 END) AS TotalPass,
        SUM(CASE WHEN tr.CNRating < 4.0 AND tr.AppearedInTest = 1 THEN 1 ELSE 0 END) AS TotalFail,
        SUM(CASE WHEN tr.AppearedInTest = 1 AND tr.CNRating IS NULL THEN 1 ELSE 0 END) AS TotalInProgress
    FROM
        TestResults tr
    JOIN
        Subjects ts ON tr.SubjectID = ts.SubjectID
    JOIN
        Attempts a ON tr.AttemptID = a.AttemptID
    WHERE
        tr.BatchID = :batch_id
        AND tr.LevelID = :level_id
    GROUP BY
        ts.SubjectName, a.AttemptNo
    ORDER BY
        ts.SubjectName, a.AttemptNo;
    """)

    results = db.session.execute(query, {'batch_id': batch_id, 'level_id': level_id}).fetchall()

    data = []
    for row in results:
        data.append({
            'SubjectName': row.SubjectName,
            'AttemptName': row.AttemptName,
            'TotalInvitations': row.TotalInvitations,
            'TotalAppeared': row.TotalAppeared,
            'TotalPass': row.TotalPass,
            'TotalFail': row.TotalFail,
            'TotalInProgress': row.TotalInProgress
        })

    return jsonify(data), 200

@app.route('/api/candidates/pass', methods=['GET'])
def get_candidates_pass():
    batch_no = request.args.get('batch_no')
    level_no = request.args.get('level_no')
    if not batch_no or not level_no:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Fetch BatchID
    batch_query = text("SELECT BatchID FROM Batches WHERE BatchNo = :batch_no")
    batch_result = db.session.execute(batch_query, {'batch_no': batch_no}).fetchone()
    if not batch_result:
        return jsonify({'error': 'Invalid batch_no'}), 400
    batch_id = batch_result.BatchID

    # Fetch LevelID
    level_query = text("SELECT LevelID FROM Levels WHERE LevelNo = :level_no")
    level_result = db.session.execute(level_query, {'level_no': level_no}).fetchone()
    if not level_result:
        return jsonify({'error': 'Invalid level_no'}), 400
    level_id = level_result.LevelID

    # Fetch the next level ID (for Level 1 -> Level 2, Level 2 -> Level 3)
    next_level_no = ''
    if level_no == 'Level1':
        next_level_no = 'Level2'
    elif level_no == 'Level2':
        next_level_no = 'Level3'
    else:
        return jsonify({'error': 'Invalid level_no'}), 400

    # Fetch the LevelID for the next level
    next_level_query = text("SELECT LevelID FROM Levels WHERE LevelNo = :next_level_no")
    next_level_result = db.session.execute(next_level_query, {'next_level_no': next_level_no}).fetchone()

    # If next level is not present, set next_level_id to None
    next_level_id = next_level_result.LevelID if next_level_result else None

    # For Level1, passed candidates must have passed all three subjects.
    if level_no == 'Level1':
        query = text("""
            SELECT DISTINCT p.Name, p.Email, p.PrimarySkill
            FROM Participants p
            JOIN TestResults tr ON p.ParticipantID = tr.ParticipantID
            JOIN Subjects s ON tr.SubjectID = s.SubjectID
            WHERE tr.BatchID = :batch_id
              AND tr.LevelID = :level_id
              AND tr.CNRating > 4.0
              AND p.ParticipantID IN (
                    SELECT tr.ParticipantID
                    FROM TestResults tr
                    JOIN Subjects s ON tr.SubjectID = s.SubjectID
                    WHERE tr.LevelID = :level_id AND tr.CNRating > 4.0
                    GROUP BY tr.ParticipantID
                    HAVING COUNT(DISTINCT s.SubjectID) = (
                        SELECT COUNT(DISTINCT SubjectID)
                        FROM Subjects
                        WHERE SubjectName IN ('Core Software Engineering', 'Prompt Engineering', 'Core Software Engineering Coding Skills')
                    )
              )
        """)
    elif level_no == 'Level2':
        query = text("""
            SELECT DISTINCT p.Name, p.Email, p.PrimarySkill
            FROM Participants p
            JOIN TestResults tr ON p.ParticipantID = tr.ParticipantID
            WHERE tr.BatchID = :batch_id
              AND tr.LevelID = :level_id
              AND tr.CNRating >= 4.0
        """)
    else:
        return jsonify({'error': 'Invalid level_no'}), 400

    # Fetch passed candidates
    results = db.session.execute(query, {'batch_id': batch_id, 'level_id': level_id}).fetchall()

    # For each passed candidate, check if they've been invited for the next level
    candidates_data = []
    for row in results:
        name = row.Name
        email = row.Email
        primary_skill = row.PrimarySkill

        # If there is no next level (next_level_id is None), set 'Not Invited'
        if next_level_id is None:
            is_invited = 'Not Invited'
        else:
            # Check if the candidate has been invited to the next level
            invitation_query = text("""
                SELECT COUNT(*) 
                FROM TestResults tr
                WHERE tr.ParticipantID = (
                    SELECT ParticipantID 
                    FROM Participants p
                    WHERE p.Email = :email
                ) AND tr.BatchID = :batch_id AND tr.LevelID = :next_level_id
            """)
            invitation_result = db.session.execute(invitation_query, {'email': email, 'batch_id': batch_id, 'next_level_id': next_level_id}).fetchone()

            # If the count of invitations > 0, the candidate is invited to the next level
            is_invited = 'Yes' if invitation_result[0] > 0 else 'No'

        candidates_data.append({
            'Name': name,
            'Email': email,
            'PrimarySkill': primary_skill,
            'InvitedForNextLevel': is_invited
        })

    return jsonify(candidates_data), 200



@app.route('/api/candidates/invited', methods=['GET'])
def get_total_invites():
    # Get batch_no and level_no from query parameters
    batch_no = request.args.get('batch_no')
    level_no = request.args.get('level_no')

    if not batch_no or not level_no:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Fetch BatchID for the given batch_no
    batch_query = text("SELECT BatchID FROM Batches WHERE BatchNo = :batch_no")
    batch_result = db.session.execute(batch_query, {'batch_no': batch_no}).fetchone()
    if not batch_result:
        return jsonify({'error': 'Invalid batch_no'}), 400
    batch_id = batch_result.BatchID

    # Fetch LevelID for the given level_no
    level_query = text("SELECT LevelID FROM Levels WHERE LevelNo = :level_no")
    level_result = db.session.execute(level_query, {'level_no': level_no}).fetchone()
    if not level_result:
        return jsonify({'error': 'Invalid level_no'}), 400
    level_id = level_result.LevelID

    # Query to calculate the total invitations sent for the given batch and level
    query = text("""
        SELECT p.Name, p.Email, p.PrimarySkill, COUNT(tr.InviteTime) AS TotalInvites
        FROM Participants p
        JOIN TestResults tr ON p.ParticipantID = tr.ParticipantID
        WHERE tr.BatchID = :batch_id
          AND tr.LevelID = :level_id
        GROUP BY p.ParticipantID
    """)

    # Fetch the total invitations data
    results = db.session.execute(query, {'batch_id': batch_id, 'level_id': level_id}).fetchall()

    # Prepare response data with Name, Email, and Tech Stack (PrimarySkill) and total invites
    invited_candidates = []
    for row in results:
        invited_candidates.append({
            'Name': row.Name,
            'Email': row.Email,
            'TechStack': row.PrimarySkill,
            'TotalInvites': row.TotalInvites
        })

    return jsonify(invited_candidates), 200

 
@app.route('/api/candidates/fail', methods=['GET'])
def get_candidates_fail():
    batch_no = request.args.get('batch_no')
    level_no = request.args.get('level_no')
    if not batch_no or not level_no:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Fetch BatchID
    batch_query = text("SELECT BatchID FROM Batches WHERE BatchNo = :batch_no")
    batch_result = db.session.execute(batch_query, {'batch_no': batch_no}).fetchone()
    if not batch_result:
        return jsonify({'error': 'Invalid batch_no'}), 400
    batch_id = batch_result.BatchID

    # Fetch LevelID
    level_query = text("SELECT LevelID FROM Levels WHERE LevelNo = :level_no")
    level_result = db.session.execute(level_query, {'level_no': level_no}).fetchone()
    if not level_result:
        return jsonify({'error': 'Invalid level_no'}), 400
    level_id = level_result.LevelID

    # Fetch the next level ID (for Level 1 -> Level 2, Level 2 -> Level 3)
    next_level_no = ''
    if level_no == 'Level1':
        next_level_no = 'Level2'
    elif level_no == 'Level2':
        next_level_no = 'Level3'
    else:
        return jsonify({'error': 'Invalid level_no'}), 400

    # Fetch the LevelID for the next level
    next_level_query = text("SELECT LevelID FROM Levels WHERE LevelNo = :next_level_no")
    next_level_result = db.session.execute(next_level_query, {'next_level_no': next_level_no}).fetchone()

    # If next level is not present, set next_level_id to None
    next_level_id = next_level_result.LevelID if next_level_result else None

    if level_no == 'Level1':
        # --- For Level1 failed candidates, include subject-wise status and invitation details ---
        fail_candidates_query = text("""
            SELECT DISTINCT p.ParticipantID, p.Name, p.Email, p.PrimarySkill
            FROM Participants p
            JOIN TestResults tr ON p.ParticipantID = tr.ParticipantID
            JOIN Attempts a ON tr.AttemptID = a.AttemptID
            WHERE tr.BatchID = :batch_id
              AND tr.LevelID = :level_id
              AND tr.CNRating < 4.0
              AND a.AttemptNo = 'Attempt3'
        """)
        candidates_results = db.session.execute(fail_candidates_query, {'batch_id': batch_id, 'level_id': level_id}).fetchall()
        
        # Define the subjects to check (adjust names if necessary)
        subjects_list = ['Core Software Engineering', 'Prompt Engineering', 'Core Software Engineering Coding Skills']
        candidates_data = []
        
        for candidate in candidates_results:
            candidate_id = candidate.ParticipantID

            # Retrieve all test results for this candidate for the three subjects
            test_results_query = text("""
                SELECT ts.SubjectName, tr.CNRating, a.AttemptNo, tr.InviteTime, tr.AppearedInTest
                FROM TestResults tr
                JOIN Subjects ts ON tr.SubjectID = ts.SubjectID
                JOIN Attempts a ON tr.AttemptID = a.AttemptID
                WHERE tr.BatchID = :batch_id
                  AND tr.LevelID = :level_id
                  AND tr.ParticipantID = :candidate_id
                  AND ts.SubjectName IN :subjects
            """)
            test_results = db.session.execute(
                test_results_query,
                {
                    'batch_id': batch_id,
                    'level_id': level_id,
                    'candidate_id': candidate_id,
                    'subjects': tuple(subjects_list)
                }
            ).fetchall()

            # For each subject, mark as "pass" if any attempt shows CNRating >= 4.0; otherwise, "fail"
            subject_status = {subject: 'fail' for subject in subjects_list}
            for row in test_results:
                subj = row.SubjectName
                if row.CNRating is not None and row.CNRating >= 4.0:
                    subject_status[subj] = 'pass'

            # Retrieve aggregate invitation details for this candidate at the given batch/level
            agg_query = text("""
                SELECT COUNT(*) as total_invitations,
                       MAX(InviteTime) as last_invited,
                       SUM(CASE WHEN AppearedInTest = 1 THEN 1 ELSE 0 END) as total_appeared
                FROM TestResults
                WHERE BatchID = :batch_id
                  AND LevelID = :level_id
                  AND ParticipantID = :candidate_id
            """)
            agg_result = db.session.execute(agg_query, {
                'batch_id': batch_id,
                'level_id': level_id,
                'candidate_id': candidate_id
            }).fetchone()

            # Check if next level exists, and set 'Not Invited' if not
            if next_level_id is None:
                is_invited = 'Not Invited'
            else:
                # Check if the candidate has been invited to the next level
                invitation_query = text("""
                    SELECT COUNT(*) 
                    FROM TestResults tr
                    WHERE tr.ParticipantID = :candidate_id
                      AND tr.BatchID = :batch_id 
                      AND tr.LevelID = :next_level_id
                """)
                invitation_result = db.session.execute(invitation_query, {'candidate_id': candidate_id, 'batch_id': batch_id, 'next_level_id': next_level_id}).fetchone()
                is_invited = 'Yes' if invitation_result[0] > 0 else 'No'

            candidate_data = {
                'Name': candidate.Name,
                'Email': candidate.Email,
                'PrimarySkill': candidate.PrimarySkill,
                'TotalInvitations': agg_result.total_invitations,
                'LastInvited': agg_result.last_invited,
                'TotalAppeared': agg_result.total_appeared,
                'Subjects': [
                    {'SubjectName': subj, 'Status': subject_status[subj]}
                    for subj in subjects_list
                ],
                'InvitedForNextLevel': is_invited
            }
            candidates_data.append(candidate_data)
        
        return jsonify(candidates_data), 200
    
    elif level_no == 'Level2':
        # For Level 2, show subject-wise failure details
        fail_candidates_query = text("""
            SELECT DISTINCT p.ParticipantID, p.Name, p.Email, p.PrimarySkill
            FROM Participants p
            JOIN TestResults tr ON p.ParticipantID = tr.ParticipantID
            JOIN Attempts a ON tr.AttemptID = a.AttemptID
            WHERE tr.BatchID = :batch_id
              AND tr.LevelID = :level_id
              AND tr.CNRating < 4.0
              AND a.AttemptNo = 'Attempt3'
        """)
        candidates_results = db.session.execute(fail_candidates_query, {'batch_id': batch_id, 'level_id': level_id}).fetchall()

        # Define subjects to check for Level 2
        subjects_list = [ 'NodeJS  for SE/SSE','ReactJS  for SE/SSE','Angular For SE/SSE','ReactJS-Leads']
        candidates_data = []

        for candidate in candidates_results:
            candidate_id = candidate.ParticipantID

            # Retrieve all test results for this candidate for the subjects
            test_results_query = text("""
                SELECT ts.SubjectName, tr.CNRating, a.AttemptNo, tr.InviteTime, tr.AppearedInTest
                FROM TestResults tr
                JOIN Subjects ts ON tr.SubjectID = ts.SubjectID
                JOIN Attempts a ON tr.AttemptID = a.AttemptID
                WHERE tr.BatchID = :batch_id
                  AND tr.LevelID = :level_id
                  AND tr.ParticipantID = :candidate_id
                  AND ts.SubjectName IN :subjects
            """)
            test_results = db.session.execute(
                test_results_query,
                {
                    'batch_id': batch_id,
                    'level_id': level_id,
                    'candidate_id': candidate_id,
                    'subjects': tuple(subjects_list)
                }
            ).fetchall()

            # For each subject, mark as "pass" if any attempt shows CNRating >= 4.0; otherwise, "fail"
            subject_status = {subject: 'fail' for subject in subjects_list}
            for row in test_results:
                subj = row.SubjectName
                if row.CNRating is not None and row.CNRating >= 4.0:
                    subject_status[subj] = 'pass'

            # Append candidate data for level 2 with subject details
            candidate_data = {
                'Name': candidate.Name,
                'Email': candidate.Email,
                'PrimarySkill': candidate.PrimarySkill,
                'Subjects': [
                    {'SubjectName': subj, 'Status': subject_status[subj]}
                    for subj in subjects_list
                ]
            }
            candidates_data.append(candidate_data)
        
        return jsonify(candidates_data), 200

    else:
        return jsonify({'error': 'Invalid level_no'}), 400

 
@app.route('/api/candidates/in_progress', methods=['GET'])
def get_candidates_in_progress():
    batch_no = request.args.get('batch_no')
    level_no = request.args.get('level_no')
    
    if not batch_no or not level_no:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Fetch BatchID
    batch_query = text("SELECT BatchID FROM Batches WHERE BatchNo = :batch_no")
    batch_result = db.session.execute(batch_query, {'batch_no': batch_no}).fetchone()
    if not batch_result:
        return jsonify({'error': 'Invalid batch_no'}), 400
    batch_id = batch_result.BatchID

    # Fetch LevelID
    level_query = text("SELECT LevelID FROM Levels WHERE LevelNo = :level_no")
    level_result = db.session.execute(level_query, {'level_no': level_no}).fetchone()
    if not level_result:
        return jsonify({'error': 'Invalid level_no'}), 400
    level_id = level_result.LevelID

    # Fetch the next level ID (for Level 1 -> Level 2, Level 2 -> Level 3)
    next_level_no = ''
    if level_no == 'Level1':
        next_level_no = 'Level2'
    elif level_no == 'Level2':
        next_level_no = 'Level3'
    else:
        return jsonify({'error': 'Invalid level_no'}), 400

    # Fetch the LevelID for the next level
    next_level_query = text("SELECT LevelID FROM Levels WHERE LevelNo = :next_level_no")
    next_level_result = db.session.execute(next_level_query, {'next_level_no': next_level_no}).fetchone()

    # If next level is not present, set next_level_id to None
    next_level_id = next_level_result.LevelID if next_level_result else None

    # In-progress candidates: Those who have CNRating between 0 and 4.0 and have not passed the current level
    in_progress_query = text("""
        SELECT DISTINCT p.ParticipantID, p.Name, p.Email, p.PrimarySkill
        FROM Participants p
        JOIN TestResults tr ON p.ParticipantID = tr.ParticipantID
        WHERE tr.BatchID = :batch_id
          AND tr.LevelID = :level_id
          AND tr.CNRating >= 0
          AND tr.CNRating < 4.0
          AND tr.ParticipantID NOT IN (
              SELECT ParticipantID 
              FROM TestResults 
              WHERE BatchID = :batch_id 
                AND LevelID = :level_id 
                AND CNRating >= 4.0
          )
    """)

    candidates_results = db.session.execute(in_progress_query, {'batch_id': batch_id, 'level_id': level_id}).fetchall()
    
    candidates_data = []
    
    for candidate in candidates_results:
        candidate_id = candidate.ParticipantID

        # Check if the candidate has been invited for the next level (if it exists)
        if next_level_id is None:
            is_invited = 'Not Invited'
        else:
            invitation_query = text("""
                SELECT COUNT(*) 
                FROM TestResults tr
                WHERE tr.ParticipantID = :candidate_id
                  AND tr.BatchID = :batch_id 
                  AND tr.LevelID = :next_level_id
            """)
            invitation_result = db.session.execute(invitation_query, {'candidate_id': candidate_id, 'batch_id': batch_id, 'next_level_id': next_level_id}).fetchone()
            is_invited = 'Yes' if invitation_result[0] > 0 else 'No'

        # Append candidate data with in-progress status and invitation details
        candidate_data = {
            'Name': candidate.Name,
            'Email': candidate.Email,
            'PrimarySkill': candidate.PrimarySkill,
            'InvitedForNextLevel': is_invited
        }
        candidates_data.append(candidate_data)

    # Return the count and the list of in-progress candidates
    return jsonify({
        'InProgressCount': len(candidates_data),
        'InProgressCandidates': candidates_data
    }), 200



@app.route('/api/participant-details', methods=['GET'])
def get_participant_details():
    batch_no = request.args.get('batch_id')
    level_id = request.args.get('level_id')
    subject_name = request.args.get('subject_name')
    attempt_no = request.args.get('attempt_id')
    status = request.args.get('status')

    if not batch_no or not level_id or not subject_name or not attempt_no or not status:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Fetch BatchID from Batches table
    batch_query = text("SELECT BatchID FROM Batches WHERE BatchNo = :batch_no")
    batch_result = db.session.execute(batch_query, {'batch_no': batch_no}).fetchone()
    if not batch_result:
        return jsonify({'error': 'Invalid batch_id'}), 400
    batch_id = batch_result.BatchID

    # Fetch AttemptID from Attempts table
    attempt_query = text("SELECT AttemptID FROM Attempts WHERE AttemptNo = :attempt_no")
    attempt_result = db.session.execute(attempt_query, {'attempt_no': attempt_no}).fetchone()
    if not attempt_result:
        return jsonify({'error': 'Invalid attempt_id'}), 400
    attempt_id = attempt_result.AttemptID

    status_condition = ""
    if status == 'pass':
        status_condition = "tr.CNRating >= 4.0"
    elif status == 'fail':
        status_condition = "tr.CNRating < 4.0 AND tr.AppearedInTest = 1"
    elif status == 'invited':
        status_condition = "1=1"  # All invited participants
    elif status == 'total_appeared':
        status_condition = "tr.AppearedInTest = 1"

    query = text(f"""
    SELECT
        p.Name,
        p.Email
    FROM
        TestResults tr
    JOIN
        Participants p ON tr.ParticipantID = p.ParticipantID
    JOIN
        Subjects ts ON tr.SubjectID = ts.SubjectID
    WHERE
        tr.BatchID = :batch_id
        AND tr.LevelID = :level_id
        AND ts.SubjectName = :subject_name
        AND tr.AttemptID = :attempt_id
        AND {status_condition}
    """)

    results = db.session.execute(query, {
        'batch_id': batch_id,
        'level_id': level_id,
        'subject_name': subject_name,
        'attempt_id': attempt_id
    }).fetchall()

    data = [{'Name': row.Name, 'Email': row.Email} for row in results]

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
    if not email:
        return jsonify({'error': 'Missing required parameters'}), 400

    participant = db.session.execute(text("SELECT * FROM Participants WHERE Email = :email"), {'email': email}).fetchone()

    if not participant:
        return jsonify({'message': 'User not found!'}), 404

    # Initialize a dictionary to store the test details by levels
    level_details = {}

    # Function to process data for each level
    def get_level_details(level):
        query = text("""
        SELECT 
            p.Name AS ParticipantName,
            p.Email,
            s.SubjectName,
            b.BatchNo,
            COUNT(tr.TestResultID) AS TotalInvites,
            MAX(tr.InviteTime) AS LastInviteDate,
            MIN(tr.InviteTime) AS FirstInviteDate
        FROM 
            Participants p
        JOIN 
            TestResults tr ON p.ParticipantID = tr.ParticipantID
        JOIN 
            Subjects s ON tr.SubjectID = s.SubjectID
        JOIN 
            Levels l ON tr.LevelID = l.LevelID
        JOIN 
            Batches b ON tr.BatchID = b.BatchID
        WHERE 
            p.Email = :email AND l.LevelNo = :level
        GROUP BY 
            p.Name, p.Email, s.SubjectName, b.BatchNo
        ORDER BY 
            LastInviteDate DESC
        """)

        level_results = db.session.execute(query, {'email': email, 'level': level}).fetchall()

        level_test_details = []

        for row in level_results:
            detail = {
                'ParticipantName': row.ParticipantName,
                'Email': row.Email,
                'SubjectName': row.SubjectName,
                'BatchNo': row.BatchNo,
                'TotalInvites': row.TotalInvites,
                'LastInvited': row.LastInviteDate,
                'StartDate': row.FirstInviteDate,
            }

            # Check pass/fail conditions for the current level
            passed_query = text("""
            SELECT COUNT(*) 
            FROM TestResults tr 
            WHERE tr.ParticipantID = :participant_id AND tr.LevelID = (SELECT LevelID FROM Levels WHERE LevelNo = :level) AND tr.CNRating >= 4
            """)

            passed = db.session.execute(passed_query, {'participant_id': participant.ParticipantID, 'level': level}).scalar()

            if passed:
                detail['TestStatus'] = 'Passed'
                detail['InviteForNextLevel'] = 'No'
                detail['InviteDate'] = None
            else:
                detail['TestStatus'] = 'Failed'

                # Check if the participant is invited for the next level
                next_level_query = text("""
                SELECT 
                    MIN(tr2.InviteTime) AS NextLevelInviteDate
                FROM 
                    TestResults tr2 
                JOIN 
                    Levels l ON tr2.LevelID = l.LevelID
                WHERE 
                    tr2.ParticipantID = :participant_id AND l.LevelNo = :next_level
                """)

                next_level = {
                    'Level1': 'Level2',
                    'Level2': 'Level3',
                    'Level3': 'Level4',
                    'Level4': 'Level5'
                }

                next_level_results = db.session.execute(next_level_query, {'participant_id': participant.ParticipantID, 'next_level': next_level.get(level)}).fetchone()

                if next_level_results and next_level_results.NextLevelInviteDate:
                    detail['InviteForNextLevel'] = 'Yes'
                    detail['InviteDate'] = next_level_results.NextLevelInviteDate
                else:
                    detail['InviteForNextLevel'] = 'No'
                    detail['InviteDate'] = None

            level_test_details.append(detail)
        return level_test_details

    # Get the details for each level from Level 1 to Level 5
    level_details['Level1'] = get_level_details('Level1')
    level_details['Level2'] = get_level_details('Level2')
    
    # You can add more levels here in a similar way

    # Determine overall test status (Passed only if any subject passed)
    overall_status = 'Failed'

    # Iterate over levels and check if the status is passed for any subject
    for level in level_details.values():
        for detail in level:
            if detail['TestStatus'] == 'Passed':
                overall_status = 'Passed'
                break  # No need to check further if we found a "Passed" status

    # Check if Level 2 data is present to set InviteForNextLevel to "Yes"
    if 'Level2' in level_details and level_details['Level2']:
        for detail in level_details['Level1']:
            detail['InviteForNextLevel'] = 'Yes'

    return jsonify({
        'participant': participant.Name,
        'test_status': overall_status,
        'details': level_details
    }), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)
