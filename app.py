from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
import os
import time
import re
from google import genai
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)
DB = os.environ.get("DB_PATH", "smartcampus.db")

gemini_key = os.environ.get("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=gemini_key) if gemini_key else None

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        due_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending'
    );
    CREATE TABLE IF NOT EXISTS notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        summary TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
        CREATE TABLE IF NOT EXISTS lectures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        lecture_date TEXT NOT NULL,
        notes TEXT,
        video_url TEXT
    );
    """)
    if conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO tasks(title,subject,due_date,status) VALUES(?,?,?,?)",
            [
                ("DBMS Assignment", "DBMS", "2026-09-20", "Pending"),
                ("Java Lab Record", "Java", "2026-09-22", "Pending"),
                ("OS Unit Test", "Operating Systems", "2026-09-25", "Pending"),
            ],
        )
    conn.commit()
    conn.close()

def summarize_notice(text):
    clean = " ".join(text.split())
    sentences = [s.strip() for s in clean.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    summary = sentences[:3]
    keywords = []
    for word in ["exam", "assignment", "registration", "fee", "deadline", "attendance", "holiday", "workshop", "submission"]:
        if word in clean.lower():
            keywords.append(word.title())
    return {
        "short": " ".join(summary)[:500],
        "keywords": keywords[:6]
    }

def ai_reply(message):

    if not gemini_client:
        return "Gemini is not configured."

    prompt = f"""
You are SmartCampus AI, an educational assistant for college students.

Answer the student's question clearly and simply.
Explain concepts in beginner-friendly language.
Give examples when useful.
For programming questions, provide correct examples.

Student question:
{message}
"""

    try:

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        print("Gemini assistant error:", e)

        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):

            question = message.lower()

            if "dbms" in question or "database" in question:
                return """
📚 DBMS — Demo Explanation

DBMS stands for Database Management System.

It is software used to create, store, manage and retrieve data from databases.

Examples:
• MySQL
• Oracle
• PostgreSQL
• SQL Server

Important concepts include tables, primary keys, foreign keys, SQL,
normalization and transactions.

Example:
A college can use a database to store student names, roll numbers,
subjects and marks.

⚡ Demo Mode: Gemini API quota is temporarily exhausted.
"""

            if "java" in question:
                return """
☕ Java — Demo Explanation

Java is a high-level, object-oriented programming language.

Important concepts include:

• Classes and Objects
• Inheritance
• Polymorphism
• Encapsulation
• Abstraction
• Exception Handling

Example:

class Student {
    String name;
    int age;
}

⚡ Demo Mode: Gemini API quota is temporarily exhausted.
"""

            if "python" in question:
                return """
🐍 Python — Demo Explanation

Python is a high-level programming language known for its simple syntax.

Example:

numbers = [10, 20, 30]
print(sum(numbers))

Python is commonly used for:
• AI and Machine Learning
• Data Science
• Web Development
• Automation

⚡ Demo Mode: Gemini API quota is temporarily exhausted.
"""

            if "operating system" in question or " os " in " " + question + " ":
                return """
💻 Operating System — Demo Explanation

An Operating System manages computer hardware and software resources.

Major functions include:

• Process Management
• Memory Management
• File Management
• Device Management
• Security

Examples include Windows, Linux and Android.

⚡ Demo Mode: Gemini API quota is temporarily exhausted.
"""

            if "assignment" in question:
                return """
📚 Assignment Help — Demo Mode

SmartCampus helps students:

• Track assignment deadlines
• Mark assignments as completed
• Organize academic work
• Create study plans
• Ask academic questions

You can manage assignments from the Assignments & Deadlines section.

⚡ Demo Mode: Gemini API quota is temporarily exhausted.
"""

            return """
🤖 SmartCampus AI — Demo Assistant

Gemini is temporarily unavailable because the API quota has been
exhausted.

You can ask about:

📚 DBMS
☕ Java
🐍 Python
💻 Operating Systems
📝 Assignments
📖 Exam preparation

⚡ Demo Mode is active. Gemini will automatically provide real AI
answers when the API becomes available again.
"""

        return "Sorry, I couldn't process that question right now."
def get_youtube_id(url):
    patterns = [
        r"(?:v=)([A-Za-z0-9_-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:shorts/)([A-Za-z0-9_-]{11})"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None           



@app.post("/api/lectures/<int:lecture_id>/notes")
def generate_lecture_notes(lecture_id):
    conn = db()
    lecture = conn.execute(
        "SELECT * FROM lectures WHERE id=?",
        (lecture_id,)
    ).fetchone()
    conn.close()

    if not lecture:
        return jsonify({"error": "Lecture not found."}), 404

    if not lecture["video_url"]:
        return jsonify({"error": "This lecture does not have a YouTube URL."}), 400

    video_id = get_youtube_id(lecture["video_url"])

    if not video_id:
        return jsonify({"error": "Invalid YouTube URL."}), 400

    if not gemini_client:
        return jsonify({"error": "Gemini is not configured."}), 500

    # Try to retrieve the YouTube transcript.
    try:
        transcript = YouTubeTranscriptApi().fetch(
            video_id,
            languages=["en"]
        )

        transcript_text = " ".join(
            snippet.text for snippet in transcript
        )

        if not transcript_text.strip():
            raise Exception("No transcript found.")

    except Exception as e:
        print("YouTube transcript unavailable:", e)

        # Fallback for Cloud Run/YouTube transcript blocking.
        demo_notes = f"""
## 📘 Lecture Notes

### Lecture
{lecture["title"]}

### Subject
{lecture["subject"]}

### Overview
This lecture covers important concepts related to {lecture["subject"]}.

### Important Concepts
• Understand the basic concepts introduced in the lecture.
• Review important definitions and terminology.
• Focus on examples discussed during the lecture.
• Revise the concepts before examinations.

### Key Points
• Identify the main concepts from the lecture.
• Understand important definitions.
• Review examples and applications.
• Practice the topic for examination preparation.

### Exam Revision
• Learn the definitions clearly.
• Understand the difference between important concepts.
• Practice important examples.
• Revise the key points before the examination.

> ⚡ Demo Mode: YouTube transcript is temporarily unavailable from the cloud server.
"""

        conn = db()
        conn.execute(
            "UPDATE lectures SET notes=? WHERE id=?",
            (demo_notes, lecture_id)
        )
        conn.commit()
        conn.close()

        return jsonify({"notes": demo_notes})

    # Generate notes from the transcript using Gemini.
    prompt = f"""
You are SmartCampus AI, an educational assistant.

Create clear and useful study notes from this college lecture transcript.

Lecture title:
{lecture["title"]}

Subject:
{lecture["subject"]}

Transcript:
{transcript_text}

Create the following:

1. Short overview
2. Important concepts
3. Key points
4. Important definitions
5. Examples
6. Exam revision points

Use simple student-friendly language.

Do not invent information that is not supported by the transcript.
"""

    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        notes = response.text

    except Exception as e:
        print("Gemini notes error:", e)

        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            notes = f"""
## 📘 Lecture Notes

### Lecture
{lecture["title"]}

### Subject
{lecture["subject"]}

### Overview
This lecture covers important concepts related to {lecture["subject"]}.

### Key Points
• Review the main concepts explained in the lecture.
• Focus on important definitions and examples.
• Revise the concepts before the examination.

### Exam Revision
• Understand the basic concepts.
• Practice important examples.
• Revise definitions and key points.

> ⚡ Demo Mode: Gemini API quota is temporarily exhausted.
"""
        else:
            return jsonify({
                "error": f"Could not generate notes: {str(e)}"
            }), 500

    conn = db()
    conn.execute(
        "UPDATE lectures SET notes=? WHERE id=?",
        (notes, lecture_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"notes": notes})


@app.get("/api/lectures")
def get_lectures():
    conn = db()
    lectures = conn.execute(
        "SELECT * FROM lectures ORDER BY lecture_date DESC"
    ).fetchall()
    conn.close()

    return jsonify([dict(lecture) for lecture in lectures])


@app.post("/api/lectures")
def add_lecture():
    data = request.get_json()

    required = ["title", "subject", "lecture_date"]

    if not all(data.get(x) for x in required):
        return jsonify({"error": "Please fill all lecture fields."}), 400

    conn = db()

    cur = conn.execute(
        """
        INSERT INTO lectures(title, subject, lecture_date, notes, video_url)
        VALUES(?,?,?,?,?)
        """,
        (
            data["title"],
            data["subject"],
            data["lecture_date"],
            data.get("notes", ""),
            data.get("video_url", "")
        )
    )

    conn.commit()

    lecture = conn.execute(
        "SELECT * FROM lectures WHERE id=?",
        (cur.lastrowid,)
    ).fetchone()

    conn.close()

    return jsonify(dict(lecture))


@app.delete("/api/lectures/<int:lecture_id>")
def delete_lecture(lecture_id):
    conn = db()

    conn.execute(
        "DELETE FROM lectures WHERE id=?",
        (lecture_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/")
def home():
    conn = db()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY due_date").fetchall()
    notices = conn.execute("SELECT * FROM notices ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()
    return render_template("index.html", tasks=tasks, notices=notices)

@app.post("/api/tasks")
def add_task():
    data = request.get_json()
    required = ["title", "subject", "due_date"]
    if not all(data.get(x) for x in required):
        return jsonify({"error": "Please fill all fields."}), 400
    conn = db()
    cur = conn.execute(
        "INSERT INTO tasks(title,subject,due_date,status) VALUES(?,?,?,'Pending')",
        (data["title"], data["subject"], data["due_date"])
    )
    conn.commit()
    task = conn.execute("SELECT * FROM tasks WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(task))

@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    conn = db()
    conn.execute("UPDATE tasks SET status=CASE WHEN status='Pending' THEN 'Completed' ELSE 'Pending' END WHERE id=?", (task_id,))
    conn.commit()
    task = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return jsonify(dict(task))

@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    conn = db()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.post("/api/summarize")
def summarize():
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Paste a notice first."}), 400
    result = summarize_notice(text)
    conn = db()
    conn.execute(
        "INSERT INTO notices(title,content,summary,created_at) VALUES(?,?,?,?)",
        ("College Notice", text, result["short"], datetime.now().isoformat(timespec="seconds"))
    )
    conn.commit()
    conn.close()
    return jsonify(result)

@app.post("/api/chat")
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Type a question."}), 400
    return jsonify({"reply": ai_reply(message)})

@app.post("/api/plan")
def plan():
    data = request.get_json()
    subjects = [x.strip() for x in data.get("subjects", "").split(",") if x.strip()]
    days = max(1, min(int(data.get("days", 3)), 14))
    hours = max(1, min(int(data.get("hours", 4)), 12))
    if not subjects:
        return jsonify({"error": "Enter at least one subject."}), 400
    plan = []
    for d in range(1, days + 1):
        items = []
        for i, subject in enumerate(subjects):
            if i >= 3:
                break
            block = max(30, int((hours * 60) / min(len(subjects), 3)))
            items.append(f"{subject} — {block} min")
        plan.append({"day": d, "items": items})
    return jsonify({"days": plan})

init_db()

@app.post("/api/lectures/<int:lecture_id>/quiz")
def generate_lecture_quiz(lecture_id):
    conn = db()

    lecture = conn.execute(
        "SELECT * FROM lectures WHERE id=?",
        (lecture_id,)
    ).fetchone()

    conn.close()

    if not lecture:
        return jsonify({
            "error": "Lecture not found."
        }), 404

    if not lecture["video_url"]:
        return jsonify({
            "error": "This lecture does not have a YouTube URL."
        }), 400

    video_id = get_youtube_id(lecture["video_url"])

    if not video_id:
        return jsonify({
            "error": "Invalid YouTube URL."
        }), 400

    if not gemini_client:
        return jsonify({
            "error": "Gemini is not configured."
        }), 500

    try:
        lecture_notes = lecture["notes"]

        if not lecture_notes or not lecture_notes.strip():
            return jsonify({
                "error": "Please generate AI notes for this lecture first."
            }), 400

        prompt = f"""
You are SmartCampus AI, an educational quiz generator.

Create exactly 5 multiple-choice questions from these
AI-generated college lecture notes.

Lecture:
{lecture["title"]}

Subject:
{lecture["subject"]}

AI Notes:
{lecture_notes}

For each question provide:

Question:
A)
B)
C)
D)
Correct Answer:
Explanation:

Rules:
- Create exactly 5 questions.
- Use only information supported by the notes.
- Make questions useful for college exam revision.
- Keep the difficulty moderate.
- Give exactly 4 options for every question.
"""

        try:
            quiz_response = gemini_client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            quiz_text = quiz_response.text

        except Exception as e:
            print("Gemini quiz error:", e)

            # Demo fallback when Gemini quota is exhausted
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):

                quiz_text = f"""
## 🧠 AI Generated Quiz

Lecture: {lecture["title"]}
Subject: {lecture["subject"]}

### Question 1
What is the main purpose of studying the concepts covered in this lecture?

A) Understanding the subject concepts
B) Avoiding revision
C) Skipping practical learning
D) Ignoring the lecture

**Correct Answer:** A

---

### Question 2
Which approach is useful when revising a college lecture?

A) Ignore definitions
B) Review concepts and examples
C) Skip important topics
D) Study without understanding

**Correct Answer:** B

---

### Question 3
What should a student identify from a lecture?

A) Main concepts and key points
B) Only the lecture date
C) Only the lecture title
D) Nothing

**Correct Answer:** A

---

### Question 4
Why are examples useful during learning?

A) They provide practical understanding
B) They replace all theory
C) They are unrelated to concepts
D) They make revision unnecessary

**Correct Answer:** A

---

### Question 5
What is a useful final revision step?

A) Review important concepts and definitions
B) Delete the notes
C) Ignore difficult topics
D) Stop revising

**Correct Answer:** A

> ⚡ Demo Mode: Gemini API quota is temporarily exhausted.
"""

            else:
                raise

        return jsonify({
            "quiz": quiz_text
        })     
    except Exception as e:
        print("Lecture quiz error:", e)

        return jsonify({
            "error": f"Could not generate quiz: {str(e)}"
        }), 500
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )