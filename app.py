from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# ----------------- DATABASE MODELS -----------------

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    class_name = db.Column(db.String(20))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20))
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    status = db.Column(db.String(20))
    image_path = db.Column(db.String(200))

# ----------------- ROUTES -----------------

# Trang chủ
@app.route('/')
def home():
    total_students = Student.query.count()
    today_str = date.today().strftime("%Y-%m-%d")
    checked_in = Attendance.query.filter_by(date=today_str).count()
    absent = total_students - checked_in
    return render_template("index.html", total_students=total_students, checked_in=checked_in, absent=absent)

# API nhận dữ liệu điểm danh từ AI
@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    new_att = Attendance(
        student_id=data['student_id'],
        date=data['date'],
        time=data['time'],
        status=data['status'],
        image_path=data['image_path']
    )
    db.session.add(new_att)
    db.session.commit()
    return jsonify({"message": "Attendance saved"}), 200

# Hiển thị danh sách điểm danh hôm nay
@app.route('/attendance/today')
def view_today_attendance():
    today_str = date.today().strftime("%Y-%m-%d")
    records = Attendance.query.filter_by(date=today_str).all()
    return render_template("attendance_today.html", records=records, today=today_str)

# Quản lý sinh viên
@app.route('/students', methods=['GET'])
def list_students():
    # Lọc sinh viên theo các tham số tìm kiếm
    student_id = request.args.get('student_id')
    name = request.args.get('name')
    class_name = request.args.get('class_name')
    faculty = request.args.get('faculty')

    query = Student.query

    if student_id:
        query = query.filter(Student.student_id.like(f"%{student_id}%"))
    if name:
        query = query.filter(Student.name.like(f"%{name}%"))
    if class_name:
        query = query.filter(Student.class_name.like(f"%{class_name}%"))
    if faculty:
        query = query.filter(Student.faculty.like(f"%{faculty}%"))

    students = query.all()
    return render_template("student_list.html", students=students)


@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        email = request.form['email']
        class_name = request.form['class_name']

        if not student_id or not name:
            return "Vui lòng nhập đủ thông tin!", 400

        student = Student(student_id=student_id, name=name, email=email, class_name=class_name)
        db.session.add(student)
        db.session.commit()
        return redirect(url_for('list_students'))

    return render_template('student_add.html')

# Route sửa sinh viên
@app.route('/students/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = Student.query.get_or_404(id)

    if request.method == 'POST':
        student.student_id = request.form['student_id']
        student.name = request.form['name']
        student.email = request.form['email']
        student.class_name = request.form['class_name']

        db.session.commit()
        return redirect(url_for('list_students'))

    return render_template("student_edit.html", student=student)

# Route xóa sinh viên
@app.route('/students/delete/<int:id>', methods=['GET'])
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('list_students'))

# ----------------- START SERVER -----------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Khởi tạo database nếu chưa có
    app.run(debug=True)
