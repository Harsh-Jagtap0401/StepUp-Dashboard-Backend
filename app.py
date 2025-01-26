from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import pandas as pd
from sqlalchemy import text
from datetime import datetime
 
app = Flask(__name__)
CORS(app)  # Enable CORS
 
# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Test_12345678@localhost/TestResultsDB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
# Create the SQLAlchemy db instance
db = SQLAlchemy(app)
 
# Function to extract details from the test name
def extract_details(test_name):
    # Define possible batches, levels, and subjects
    batches = ["Batch1", "Batch2", "Batch3", "Batch4", "Batch5"]
    levels = ["Level1", "Level2", "Level3", "Level4", "Level5"]
    subjects = [
        "Prompt Engineering",
        "Core Software Engineering Coding Skills",
        "Core Software Engineering",
        "NodeJS for SE/SSE",
        "ReactJS for SE/SSE",
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
        print(f"Processing row: {row['Name']}, {row['Email']}, {row['Test name']}, {row['Invites Time']}, {row['Test Status']}, {row['Submitted Date']}, {row['CN rating']}")
 
        name = row['Name']
        email = row['Email']
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
            insert_participant = text(f"INSERT INTO Participants (Name, Email) VALUES ('{name}', '{email}')")
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
    batch_id = request.args.get('batch_id')
    level_id = request.args.get('level_id')
 
    query = text("""
    SELECT
        ts.SubjectName,
        tr.AttemptID,
        COUNT(DISTINCT tr.ParticipantID) AS TotalInvitations,
        SUM(CASE WHEN tr.AppearedInTest = 1 THEN 1 ELSE 0 END) AS TotalAppeared,
        SUM(CASE WHEN tr.CNRating >= 4.0 THEN 1 ELSE 0 END) AS TotalPass,
        SUM(CASE WHEN tr.CNRating < 4.0 AND tr.AppearedInTest = 1 THEN 1 ELSE 0 END) AS TotalFail,
        SUM(CASE WHEN tr.AppearedInTest = 1 AND tr.CNRating IS NULL THEN 1 ELSE 0 END) AS TotalInProgress
    FROM
        TestResults tr
    JOIN
        Subjects ts ON tr.SubjectID = ts.SubjectID
    WHERE
        tr.BatchID = :batch_id
        AND tr.LevelID = :level_id
    GROUP BY
        ts.SubjectName, tr.AttemptID
    ORDER BY
        ts.SubjectName, tr.AttemptID;
    """)
 
    results = db.session.execute(query, {'batch_id': batch_id, 'level_id': level_id}).fetchall()
 
    data = []
    for row in results:
        data.append({
            'SubjectName': row.SubjectName,
            'AttemptID': row.AttemptID,
            'TotalInvitations': row.TotalInvitations,
            'TotalAppeared': row.TotalAppeared,
            'TotalPass': row.TotalPass,
            'TotalFail': row.TotalFail,
            'TotalInProgress': row.TotalInProgress
        })
 
    return jsonify(data), 200
 
 
@app.route('/api/participant-details', methods=['GET'])
def get_participant_details():
    batch_id = request.args.get('batch_id')
    level_id = request.args.get('level_id')
    subject_name = request.args.get('subject_name')
    attempt_id = request.args.get('attempt_id')
    status = request.args.get('status')

    if not batch_id or not level_id or not subject_name or not attempt_id or not status:
        return jsonify({'error': 'Missing required parameters'}), 400

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)