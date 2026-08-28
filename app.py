import sqlite3
import os
from flask import Flask, redirect, render_template, request, flash, url_for

app = Flask(__name__)
app.secret_key = "your-secret-key-here"


# ============ DATABASE INITIALIZATION ============
def init_db():
    try:
        # Check if database exists and is healthy
        if os.path.exists("database.db"):
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
            print("[OK] Database is healthy!")
            return

    except sqlite3.DatabaseError:
        print("[WARNING] Database is corrupted! Recreating...")
        if os.path.exists("database.db"):
            os.remove("database.db")
            print("[OK] Old database removed")

    # Create fresh database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        course TEXT,
        semester TEXT,
        address TEXT
    )
    """)

    conn.commit()
    conn.close()
    print("[OK] New database created successfully!")


init_db()

# ============ ROUTES ============
# @app.route("/", methods=["GET"])
# def home():
#     try:
#         conn = sqlite3.connect("database.db")
#         cur = conn.cursor()

#         search = request.args.get("search", "").strip()

#         if search:
#             cur.execute("""
#             SELECT * FROM students
#             WHERE student_id LIKE ?
#             OR name LIKE ?
#             OR course LIKE ?
#             ORDER BY id DESC
#             """, (f"%{search}%", f"%{search}%", f"%{search}%"))
#         else:
#             cur.execute("SELECT * FROM students ORDER BY id DESC")

#         students = cur.fetchall()
#         conn.close()

#         return render_template("index.html", students=students, search_query=search)

#     except sqlite3.DatabaseError:
#         flash("Database error! Please restart the application.", "error")
#         return render_template("index.html", students=[], search_query="")


@app.route("/", methods=["GET"])
def home():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    search = request.args.get("search", "").strip()
    course_filter = request.args.get("course", "").strip()
    semester_filter = request.args.get("semester", "").strip()
    sort_by = request.args.get("sort_by", "id")
    sort_order = request.args.get("sort_order", "DESC")

    # Base query
    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if search:
        query += " AND (student_id LIKE ? OR name LIKE ? OR course LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if course_filter:
        query += " AND course = ?"
        params.append(course_filter)

    if semester_filter:
        query += " AND semester = ?"
        params.append(semester_filter)

    # Sorting
    allowed_sort = ["id", "student_id", "name", "course", "semester"]
    if sort_by in allowed_sort:
        query += f" ORDER BY {sort_by} {sort_order}"
    else:
        query += " ORDER BY id DESC"

    cur.execute(query, params)
    students = cur.fetchall()

    # Get all courses and semesters for filters
    cur.execute(
        "SELECT DISTINCT course FROM students WHERE course IS NOT NULL AND course != ''"
    )
    all_courses = [row[0] for row in cur.fetchall()]

    cur.execute(
        "SELECT DISTINCT semester FROM students WHERE semester IS NOT NULL AND semester != ''"
    )
    all_semesters = [row[0] for row in cur.fetchall()]

    conn.close()

    return render_template(
        "index.html",
        students=students,
        search_query=search,
        course_filter=course_filter,
        semester_filter=semester_filter,
        all_courses=all_courses,
        all_semesters=all_semesters,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@app.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        course = request.form.get("course", "").strip()
        semester = request.form.get("semester", "").strip()
        address = request.form.get("address", "").strip()

        if not student_id or not name:
            flash("Student ID and Name are required!", "error")
            return render_template("add_student.html")

        try:
            conn = sqlite3.connect("database.db")
            cur = conn.cursor()

            cur.execute(
                """
            INSERT INTO students 
            (student_id, name, email, phone, course, semester, address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (student_id, name, email, phone, course, semester, address),
            )

            conn.commit()
            conn.close()
            flash(f"Student '{name}' added successfully!", "success")
            return redirect("/")

        except sqlite3.IntegrityError:
            flash("Student ID already exists! Please use a unique ID.", "error")
            return render_template("add_student.html")

        except sqlite3.DatabaseError:
            flash("Database error! Please restart the application.", "error")
            return render_template("add_student.html")

    return render_template("add_student.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    try:
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        if request.method == "POST":
            student_id = request.form.get("student_id", "").strip()
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            course = request.form.get("course", "").strip()
            semester = request.form.get("semester", "").strip()
            address = request.form.get("address", "").strip()

            if not student_id or not name:
                flash("Student ID and Name are required!", "error")
                cur.execute("SELECT * FROM students WHERE id=?", (id,))
                student = cur.fetchone()
                conn.close()
                return render_template("edit_student.html", student=student)

            try:
                cur.execute(
                    """
                UPDATE students 
                SET student_id=?, name=?, email=?, phone=?, 
                    course=?, semester=?, address=?
                WHERE id=?
                """,
                    (student_id, name, email, phone, course, semester, address, id),
                )

                conn.commit()
                conn.close()
                flash(f"Student '{name}' updated successfully!", "success")
                return redirect("/")

            except sqlite3.IntegrityError:
                flash("Student ID already exists! Please use a unique ID.", "error")
                cur.execute("SELECT * FROM students WHERE id=?", (id,))
                student = cur.fetchone()
                conn.close()
                return render_template("edit_student.html", student=student)

        cur.execute("SELECT * FROM students WHERE id=?", (id,))
        student = cur.fetchone()
        conn.close()

        if not student:
            flash("Student not found!", "error")
            return redirect("/")

        return render_template("edit_student.html", student=student)

    except sqlite3.DatabaseError:
        flash("Database error! Please restart the application.", "error")
        return redirect("/")


@app.route("/delete/<int:id>")
def delete_student(id):
    try:
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("SELECT name FROM students WHERE id=?", (id,))
        student = cur.fetchone()

        if student:
            cur.execute("DELETE FROM students WHERE id=?", (id,))
            conn.commit()
            flash(f"Student '{student[0]}' deleted successfully!", "success")
        else:
            flash("Student not found!", "error")

        conn.close()
        return redirect("/")

    except sqlite3.DatabaseError:
        flash("Database error! Please restart the application.", "error")
        return redirect("/")


@app.route("/dashboard")
def dashboard():
    try:
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        # Total students
        cur.execute("SELECT COUNT(*) FROM students")
        total_students = cur.fetchone()[0]

        # Total courses
        cur.execute(
            "SELECT COUNT(DISTINCT course) FROM students WHERE course IS NOT NULL AND course != ''"
        )
        total_courses = cur.fetchone()[0]

        # Students by course
        cur.execute("""
            SELECT course, COUNT(*) as count 
            FROM students 
            WHERE course IS NOT NULL AND course != '' 
            GROUP BY course 
            ORDER BY count DESC
        """)
        course_data = cur.fetchall()

        # Students by semester
        cur.execute("""
            SELECT semester, COUNT(*) as count 
            FROM students 
            WHERE semester IS NOT NULL AND semester != '' 
            GROUP BY semester
        """)
        semester_data = cur.fetchall()

        # Recent students
        cur.execute("SELECT * FROM students ORDER BY id DESC LIMIT 5")
        recent_students = cur.fetchall()

        conn.close()

        return render_template(
            "dashboard.html",
            total_students=total_students,
            total_courses=total_courses,
            course_data=course_data,
            semester_data=semester_data,
            recent_students=recent_students,
        )

    except sqlite3.DatabaseError:
        flash("Database error! Please restart the application.", "error")
        return render_template(
            "dashboard.html",
            total_students=0,
            total_courses=0,
            course_data=[],
            semester_data=[],
            recent_students=[],
        )


@app.route("/export/csv")
def export_csv():
    try:
        import csv
        from io import StringIO
        from flask import Response

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM students ORDER BY id DESC")
        students = cur.fetchall()
        conn.close()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "ID",
                "Student ID",
                "Name",
                "Email",
                "Phone",
                "Course",
                "Semester",
                "Address",
            ]
        )

        for student in students:
            writer.writerow(student)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=students_export.csv"},
        )

    except sqlite3.DatabaseError:
        flash("Database error! Please restart the application.", "error")
        return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
