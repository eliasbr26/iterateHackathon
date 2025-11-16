#!/usr/bin/env python3
"""
Create a demo interview for testing purposes
"""
import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('quantcoach_interviews.db')
cursor = conn.cursor()

try:
    # Check if interview 1 exists
    cursor.execute("SELECT id FROM interviews WHERE id = 1")
    existing = cursor.fetchone()

    if existing:
        print(f"✅ Interview 1 already exists")

        # Check status
        cursor.execute("SELECT status FROM interviews WHERE id = 1")
        status = cursor.fetchone()[0]
        print(f"   Status: {status}")

    else:
        print("Creating demo data...")

        # Create demo candidate
        cursor.execute("""
            INSERT INTO candidates (name, email, phone, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, ('Jane Smith', 'jane.smith@example.com', '+1-555-0123',
              datetime.now(), datetime.now()))
        candidate_id = cursor.lastrowid
        print(f"✅ Created candidate: Jane Smith (ID: {candidate_id})")

        # Create demo interviewer
        cursor.execute("""
            INSERT INTO interviewers (name, email, total_interviews_conducted, tends_harsh, tends_lenient, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('John Doe', 'john.doe@company.com', 0, 0, 0, datetime.now(), datetime.now()))
        interviewer_id = cursor.lastrowid
        print(f"✅ Created interviewer: John Doe (ID: {interviewer_id})")

        # Create demo interview
        cursor.execute("""
            INSERT INTO interviews
            (room_name, candidate_id, interviewer_id, job_title, scheduled_start,
             actual_start, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('interview-1', candidate_id, interviewer_id, 'Senior Software Engineer',
              datetime.now(), datetime.now(), 'in_progress',
              datetime.now(), datetime.now()))
        interview_id = cursor.lastrowid
        print(f"✅ Created interview: ID {interview_id}")

        conn.commit()
        print(f"\n✅ Demo interview created successfully! Interview ID: {interview_id}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    conn.close()
