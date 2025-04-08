from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date
import os

# Khởi tạo ứng dụng Flask và các cấu hình cơ bản
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.secret_key = 'your_secret_key_here'
db = SQLAlchemy(app)

# Khởi tạo Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ----------------- DATABASE MODELS -----------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', 'student'
    profile_image = db.Column(db.String(100), nullable=True)  # Add profile image field

# Model Student: Quản lý sinh viên với các thông tin như mã sinh viên, tên, email, lớp
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    class_name = db.Column(db.String(20))

# Model Attendance: Quản lý điểm danh với các thông tin như mã sinh viên, ngày, giờ, trạng thái điểm danh và đường dẫn ảnh
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20))
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    status = db.Column(db.String(20))
    image_path = db.Column(db.String(200))

# ----------------- ROUTES -----------------

# Tạo route cho trang login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        # Kiểm tra mật khẩu
        if user and check_password_hash(user.password, password):
            login_user(user)  # Đăng nhập người dùng vào phiên

            # Sau khi đăng nhập, chuyển hướng đến trang chủ
            return redirect(url_for('home'))  # Chuyển hướng đến trang chủ (home)

        return "Thông tin đăng nhập không hợp lệ!"  # Nếu thông tin sai
    return render_template('login.html')  # Trả về form đăng nhập khi GET


# ----------------- ATTENDANCE TODAY ROUTE -----------------
@app.route('/attendance/today')
@login_required
def attendance_today():
    today_str = date.today().strftime("%Y-%m-%d")
    records = Attendance.query.filter_by(date=today_str).all()

    # Lấy thông tin sinh viên dựa trên mã sinh viên (student_id)
    for record in records:
        student = Student.query.filter_by(student_id=record.student_id).first()
        record.student_name = student.name if student else "Unknown"

    return render_template('attendance_today.html', records=records, today=today_str)




# ----------------- API MARK ATTENDANCE -----------------
@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    try:
        # Lấy dữ liệu JSON gửi từ client (AI)
        data = request.get_json()

        # Trích xuất dữ liệu từ JSON
        student_id = data['student_id']
        date = data['date']
        time = data['time']
        status = data['status']
        image_path = data['image_path']

        # Tạo một bản ghi điểm danh mới
        attendance = Attendance(student_id=student_id, date=date, time=time, status=status, image_path=image_path)

        # Lưu vào cơ sở dữ liệu
        db.session.add(attendance)
        db.session.commit()

        # Trả về phản hồi thành công
        return jsonify({"message": "Attendance marked successfully!"}), 200

    except Exception as e:
        # Nếu có lỗi, trả về thông báo lỗi
        return jsonify({"message": f"Error: {str(e)}"}), 400


# Đảm bảo định nghĩa route cho admin_dashboard
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':  # Kiểm tra nếu người dùng không phải admin thì sẽ chuyển hướng về login
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')  # Trang quản lý admin

# Cập nhật route đăng xuất
@app.route('/logout')
@login_required
def logout():
    logout_user()  # Đăng xuất người dùng
    return redirect(url_for('login'))  # Chuyển hướng về trang login

# ----------------- USER LOADER -----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Tìm người dùng từ database bằng user_id

# ----------------- ADMIN ROUTES -----------------

# Tạo route cho trang đăng ký admin
from flask import flash, redirect, url_for

@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Kiểm tra nếu tài khoản đã tồn tại
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác!', 'danger')
            return redirect(url_for('register_admin'))  # Quay lại trang đăng ký

        # Tạo người dùng admin
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        admin = User(username=username, password=hashed_password, role='admin')

        db.session.add(admin)
        db.session.commit()

        # Flash thông báo đăng ký thành công và chuyển hướng đến trang đăng nhập
        flash('Admin account created successfully!', 'success')
        return redirect(url_for('login'))  # Chuyển hướng đến trang đăng nhập

    # Trả về trang đăng ký admin nếu phương thức là GET
    return render_template('register_admin.html')





@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Cập nhật thông tin người dùng (tên, ảnh, email, v.v.)
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        if 'profile_image' in request.files:
            profile_image = request.files['profile_image']
            filename = secure_filename(profile_image.filename)
            profile_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            current_user.profile_image = filename
        db.session.commit()
        return redirect(url_for('profile'))  # Sau khi cập nhật, chuyển lại đến trang profile

    return render_template('profile.html')  # Trang profile sẽ được render


# ----------------- HOME PAGE -----------------
@app.route('/')
@login_required  # Đảm bảo người dùng đã đăng nhập
def home():
    if current_user.role == 'admin':
        # Chỉ cho phép admin vào trang này, nếu người dùng là admin
        total_students = Student.query.count()
        today_str = date.today().strftime("%Y-%m-%d")
        checked_in = Attendance.query.filter_by(date=today_str).count()
        absent = total_students - checked_in
        return render_template("index.html", total_students=total_students, checked_in=checked_in, absent=absent)

    # Nếu người dùng không phải admin, redirect về trang login
    return redirect(url_for('login'))


# Set the folder to save uploaded images
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'  # This is the folder where images will be saved


# ----------------- STUDENT MANAGEMENT -----------------
@app.route('/students', methods=['GET'])
@login_required
def list_students():
    if current_user.role not in ['admin', 'teacher']:  # Kiểm tra quyền truy cập
        return redirect(url_for('home'))

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

# Thêm sinh viên
@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if current_user.role not in ['admin', 'teacher']:  # Kiểm tra quyền truy cập
        return redirect(url_for('home'))

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

# Sửa sinh viên
@app.route('/students/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    if current_user.role not in ['admin', 'teacher']:  # Kiểm tra quyền truy cập
        return redirect(url_for('home'))

    student = Student.query.get_or_404(id)

    if request.method == 'POST':
        student.student_id = request.form['student_id']
        student.name = request.form['name']
        student.email = request.form['email']
        student.class_name = request.form['class_name']

        db.session.commit()
        return redirect(url_for('list_students'))

    return render_template("student_edit.html", student=student)

# Xóa sinh viên
@app.route('/students/delete/<int:id>', methods=['GET'])
@login_required
def delete_student(id):
    if current_user.role not in ['admin', 'teacher']:  # Kiểm tra quyền truy cập
        return redirect(url_for('home'))

    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('list_students'))

# ----------------- START SERVER -----------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Khởi tạo database nếu chưa có
    app.run(debug=True)
