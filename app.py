from flask import Flask, Response, json, jsonify, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
from functools import wraps
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")


def getDatabase():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

#giriş yapma
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Kullanıcı adı ve şifre alanını doldurun","warning")
            return render_template("login.html")

        connection = getDatabase()
        if connection is None:
            return render_template("login.html",error = "Veri tabanı bağlantısı kurulamadı.")
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]

                flash(f"Giriş Yapıldı, Hoşgeldiniz{user['username']}", "success")
                return redirect(url_for("index"))
            else:
                flash("Kullanıcı adınızı veya şifrenizi hatalı girdiniz.","error")

        except Error as e:
            print(f"Giriş Yapılamadı: {e}")
            flash("Giriş Yapılamadı.","error")
        finally:
            cursor.close()
            connection.close()

    return render_template("login.html")

#giriş kontrolü
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Bu sayfaya erişmek için giriş yapmalısınız.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

#çıkış yapma
@app.route("/logout")
def logout():
    if "user_id" in session:
        session.clear()
        flash("Başarıyla çıkış yaptınız.","success")
    return redirect(url_for("index"))

#kayıt olma
@app.route("/register", methods=["GET", "POST"])
def register():
    
    if "user_id" in session:
        return redirect(url_for("index"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        passwordConfirm = request.form.get("passwordConfirm", "").strip()

        if not all([username, email, password, passwordConfirm]):
            flash("Tüm alanları zorunlu alanları doldurunuz!", "error")
            return render_template("register.html")

        if password != passwordConfirm:
            flash("Şifre alanları eşleşmiyor.", "danger")
            return render_template("register.html")

        if len(password) < 7:
            flash("Şifre en az 6 karakter olmalıdır!", "danger")
            return render_template("register.html")

        connection = getDatabase()
        if connection is None:
            return render_template("register.html",error = "Veri tabanı bağlantısı kurulamadı.")
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            user = cursor.fetchone()

            if user:
                flash("Bu E-posta veya kullanıcı adı daha önce alınmış!", "danger")
                return render_template("register.html")

            hashedPassword = generate_password_hash(password, method="pbkdf2:sha256")
            cursor.execute(
                "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                (username, email, hashedPassword, "student")
            )
            connection.commit()
            flash("Kayıt Başarılı.", "success")
            return redirect(url_for("login"))

        except Error as e:
            print(f"Kayıt Olunamadı: {e}")
            flash("Kayıt Olunamadı.", "danger")
        finally:
            cursor.close()
            connection.close()

    return render_template("register.html")


#admin yetkisi kontrolü
def adminRequired(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "admin":
            flash("Erişim Hatası", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

#admin paneli
@app.route("/admin")
@adminRequired
def adminPage():
    return "Admin Paneline Hoşgeldiniz!"

#ana sayfa
@app.route("/")
def index():
    if "user_id" not in session:
        flash("Bu sayfaya erişmek için giriş yapmalısınız.", "warning")
        return redirect(url_for("login"))
    return render_template("index.html", username=session.get("username"))


#öğrencileri listeleme
@app.route("/student",methods=['GET'])
@login_required
def students():
    
    connection = getDatabase()
    if connection is None:
        return render_template("student.html",error = "Veri tabanı bağlantısı kurulamadı.")
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()#öğrenci kayıtlarını getir.
        if not students:
            return "kayıtlı öğrenci bulunamadı"
    except mysql.connector.Error as hata1:
            print(f"Hata oluştu: {hata1}")  
            return "Öğrenciler listelenirken bir hata oluştu."
    finally:
        cursor.close()
        connection.close()
    
    if request.args.get("format") == "json":
         #return jsonify(students) türkçe karakterleri göstermek için Response kullanıyoruz.(aşağıda)
         return Response(
            json.dumps(students, ensure_ascii=False),
            mimetype="application/json; charset=utf-8"
            #Response'un hangi tür veri göndereceğini mimetype ile
            # tarayıcıya belirtiyoruz(html,json,metin vb...)
        ) 
    return render_template("students.html",students=students)


#öğrenci ekleme
@app.route("/addStudent",methods=['GET','POST'])
@login_required
def addStudent():
    if request.method == "POST":
        studentName = request.form["studentName"]
        studentSurename = request.form["studentSurename"]
        studentNo = request.form["studentNo"]
        gender = request.form["gender"]
        departments = request.form["departments"]
        city = request.form["city"]
        comment = request.form.get("comment","").strip()
        if not comment:
            comment = "Açıklama Yok"
        if not all([studentName, studentSurename, studentNo,gender,departments,city]):
         return render_template("addStudent.html", 
                                 message="Lütfen tüm zorunlu alanları doldurun.",
                                 form_data=request.form)
    
        connection = getDatabase()
        if connection is None:
            return render_template("addStudent.html",error = "Veri tabanı bağlantısı kurulamadı.")
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM students WHERE studentNo = %s",(studentNo,))
            numberControl = cursor.fetchone()
            
            if numberControl:
                cursor.close()
                connection.close()
                return render_template("addStudent.html", message=" Bu numara daha önce başka bir öğrenciye verilmiş!")
            
            cursor.execute("INSERT INTO students (studentName,studentSurename,studentNo,gender,departments,city,comment) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                      (studentName,studentSurename,studentNo,gender,departments,city,comment))
            connection.commit()
            
        except Error as e:
              connection.rollback()
              print(f"Hata oluştu: {e}")  
              return "Öğrenci eklenirken bir hata oluştu."
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for("students")) 

    return render_template("addStudent.html")


@app.route("/deleteStudent", methods=['GET', 'POST'])
@login_required
def deleteStudent():
    if request.method == "POST":
        studentNo = request.form["studentNo"]
        reason = request.form["reason"]#öğrenci silme nedeni.

        if not all([studentNo, reason]):
            return render_template("deleteStudent.html",
                                   Warning="Kaydı silinecek öğrencinin numarası ve nedeni girilmelidir!",
                                   form_data=request.form)#eksik form doldurma işlemlerinde veriler sıfırlanmasın diye kullanıyoruz.
            
        if not studentNo.isdigit():
            return render_template("deleteStudent.html",error = "Silinecek öğrencinin numarası rakamlardan oluşmalı.") 

        connection = getDatabase()
        if connection is None:
            return render_template("deleteStudent.html",error = "Veri tabanı bağlantısı kurulamadı.")
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT studentName, studentSurename FROM students WHERE studentNo = %s", (studentNo,))
            student = cursor.fetchone()
            
            if not student:
                cursor.close()
                connection.close()
                return render_template("deleteStudent.html", message="Bu numaraya sahip öğrenci bulunamadı!")

            cursor.execute(
                "INSERT INTO deletedstudents (studentName, studentSurename, studentNo, reason) VALUES (%s, %s, %s, %s)",
                (student['studentName'], student['studentSurename'], studentNo, reason)
            )

            cursor.execute("DELETE FROM students WHERE studentNo = %s", (studentNo,))
            if cursor.rowcount > 0:
                connection.commit()
                return redirect(url_for("students"))
            else:
                return render_template("deleteStudent.html", message="Silme işlemi başarısız oldu!")

        except Error as e:
            connection.rollback()
            print(f"Hata oluştu: {e}")
            return "Öğrenci silinirken hata oluştu."

        finally:
            cursor.close()
            connection.close()

    return render_template("deleteStudent.html")
      
        
#öğrenci bilgilerini gösterme(bir öğrenci)
@app.route("/studentInfo/<int:id>")
@login_required
def studentInfo(id):
    connection = getDatabase()
    if connection is None:
        return render_template("studentInfo.html",error="Veri tabanı bağlantısı kurulamadı")
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM students WHERE id = %s",(id,))
        student = cursor.fetchone()#tek bir öğrenci getireceğiz.
        if student is None:
            print("error:","öğrenci bulunamadı.")
            return render_template("studentInfo.html",error="Öğrenci bulunamadı.")
        
    except Error as e:
        print(f"Hata oluştu: {e}")
        return "Öğrenci bilgileri bulunamadı."
    finally:
        cursor.close()
        connection.close()
    return render_template("studentInfo.html",student=student)


#öğrenci güncelleme
@app.route("/studentUpdate/<int:id>", methods=['GET', 'POST'])
@login_required
def studentUpdate(id):
    connection = getDatabase()
    if connection is None:
        return render_template("studentUpdate.html",error = "Veri tabanı bağlantısı kurulamadı.")
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM students WHERE id=%s", (id,))  
        student = cursor.fetchone()
        if not student:
            return "Öğrenci bulunamadı", 404
            
    except Error as e:
        print(f"öğrenci bilgileri çekilemedi: {e}")
        cursor.close()
        connection.close()
        return "Öğrenci bilgileri bulunamadı.."
    
    if request.method == "POST":#öğrenci verileri güncellenmez ise eski değeri korunsun.
        studentName = request.form.get("studentName") or student["studentName"]
        studentSurename = request.form.get("studentSurename") or student["studentSurename"]
        studentNo = request.form.get("studentNo") or student["studentNo"]
        gender = request.form.get("gender") or student["gender"]
        departments = request.form.get("departments") or student["departments"]
        city = request.form.get("city") or student["city"]
        comment = request.form.get("comment") or student["comment"]
        
        if not comment:
            comment = "Açıklama Yok"
        
        try:
            cursor.execute(
                "UPDATE students SET studentName=%s, studentSurename=%s, studentNo=%s, gender=%s, departments=%s, city=%s, comment=%s WHERE id=%s",
                (studentName, studentSurename, studentNo, gender, departments, city, comment, id))
            connection.commit()   
        except Error as e:
            print(f"Öğrenci güncelleme hatası: {e}")
            return "Öğrenci güncellenemedi"
            
        finally:
            cursor.close()
            connection.close()       
        return redirect(url_for("students"))
    
    cursor.close()
    connection.close()
    return render_template("studentUpdate.html", student=student)
        
  
#öğrenci arama 
@app.route("/studentSearch", methods=["GET", "POST"])
@login_required
def studentSearch():
    if request.method == "POST":
        studentNo = request.form.get("studentNo")
        if not studentNo:
            return render_template("studentSearch.html", error = "Lütfen öğrenci numarasını giriniz.")
        if not studentNo.isdigit():
            return render_template("studentSearch.html",error = "Öğrenci numarası sadece rakamlardan oluşmalı.") 

        connection = getDatabase(dictionary = True)
        if connection is None:
            return render_template("studentSearch.html",error = "Veri tabanı bağlantısı kurulamadı.")
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM students WHERE studentNo=%s", (studentNo,))
            student = cursor.fetchone()
            if student:
                return render_template("studentInfo.html", student=student)
            else:
                return render_template("studentSearch.html", hata="Aradığınız öğrenci bulunamadı.")
        except Error as e:
            print(f"Arama hatası: {e}")
            return render_template("studentSearch.html", error="hata")
        finally:
            print(student)
            cursor.close()
            connection.close()

    return render_template("studentSearch.html")

#öğrenciye not ekleme
@app.route("/addGrade",methods=["GET","POST"])
@login_required
def addGrade():
         if request.method == "POST":
            student_id = request.form["student_id"]
            course = request.form["course"]
            grade = request.form["grade"]
            
            if not all([student_id, course, grade]):
                flash("Lütfen tüm alanları doldurun.","error")
                return redirect(url_for("addGrade"))
            
            try:
                grade = float(grade)
                if grade < 0 or grade > 100: 
                    flash("Girilecek not 0 ile 100 arasında olmalıdır.","warning")
                    return redirect(url_for("addGrade"))    
            except ValueError:
                flash("Geçersiz not değeri.","error")
                return redirect(url_for("addGrade"))
            
            connection  = getDatabase()
            if connection is None:
                return render_template("addGrade.html",error = "Veri tabanı bağlantısı kurulamadı.")
            cursor = connection.cursor()
            
            cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
            student = cursor.fetchone()

            if not student:
                cursor.close()
                connection.close()
                flash("Bu ID'ye sahip öğrenci yok.","error")
                return redirect(url_for("addGrade"))
            
            cursor.execute("SELECT * FROM grades WHERE student_id = %s AND course = %s", (student_id, course))
            existing_grade = cursor.fetchone()
            if existing_grade:
                cursor.close()
                connection.close()
                flash("Bu öğrenci için bu derse ait not zaten mevcut.","error")
                return redirect(url_for("addGrade"))
        
            try:
                cursor.execute("INSERT INTO grades (student_id,course,grade) VALUES (%s,%s,%s)",(student_id,course,grade))
                connection .commit()
                flash("Not başarıyla eklendi.","success")
                
            except Error as e:
                connection.rollback()
                print(f"HATA: {e}")
                flash("öğrenciye not eklenirken hata oluştu.","error")
            finally:
                cursor.close()
                connection.close() 
            return redirect(url_for("addGrade"))
        
         return render_template("addGrade.html")
       
       
if __name__ == "__main__":
    app.run(debug=True)
   
   