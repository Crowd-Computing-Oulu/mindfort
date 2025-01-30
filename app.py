import random
from flask import Flask, render_template, jsonify, send_file, request, send_from_directory, session, redirect, url_for, flash
import uuid
import pandas as pd
import time
import threading
import logging
import os 
import zipfile
from io import BytesIO
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from lessons import get_lesson_by_id, lessons, get_lesson_by_id_with_ordering
from chatgpt import process_message
from datetime import datetime

app = Flask(__name__)
app.logger.setLevel(logging.ERROR)
app.secret_key = 'mindfort2024'

DATABASE = 'database.db'
VERSION = "v25.01.17 BETA"

def init_db():
    def table_exists(conn, table_name):
        """Check if a table exists in the database."""
        cur = conn.cursor()
        cur.execute("""
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' AND name=?
        """, (table_name,))
        return cur.fetchone() is not None

    # Connect to the database
    with sqlite3.connect(DATABASE) as conn:
        print("Checking database...")

        # Ensure messages table exists
        if not table_exists(conn, "messages"):
            print("Creating 'messages' table...")
            conn.execute("""
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sent_by_user BOOLEAN,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                content TEXT NOT NULL,
                conversation INTEGER NOT NULL
            )
            """)

        # Ensure users table exists
        if not table_exists(conn, "users"):
            print("Creating 'users' table...")
            conn.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level INTEGER NOT NULL,
                lesson_state INTEGER NOT NULL CHECK(lesson_state IN (0, 1, 2, 3, 4)),
                first_name TEXT,
                last_name TEXT,
                username TEXT UNIQUE NOT NULL,
                age INTEGER,
                gender TEXT,
                country TEXT,
                lesson_cases TEXT NOT NULL,
                signup_datetime DATETIME NOT NULL,
                ip TEXT NOT NULL,
                lessons_order TEXT NOT NULL,
                email TEXT UNIQUE,
                password TEXT NOT NULL
            )
            """)
        
        # Ensure feedback table exists
        if not table_exists(conn, "feedback"):
            print("Creating 'feedback' table...")
            conn.execute("""
            CREATE TABLE feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(message_id) REFERENCES messages(id)
            )
            """)
            
        # Ensure stage_finished table exists
        if not table_exists(conn, "stage_finished"):
            print("Creating 'stage_finished' table...")
            conn.execute("""
            CREATE TABLE stage_finished (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL,
                stage_finished INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
        # Ensure likert_pre table exists
        if not table_exists(conn, "likert_pre"):
            print("Creating 'likert_pre' table...")
            conn.execute("""
            CREATE TABLE likert_pre (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lesson_id INTEGER NOT NULL,
                value INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """)
            
         # Ensure likert_mid table exists
        if not table_exists(conn, "likert_mid"):
            print("Creating 'likert_mid' table...")
            conn.execute("""
            CREATE TABLE likert_mid (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lesson_id INTEGER NOT NULL,
                value INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """)
            
         # Ensure likert_post table exists
        if not table_exists(conn, "likert_post"):
            print("Creating 'likert_post' table...")
            conn.execute("""
            CREATE TABLE likert_post (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lesson_id INTEGER NOT NULL,
                value INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """)
            
        # Ensure argument_essays table exists
        if not table_exists(conn, "argument_essays"):
            print("Creating 'argument_essays' table...")
            conn.execute("""
            CREATE TABLE argument_essays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lesson_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """)

        conn.commit()
        print("Database is up-to-date.")

# Call the function to ensure database is initialized
init_db()


# Utility Function: Get Database Connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    lessons_ordered_for_user = {}
    
    
    if session.get('user.lessons_order'):
        for i in range (0, len(lessons)):
            lessons_ordered_for_user[i] = get_lesson_by_id_with_ordering(i, session['user.lessons_order'])
    
    return render_template('index.html', 
        lessons = lessons_ordered_for_user,
        session_id = get_session_id(),
        version = VERSION,
        current_path=request.path)
    
@app.route('/admin')
def admin():
    if session.get('user.email'):
        if session.get('user.email') in ['daniel.szabo@oulu.fi']:
            return render_template('admin.html', 
                users = get_users_from_db(),
                session_id = get_session_id(),
                version = VERSION,
                current_path=request.path)
    
    return redirect(url_for('index'))
        

@app.route('/prolific_login', methods=['GET'])
def prolific_login():
    username = request.args.get('PROLIFIC_PID')
    
    # try logging in first
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user:
        session['user.id'] = user['id']
        session['user.username'] = user['username']
        session['user.email'] =  user['email']
        session['user.first_name'] =  user['first_name']
        session['user.last_name'] = user['last_name']
        session['user.level'] = user['level']
        session['user.lesson_state'] = user['lesson_state']
        session['user.lessons_order'] = user['lessons_order']
        session['user.lesson_cases'] = user['lesson_cases'].split(',')
        session['user.age'] = user['age']
        session['user.gender'] = user['gender']
        session['user.country'] = user['country']
        flash('Signed in successfully!', 'success')
        return redirect(url_for('index'))
    else:
           
        first_name = "Participant " + username

        # Get signup datetime and IP
        signup_datetime = datetime.utcnow()
        user_ip = request.remote_addr

        # Generate lesson order
        lessons = list(range(12))  # Lessons ID 0 to 11
        random.shuffle(lessons)  # Shuffle lessons
        # Convert lesson order to string for storage
        lesson_order_str = ','.join(map(str, lessons))

        # Generate lesson cases
        lesson_cases = [random.randint(0, 3) for _ in range(12)]
        lesson_cases_str = ','.join(map(str, lesson_cases))

        try:
            conn = get_db_connection()
            conn.execute("""
                INSERT INTO users (first_name, last_name, username, age, gender, country, email, password, level, lesson_state, signup_datetime, ip, lessons_order, lesson_cases)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                         (first_name, '', username, '', '', '', username, '', 0, 0, signup_datetime, user_ip, lesson_order_str, lesson_cases_str))
            conn.commit()
            conn.close()
            
            flash('Account created successfully!', 'success')

            # Sign user in automatically
            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            conn.close()

            if user:
                session['user.id'] = user['id']
                session['user.username'] = user['username']
                session['user.email'] =  user['email']
                session['user.first_name'] =  user['first_name']
                session['user.last_name'] = user['last_name']
                session['user.level'] = user['level']
                session['user.lesson_state'] = user['lesson_state']
                session['user.lessons_order'] = user['lessons_order']
                session['user.lesson_cases'] = user['lesson_cases'].split(',')
                session['user.age'] = user['age']
                session['user.gender'] = user['gender']
                session['user.country'] = user['country']
                return redirect(url_for('index'))
            else:
                return redirect(url_for('signin'))
        
        except sqlite3.IntegrityError as e :
            flash(f'Username or email is already registered. ({e})', 'danger')
            return render_template('signup.html',
                                   session_id=get_session_id(),
                                   version=VERSION,
                                   current_path=request.path)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form.get('signup-firstname', '')
        last_name = request.form.get('signup-lastname', '')
        username = request.form['signup-username']  # Mandatory
        age = request.form.get('signup-age', '')
        gender = request.form.get('signup-gender', '')
        country = request.form.get('signup-country', '')
        email = request.form.get('signup-email', '')
        password = request.form['signup-password']
        confirm_password = request.form['signup-password-confirm']
        terms = request.form.get('terms')

        if not terms:
            flash('You must accept the terms and conditions.', 'danger')
            return redirect(url_for('signup'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Get signup datetime and IP
        signup_datetime = datetime.utcnow()
        user_ip = request.remote_addr

        # Generate lesson order
        lessons = list(range(12))  # Lessons ID 0 to 11
        random.shuffle(lessons)  # Shuffle lessons
        # Convert lesson order to string for storage
        lesson_order_str = ','.join(map(str, lessons))

        # Generate lesson cases
        lesson_cases = [random.randint(0, 3) for _ in range(12)]
        lesson_cases_str = ','.join(map(str, lesson_cases))

        try:
            conn = get_db_connection()
            conn.execute("""
                INSERT INTO users (first_name, last_name, username, age, gender, country, email, password, level, lesson_state, signup_datetime, ip, lessons_order, lesson_cases)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                         (first_name, last_name, username, age, gender, country, email, hashed_password, 0, 0, signup_datetime, user_ip, lesson_order_str, lesson_cases_str))
            conn.commit()
            conn.close()
            
            flash('Account created successfully!', 'success')

            # Sign user in automatically
            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            conn.close()

            if user and check_password_hash(user['password'], password):
                session['user.id'] = user['id']
                session['user.username'] = user['username']
                session['user.email'] =  user['email']
                session['user.first_name'] =  user['first_name']
                session['user.last_name'] = user['last_name']
                session['user.level'] = user['level']
                session['user.lesson_state'] = user['lesson_state']
                session['user.lessons_order'] = user['lessons_order']
                session['user.lesson_cases'] = user['lesson_cases'].split(',')
                session['user.age'] = user['age']
                session['user.gender'] = user['gender']
                session['user.country'] = user['country']
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'danger')
                return redirect(url_for('signin'))
        
        except sqlite3.IntegrityError:
            flash('Username or email is already registered.', 'danger')
            return render_template('signup.html',
                                   session_id=get_session_id(),
                                   version=VERSION,
                                   current_path=request.path)
    
    return render_template('signup.html',
                           session_id=get_session_id(),
                           version=VERSION,
                           current_path=request.path)
    
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['signin-email']
        password = request.form['signin-password']

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ? OR username = ?", (email,email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user.id'] = user['id']
            session['user.username'] = user['username']
            session['user.email'] =  user['email']
            session['user.first_name'] =  user['first_name']
            session['user.last_name'] = user['last_name']
            session['user.level'] = user['level']
            session['user.lesson_state'] = user['lesson_state']
            session['user.lessons_order'] = user['lessons_order']
            session['user.lesson_cases'] = user['lesson_cases'].split(',')
            session['user.age'] = user['age']
            session['user.gender'] = user['gender']
            session['user.country'] = user['country']
            flash('Signed in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('signin.html',
                           session_id = get_session_id(),
      version = VERSION,
      current_path=request.path)


@app.route('/lesson', methods=['GET'])
def lesson():
    try:
        id = int(request.args.get("id"))  # Use 'id' as lesson_id
        user_id = session.get('user.id') 
        # Fetch messages for the conversation
        messages = get_messages_from_db(user_id,id)
        return render_template(
            'lesson.html',
            lesson=get_lesson_by_id_with_ordering(id, session['user.lessons_order']),
            session_id=get_session_id(),
            lesson_state=session['user.lesson_state'],
            version=VERSION,
            current_path=request.path,
            messages=messages
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/likert/<string:version>/<int:lesson_id>', methods=['POST'])
def likert(version,lesson_id):
    if 'user.id' not in session:
        flash("You must be logged in to submit this form.", 'danger')
        return redirect(url_for('signin'))

    value = request.form['likert_scale']
    user_id = session['user.id']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Store the likert scale response in the database
    conn = get_db_connection()
    conn.execute(f"""
        INSERT INTO likert_{version} (user_id, lesson_id, value, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, lesson_id, value, timestamp))
    conn.commit()
    conn.close()
    
    try:
        conn = get_db_connection()
        with conn:
            # get current stage
            stage_finished = conn.execute(
                "SELECT lesson_state FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()["lesson_state"]
            # log time
            conn.execute("INSERT INTO stage_finished (lesson_id, stage_finished) VALUES (?, ?)", (lesson_id, stage_finished))
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
    finally:
        conn.close()
    
    if(session['user.lesson_state'] == 4):
              
        try:
            conn = get_db_connection()
            with conn:
               
                # Increment the user's lesson_state in the database
                conn.execute(
                    "UPDATE users SET lesson_state = 0 WHERE id = ?",
                    (user_id,)
                )
                # Update the session to reflect the new lesson_state
                user_level = conn.execute(
                    "SELECT lesson_state FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()
                session['user.lesson_state'] = user_level[0] if user_level else session.get('lesson_state', 0)
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')
        finally:
            conn.close()

        try:
            conn = get_db_connection()
            with conn:
                # Increment the user's level in the database
                conn.execute(
                    "UPDATE users SET level = level + 1 WHERE id = ?",
                    (user_id,)
                )
                # Update the session to reflect the new level
                user_level = conn.execute(
                    "SELECT level FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()
                session['user.level'] = user_level[0] if user_level else session.get('level', 0)

            
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')
        finally:
            conn.close()

        flash('Lesson finished, level UP', 'success')
        return redirect(url_for('index'))
    else:
        try:
            conn = get_db_connection()
            with conn:
                # Increment the user's lesson_state in the database
                conn.execute(
                    "UPDATE users SET lesson_state = lesson_state + 1 WHERE id = ?",
                    (user_id,)
                )
                # Update the session to reflect the new lesson_state
                user_level = conn.execute(
                    "SELECT lesson_state FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()
                session['user.lesson_state'] = user_level[0] if user_level else session.get('lesson_state', 0)
            session['user.lesson_state'] == 4
            flash('Stage finished. On to the next lesson stage.', 'success')
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')
        finally:
            conn.close()

    return redirect(f'/lesson?id={lesson_id}')


def get_messages_from_db(user_id, lesson_id):
    
    weakargument_base = "You are Forty, a proactive educational chat partner within the MindFort system. MindFort uses cognitive inoculation theory to help users recognize and counter misinformation, which means that you try to weakly (but proactively) argue against a positive attitude that the user holds, so that they can form complete opinions, knowledge and defence against such attacks. You don't show any sign of doubt about your (incorrect) opinion until the user starts presenting facts they looked up or logical arguments. Your job is to be a person that says incorrect things that the user has to disprove and correct using logic and facts. You speak proactively about the subject of this discussion and keep your messages in a short format suitable for a real time chat. When the user starts talking to you, you can say hi back and immediately get started with the discussion, and when the user tries to talk about something else, nudge them back to this topic. Refuse to talk about off-topic things. For this discussion, argue that "
    
    messages = []
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Fetch messages from the database for the given lesson_id
        cursor.execute("""
            SELECT id, sent_by_user, content
            FROM messages
            WHERE conversation = ? AND user_id = ?
            ORDER BY created_at ASC
        """, (lesson_id, user_id))
        
        rows = cursor.fetchall()

        # Format messages for `process_message`
        for row in rows:
            role = "user" if row[1] else "assistant"
            messages.append({
                "id": row[0],
                "role": role,
                "content": row[2]
            })

    messages.insert(0, {
        "role": "system",
        "content": weakargument_base + get_lesson_by_id_with_ordering(lesson_id, session['user.lessons_order'])['llmprompt']
    })

    return messages

def get_users_from_db():
    
    
    users = []
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM users
        """, ())
        
        rows = cursor.fetchall()

        for row in rows:
            users.append({
                "id": row[0],
                "level": row[1],
                "lesson_state": row[2],
                "first_name": row[3],
                "last_name": row[4],
                "username": row[5],
                "age": row[6],
                "gender": row[7],
                "country": row[8],
                "lesson_cases": row[9],
                "signup_datetime": row[10],
                "ip": row[11],
                "lessons_order": row[12],
                "email": row[13],
            })
            
    return users

def get_message_from_db_by_id(id):
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, sent_by_user, content, conversation
            FROM messages
            WHERE id = ?
            ORDER BY created_at ASC
        """, (id,))
        
        rows = cursor.fetchall()

        # Format messages for `process_message`
        for row in rows:
            role = "user" if row[1] else "assistant"
            return {
                "id": row[0],
                "role": role,
                "lesson_id": row[3],
                "content": row[2]
            }            


@app.route('/finish_conv')
def finish_conv():
    # Retrieve the conversation ID and user ID
    lesson_id =  int(request.args.get("id"))
    user_id = session.get('user.id')  # Assuming the user ID is stored in the session under 'user_id'

    if not user_id:
        flash('User not logged in.', 'error')
        return redirect(url_for('signin'))  # Redirect to login if user is not logged in

    try:
        conn = get_db_connection()
        with conn:
            
             # get current stage
            stage_finished = conn.execute(
                "SELECT lesson_state FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()["lesson_state"]
            
            # log time
            conn.execute("INSERT INTO stage_finished (lesson_id, stage_finished) VALUES (?, ?)", (lesson_id, stage_finished))
            
            # Increment the user's lesson_state in the database
            conn.execute(
                "UPDATE users SET lesson_state = lesson_state + 1 WHERE id = ?",
                (user_id,)
            )
            
            
            
            # Update the session to reflect the new lesson_state
            user_level = conn.execute(
                "SELECT lesson_state FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            session['user.lesson_state'] = user_level[0] if user_level else session.get('lesson_state', 0)

        flash('Stage finished. On to the next lesson stage.', 'success')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
    finally:
        conn.close()

    return redirect(f'lesson?id={lesson_id}')

@app.route('/finish_stage', methods=['GET', 'POST'])
def finish_stage():
    # Retrieve the conversation ID and user ID
    lesson_id = int(request.form.get('id'))
    user_id = session.get('user.id')  # Assuming the user ID is stored in the session under 'user_id'

    if not user_id:
        flash('User not logged in.', 'error')
        return redirect(url_for('signin'))  # Redirect to login if user is not logged in

    try:
        conn = get_db_connection()
        with conn:
            
             # get current stage
            stage_finished = conn.execute(
                "SELECT lesson_state FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()["lesson_state"]
            
            print(stage_finished)
            
            # log time
            conn.execute("INSERT INTO stage_finished (lesson_id, stage_finished) VALUES (?, ?)", (lesson_id, stage_finished))
            
            # Increment the user's lesson_state in the database
            conn.execute(
                "UPDATE users SET lesson_state = lesson_state + 1 WHERE id = ?",
                (user_id,)
            )

            # Update the session to reflect the new lesson_state
            user_level = conn.execute(
                "SELECT lesson_state FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            session['user.lesson_state'] = user_level[0] if user_level else session.get('lesson_state', 0)
     
        flash('Stage finished. On to the next lesson stage.', 'success')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
    finally:
        conn.close()

    return redirect(f'lesson?id={lesson_id}')

@app.route('/profile')
def profile():
    return render_template('profile.html',
        session_id = get_session_id(),
        version = VERSION,
        current_path=request.path)

@app.route('/signout')
def signout():
    session.clear()
    flash('You have been signed out.', 'success')
    return redirect(url_for('signin'))

@app.route('/terms')
def terms():
    return render_template('terms.html',
        session_id = get_session_id(),
        version = VERSION,
        current_path=request.path)
    
@app.route('/privacy')
def privacy():
    return render_template('privacy.html',
        session_id = get_session_id(),
        version = VERSION,
        current_path=request.path)
    
@app.route('/about')
def about():
    return render_template('about.html',
        session_id = get_session_id(),
        version = VERSION,
        current_path=request.path)
    
# Feedback Submission Endpoint
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        # Handle form submission
        message_id = int(request.form.get('message-id'))
        feedback_content = request.form.get('feedback-content')

        if not message_id or not feedback_content:
            flash("All fields are required.", "error")
            return redirect(url_for('feedback', id=message_id))

        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO feedback (message_id, content) VALUES (?, ?)", (message_id, feedback_content))
            conn.commit()
            
        flash("Feedback submitted successfully.", "success")
        message = get_message_from_db_by_id(message_id)
        return redirect(url_for('lesson', id=message['lesson_id']))

    # Render feedback form
    message_id = int(request.args.get('id'))
    message = get_message_from_db_by_id(message_id)

    if not message:
        flash("Message not found.", "error")
        return redirect(url_for('index'))  # Redirect to a suitable page if message is invalid

    return render_template(
        'feedback.html',
        session_id=get_session_id(),
        message=message,
        version=VERSION,
        current_path=request.path
    )


@app.route('/dataprocessing')
def dataprocessing():
    return render_template('dataprocessing.html',
        session_id = get_session_id(),
        version = VERSION,
        current_path=request.path)
        
@app.route('/delete_account')
def delete_user_account():
    try:
        user_id = session.get('user.id')
        if not user_id:
            flash('No user is currently logged in.', 'danger')
            return redirect(url_for('signin'))
        
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete related data from the messages table
        cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        
        # Delete related data from the feedback table based on message_id
        cursor.execute("""
            DELETE FROM feedback
            WHERE message_id IN (
                SELECT id FROM messages WHERE user_id = ?
            )
        """, (user_id,))

        # Delete related data from the likert tables
        cursor.execute("DELETE FROM likert_pre WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM likert_mid WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM likert_post WHERE user_id = ?", (user_id,))

        # Finally, delete the user from the users table
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

        conn.commit()
        conn.close()
        
        session.pop('user.id', None)  # Clear the session for logout
        flash('Account and related data deleted successfully.', 'success')
        session.clear()
         
        return redirect(url_for('index'))  # Redirect to home or any other page
        
    except Exception as e:
        # Log the exception if necessary
        flash('An error occurred while trying to delete the account.', 'danger')
        return redirect(url_for('profile'))  # Redirect back to profile or any other page
    


@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    user_message = data.get('content')
    conv_id = int(data.get('conv_id'))
    user_id = session.get('user.id') 

    if not user_message :
        return jsonify(success=False, error="Invalid input data: Missing User Message"), 400
    
    if not user_id:
        return jsonify(success=False, error="Invalid input data: Missing User ID"), 400
    
    if not data.get('conv_id'):
        return jsonify(success=False, error="Invalid input data: Missing Conversation ID"), 400

    messages = get_messages_from_db(user_id, conv_id)
        
    messages.append({"role": "user", "content": user_message})
    
    bot_reply = process_message(messages)[len(process_message(messages))-1]['content']

    # Log the messages in the database
    try:
        conn = sqlite3.connect('database.db')  # Replace with your database path
        cursor = conn.cursor()

        # Add user's message to the messages table
        cursor.execute(
            """
            INSERT INTO messages (user_id, sent_by_user, content, conversation, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, True, user_message, conv_id, datetime.now())
        )

        # Add assistant's reply to the messages table
        cursor.execute(
            """
            INSERT INTO messages (user_id, sent_by_user, content, conversation, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, False, bot_reply, conv_id, datetime.now())
        )

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify(success=False, error="Database error"), 500

    # Return both the user's message and the bot's reply
    return jsonify(success=True, user_message=user_message, bot_reply=bot_reply)

@app.route('/submit_essay', methods=['POST'])
def submit_essay():
    user_id = session.get('user.id') 
    lesson_id = int(request.args.get('id'))
    content = request.form.get('content')

    if not content or len(content) < 200:
        return jsonify({"error": "Essay content is required and must be at least 250 characters long."}), 400

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO argument_essays (user_id, lesson_id, content) VALUES (?, ?, ?)",
        (user_id, lesson_id, content)
    )
    conn.commit()
    conn.close()
    
    try:
        conn = get_db_connection()
        with conn:
            # Increment the user's lesson_state in the database
            conn.execute(
                "UPDATE users SET lesson_state = lesson_state + 1 WHERE id = ?",
                (user_id,)
            )
            # Update the session to reflect the new lesson_state
            user_level = conn.execute(
                "SELECT lesson_state FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            session['user.lesson_state'] = user_level[0] if user_level else session.get('lesson_state', 0)

        flash('Stage finished. On to the next lesson stage.', 'success')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
    finally:
        conn.close()

    return redirect(f"/lesson?id={lesson_id}") 

@app.route("/erase_conv")
def erase_conv():
    lesson_id = request.args.get("id")
    if not lesson_id:
        flash("No conversation ID provided.", "error")
        return redirect(url_for("home"))  # Replace "home" with your desired redirect endpoint

    try:
        conn = get_db_connection()
        with conn:
            conn.execute("DELETE FROM messages WHERE conversation = ?", (lesson_id,))
        flash("Conversation reset successfully.", "success")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
    finally:
        conn.close()

    return redirect(f"/lesson?id={lesson_id}") 


@app.errorhandler(404)
def error_not_found(_error):
  return render_template('404.html', 
      session_id = get_session_id(),
      version = VERSION,
      current_path=request.path)

def get_session_id():
    global states

    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    session_id = session['session_id']

    return session_id

if __name__ == '__main__':
    app.run(port=8000, debug=True)
