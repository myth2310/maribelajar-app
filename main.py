from flask import Flask,redirect,url_for, render_template, request,Response,current_app,session,send_file,flash,jsonify
import cv2,time
import cv2, os
import numpy as np
from PIL import Image
from flask_mysqldb import MySQL
import webbrowser
import MySQLdb.cursors
from datetime import datetime
import urllib.parse
from werkzeug.utils import secure_filename
import hashlib
import datetime
import locale
import shutil

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['UPLOAD_FILE_MATERI'] = 'static/materi/'
app.config['UPLOAD_FILE_PROFIL'] = 'static/profil/'

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'learning'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

SECRET_KEY = 'secret'
face_cascade = cv2.CascadeClassifier('static/haarcascade_frontalface_default.xml')

capturing = False
id_input = ''
a = 0
stop_capture = False

def generate_frames():
    camera = cv2.VideoCapture(0)
    global a, capturing, stop_capture 
    stop_capture = True
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if capturing and a < 30:
                    a += 1
                    cv2.imwrite(f'Dataset/User.{id_input}.{a}.jpg', gray[y:y+h, x:x+w])

                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')    
    video.release()
    cv2.destroyAllWindows() 

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture', methods=['POST'])
def capture():
    nama = request.form['nama']
    status = request.form['status']
    level = request.form['level']
    id_kelas = request.form['id_kelas']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (nama,status,level,id_kelas) VALUES (%s, %s, %s, %s)", (nama,status,level,id_kelas))
    mysql.connection.commit()

    global capturing, id_input, a
    capturing = True
    id_input = request.form['id_users']
    a = 0 
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier("static/haarcascade_frontalface_default.xml")
    def getImagesWithLabels(path):
        imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
        faceSamples = []
        Ids = []
        for imagePath in imagePaths:
            pilImage = Image.open(imagePath).convert('L')
            imageNp = np.array(pilImage, 'uint8')
            Id = int(os.path.split(imagePath)[-1].split(".")[1])
            faces = detector.detectMultiScale(imageNp)
            for (x, y, w, h) in faces:
                faceSamples.append(imageNp[y:y + h, x:x + w])
                Ids.append(Id)
        return faceSamples, Ids

    faces, Ids = getImagesWithLabels('Dataset')
    recognizer.train(faces, np.array(Ids))
    recognizer.save('static/training.xml')
    return redirect(url_for('user'))

@app.route('/train', methods=['POST'])
def train():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier("static/haarcascade_frontalface_default.xml")
    def getImagesWithLabels(path):
        imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
        faceSamples = []
        Ids = []
        for imagePath in imagePaths:
            pilImage = Image.open(imagePath).convert('L')
            imageNp = np.array(pilImage, 'uint8')
            Id = int(os.path.split(imagePath)[-1].split(".")[1])
            faces = detector.detectMultiScale(imageNp)
            for (x, y, w, h) in faces:
                faceSamples.append(imageNp[y:y + h, x:x + w])
                Ids.append(Id)
        return faceSamples, Ids

    faces, Ids = getImagesWithLabels('Dataset')
    recognizer.train(faces, np.array(Ids))

    recognizer.save('static/training.xml')

    return redirect(url_for('index'))

session = {}
def get_frame():
    camera = 0
    video = cv2.VideoCapture(camera, cv2.CAP_DSHOW)
    faceCascade = cv2.CascadeClassifier('static/haarcascade_frontalface_default.xml')
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('static/training.xml')
    scanning = True
    start_time = time.time()
    confidence = 0
    while scanning:
        check, frame = video.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            id, confidence = recognizer.predict(gray[y:y + h, x:x + w])

            if id != -1:  # Periksa apakah ID yang valid dikenali
                user_name, user_level = fetch_user_name_from_database(id)
                print(id, user_name,confidence)

                if scanning:
                    cv2.putText(frame, "Scanning...", (x + 10, y + 30), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0))

                if confidence > 75 and user_name != 'Unknown':
                    scanning = False
                    session['id_user'] = id
                    session['nama'] = user_name
                    session['level'] = user_level
                    session['islogin'] = True
                    webbrowser.open_new('http://127.0.0.1:5000/home')

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    video.release()
    cv2.destroyAllWindows()

def fetch_user_name_from_database(user_id):
    try:
        conn = MySQLdb.connect(host="localhost", user="root", passwd="", db="learning")
        cur = conn.cursor()
        cur.execute("SELECT nama, level FROM users WHERE id_user = %s", (user_id,))
        result = cur.fetchone()

        if result:
            user_name, user_level = result[0], result[1]
            return user_name, user_level
        else:
            return 'Unknown', 'Unknown'
    except Exception as e:
        print(f"Terjadi kesalahan saat mengambil data pengguna: {e}")
        return 'Unknown', 'Unknown'
    finally:
        cur.close()
        conn.close()

@app.route('/')
@app.route('/login-face')
def realtime():
    if 'islogin' in session:       
        return redirect(url_for('home'))
    else:
        return render_template('realtime.html')
    
@app.route('/video_feed')
def video_feed():
    return Response(get_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')

#Page Admin
@app.route('/dashboard')
def dashboard():
    if 'islogin' in session:
        username = (session['nama'])
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT COUNT(*) FROM users WHERE level='Guru'")
        result_guru = cur.fetchone()
        count_guru = result_guru['COUNT(*)']

        cur.execute("SELECT COUNT(*) FROM users WHERE level='Siswa'")
        result_siswa = cur.fetchone()
        count_siswa = result_siswa['COUNT(*)']

        cur.execute("SELECT COUNT(*) FROM kelas")
        result_kelas = cur.fetchone()
        count_kelas = result_kelas['COUNT(*)']

        cur.execute("SELECT COUNT(*) FROM jurusan")
        result_jurusan = cur.fetchone()
        count_jurusan = result_jurusan['COUNT(*)']

        return render_template('admin/dashboard.html',username=username, count_guru=count_guru,count_siswa=count_siswa,count_kelas=count_kelas,count_jurusan=count_jurusan)
    else:
        return redirect(url_for('login'))

@app.route('/data')
def data():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT level, COUNT(*) as total FROM users GROUP BY level")
    data = cur.fetchall()
    labels = []
    values = []
    for row in data:
        labels.append(row['level'])
        values.append(row['total'])
    print(labels)
    print(values)
    return jsonify({'labels': labels, 'values': values})

@app.route('/registrasi')
def registrasi():
    if 'islogin' in session:
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM kelas")
            kelas = cursor.fetchall()

            cursor.execute("SELECT * FROM mapel")
            mapel = cursor.fetchall()

            cursor.execute("SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'learning' AND TABLE_NAME = 'users'")
            result = cursor.fetchone()

            next_id = result["AUTO_INCREMENT"]

            
            return render_template('admin/registrasi.html', kelas=kelas, mapel=mapel, next_id=next_id)
    else:
        return redirect(url_for('login'))

@app.route('/kelas')
def kelas():
    if 'islogin' in session:
        curl = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        curl.execute('''
            SELECT kelas.*,jurusan.jurusan,jurusan.id_jurusan
            FROM kelas 
            LEFT JOIN jurusan ON jurusan.id_jurusan = kelas.id_jurusan
        ''')
        kelas = curl.fetchall()
        curl.execute("SELECT * FROM jurusan")
        jurusan = curl.fetchall()
        return render_template('admin/kelas.html',kelas=kelas,jurusan=jurusan)
    else:
        return redirect(url_for('login'))

@app.route('/mata-pelajaran')
def mapel():
    if 'islogin' in session:
        curl = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        curl.execute('''
            SELECT mapel.*, jurusan.jurusan,jurusan.id_jurusan
            FROM mapel 
            LEFT JOIN jurusan ON jurusan.id_jurusan = mapel.id_jurusan
        ''')
        mapel = curl.fetchall()
        curl.execute("SELECT * FROM jurusan")
        jurusan = curl.fetchall()
        return render_template('admin/mapel.html', mapel=mapel,jurusan=jurusan)
    else:
        return redirect(url_for('login'))
    
@app.route('/jurusan')
def jurusan():
    if 'islogin' in session:
        curl = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        curl.execute("SELECT * FROM jurusan")
        jurusan = curl.fetchall()
        return render_template('admin/jurusan.html',jurusan=jurusan)
    else:
        return redirect(url_for('login'))

@app.route('/akademik')
def akademik():
    if 'islogin' in session:
        curl = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        curl.execute("SELECT * FROM akademik")
        akademik = curl.fetchall()
        return render_template('admin/akademik.html',akademik=akademik)
    else:
        return redirect(url_for('login'))

@app.route('/jadwal')
def jadwal():
    if 'islogin' in session:
        curl = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        curl.execute("SELECT * FROM kelas")
        kelas = curl.fetchall()

        curl.execute("SELECT * FROM mapel")
        pelajaran = curl.fetchall()
      
        query = """
            SELECT jadwal.*, mapel.pelajaran AS nama_mapel, kelas.kelas AS nama_kelas, jadwal.day
            FROM jadwal
            INNER JOIN mapel ON jadwal.id_mapel = mapel.id_mapel
            INNER JOIN kelas ON jadwal.id_kelas = kelas.id_kelas
        """
        curl.execute(query)
        data = curl.fetchall()

        locale.setlocale(locale.LC_TIME, 'id_ID')
        day = datetime.datetime.now().strftime('%A')
        print(day)

        return render_template('admin/jadwal.html',pelajaran=pelajaran,kelas=kelas,data=data)
    else:
        return redirect(url_for('login'))

@app.route('/user')
def user():
    if 'islogin' in session:
        curl = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        curl.execute('''
            SELECT users.*, kelas.kelas, jurusan.jurusan, mapel.pelajaran ,mapel.pelajaran_slug, kelas.id_jurusan
            FROM users 
            LEFT JOIN kelas ON users.id_kelas = kelas.id_kelas
            LEFT JOIN jurusan ON kelas.id_jurusan = jurusan.id_jurusan
            LEFT JOIN mapel ON users.id_mapel = mapel.id_mapel
            WHERE users.level = 'Siswa'
        ''')
        users = curl.fetchall()   

        curl.execute("""
            SELECT users.id_user, users.nama, users.level, mapel.pelajaran AS nama_mapel
            FROM users
            INNER JOIN mapel ON users.id_mapel = mapel.id_mapel
            WHERE users.level = 'Guru'
        """)
        guru = curl.fetchall()   

        curl.execute("SELECT * FROM users WHERE level = 'Admin' ")
        admin = curl.fetchall()   
        return render_template('admin/user.html',users=users,guru=guru,admin=admin)
    else:
        return redirect(url_for('login'))

@app.route('/insert-jadwal', methods=['POST'])
def insertJadwal():
    day = request.form['day']
    id_mapel = request.form['id_mapel']
    id_kelas = request.form['id_kelas']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO jadwal (day, id_mapel, id_kelas) VALUES (%s, %s, %s)",(day, id_mapel, id_kelas))
    mysql.connection.commit()
    return redirect(url_for('jadwal'))

@app.route('/edit-jadwal/<int:id_jadwal>', methods=['GET', 'POST'])
def editJadwal(id_jadwal):
    day = request.form['day']
    id_mapel = request.form['id_mapel']
    id_kelas = request.form['id_kelas']
    cur = mysql.connection.cursor()
    cur.execute("UPDATE jadwal SET day = %s, id_mapel = %s, id_kelas = %s WHERE id_jadwal = %s", (day,id_mapel,id_kelas, id_jadwal))
    mysql.connection.commit()
    flash('Jadwal Berhasil diubah')
    return redirect(url_for('jadwal'))

@app.route('/hapus-jadwal/<int:id_jadwal>', methods=['GET', 'POST'])
def hapusJadwal(id_jadwal):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM jadwal WHERE id_jadwal = %s", (id_jadwal,))
        mysql.connection.commit()
        flash('Jadwal Berhasil dihapus')
        return redirect(url_for('jadwal'))

@app.route('/insert-user', methods=['POST'])
def insertUser():
    nama = request.form['nama']
    status = request.form['status']
    level = request.form['level']
    id_mapel = request.form['id_mapel']
    password = request.form['password'] 
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (nama, status, level, id_mapel, password) VALUES (%s, %s, %s, %s, %s)",(nama, status, level, id_mapel, hashed_password))
    mysql.connection.commit()
    return redirect(url_for('user'))

@app.route('/edit-user/<int:id_user>', methods=['GET', 'POST'])
def editUser(id_user):
    if request.method == 'POST':
        nama = request.form['nama']
        status = request.form['status']
        level = request.form['level']
        id_mapel = request.form.get('id_mapel', None)
        id_kelas = request.form.get('id_kelas', None)
        password = request.form.get('password', None)
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET nama=%s, status=%s, level=%s, id_mapel=%s,id_kelas=%s,password=%s WHERE id_user=%s",
                    (nama, status, level, id_mapel,id_kelas, hashed_password, id_user))
        mysql.connection.commit()
        return redirect(url_for('user'))

    if request.method == 'GET':
        cur = mysql.connection.cursor()

        query = """
            SELECT users.*, kelas.kelas, jurusan.jurusan, mapel.pelajaran
            FROM users
            LEFT JOIN kelas ON users.id_kelas = kelas.id_kelas
            LEFT JOIN jurusan ON kelas.id_jurusan = jurusan.id_jurusan
            LEFT JOIN mapel ON users.id_mapel = mapel.id_mapel
            WHERE users.id_user = %s
        """
        cur.execute(query, (id_user,))
        user = cur.fetchone()
     
        cur.execute("SELECT * FROM kelas")
        kelas = cur.fetchall()
        cur.execute("SELECT * FROM mapel")
        mapel = cur.fetchall()
        
        return render_template('admin/edit_user.html', user=user,kelas=kelas,mapel=mapel)

# Fungsi untuk menghapus pengguna
@app.route('/delete-user/<int:id_user>')
def deleteUser(id_user):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE id_user = %s", (id_user,))
    mysql.connection.commit()
    return redirect(url_for('user'))

@app.route('/form-register')
def formRegistrasi():
    if 'islogin' in session:
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM kelas")
            kelas = cursor.fetchall()

            cursor.execute("SELECT * FROM mapel")
            mapel = cursor.fetchall()

        return render_template('admin/formRegistrasi.html', kelas=kelas, mapel=mapel)
    else:
        return redirect(url_for('actionLogin'))

#Page Users
@app.route('/home')
def home():
    if 'islogin' in session:
        level = (session['level'])
        id_user = session['id_user']
        username = (session['nama'])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT users.*, kelas.kelas, jurusan.jurusan, mapel.pelajaran ,mapel.pelajaran_slug, kelas.id_jurusan
            FROM users 
            LEFT JOIN kelas ON users.id_kelas = kelas.id_kelas
            LEFT JOIN jurusan ON kelas.id_jurusan = jurusan.id_jurusan
            LEFT JOIN mapel ON users.id_mapel = mapel.id_mapel
            WHERE users.id_user = %s
        ''', (id_user,))
        user_data = cursor.fetchone()

        id_jurusan = user_data.get('id_jurusan')
        cursor.execute('''
            SELECT mapel.pelajaran, mapel.id_mapel,mapel.pelajaran_slug
            FROM mapel
            WHERE mapel.id_jurusan = %s
        ''', (id_jurusan,))
        user_subjects = cursor.fetchall()
         
        day = datetime.datetime.now().strftime('%A')
        print(day)
        query = """
        SELECT jadwal.day, mapel.pelajaran, jadwal.id_mapel, mapel.pelajaran_slug, users.id_kelas
        FROM users
        INNER JOIN jadwal ON jadwal.id_kelas = users.id_kelas
        LEFT JOIN mapel ON mapel.id_mapel = jadwal.id_mapel
        WHERE users.id_user = %s AND jadwal.day = %s
        """
        cursor.execute(query, (id_user, day))
        jadwal = cursor.fetchall()

        
        cursor.execute('SELECT * FROM akademik WHERE status = 1')
        akademik = cursor.fetchone()  

        return render_template('users/index.html', user=user_data,akademik=akademik,username=username,user_subjects=user_subjects,level=level,jadwal=jadwal )

    else:
        return redirect(url_for('realtime'))

        
@app.route('/materi')
def materi():
    if 'islogin' in session:
        username = (session['nama'])
        level = session['level']
        return render_template('users/materi.html', level=level,username=username)
    else:
        return redirect(url_for('realtime'))

@app.route('/jadwal-pelajaran')
def jadwalPelajaran():
    if 'islogin' in session:
        username = (session['nama'])
        level = session['level']
        id_user = session['id_user']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = """
        SELECT jadwal.day, mapel.pelajaran, jadwal.id_mapel, mapel.pelajaran_slug, users.id_kelas
        FROM users
        INNER JOIN jadwal ON jadwal.id_kelas = users.id_kelas
        LEFT JOIN mapel ON mapel.id_mapel = jadwal.id_mapel
        WHERE users.id_user = %s
        """
        cursor.execute(query, (id_user,))
        jadwal = cursor.fetchall()

        return render_template('users/jadwal.html', level=level,jadwal=jadwal,username=username)
    else:
        return redirect(url_for('realtime'))

@app.route('/profil')
def profil():
    if 'islogin' in session:
        level = session['level']
        id_user = session['id_user']
        username = (session['nama'])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT users.*, kelas.kelas, jurusan.jurusan, mapel.pelajaran, kelas.id_jurusan
            FROM users 
            LEFT JOIN kelas ON users.id_kelas = kelas.id_kelas
            LEFT JOIN jurusan ON kelas.id_jurusan = jurusan.id_jurusan
            LEFT JOIN mapel ON users.id_mapel = mapel.id_mapel
            WHERE users.id_user = %s
        ''', (id_user,))
        user_data = cursor.fetchone()
        return render_template('users/profil.html', level=level,user=user_data, username=username)
    else:
        return redirect(url_for('realtime'))
   
@app.route('/tambah-materi')
def addMateri():
    if 'islogin' in session:
        level = (session['level'])
        id_user = session['id_user']
        username = (session['nama'])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT users.*, mapel.pelajaran
            FROM users 
            LEFT JOIN mapel ON users.id_mapel = mapel.id_mapel
            WHERE users.id_user = %s
        ''', (id_user,))

        user_data = cursor.fetchone()

        cursor.execute('SELECT * FROM kelas')
        kelas_data = cursor.fetchall()       

        cursor.execute('''
            SELECT aktifitas.*, mapel.pelajaran, kelas.kelas
            FROM aktifitas
            LEFT JOIN mapel ON aktifitas.id_mapel = mapel.id_mapel
            LEFT JOIN kelas ON aktifitas.id_kelas = kelas.id_kelas
            WHERE aktifitas.id_user = %s
        ''', (id_user,))
        aktifitas_data = cursor.fetchall()

        return render_template('users/insertMateri.html',user=user_data, kelas=kelas_data, aktifitas=aktifitas_data,level=level, username = username )
    else:
        return redirect(url_for('login'))

@app.route('/daftar-ujian')
def listUjian():
    if 'islogin' in session:
        level = (session['level'])
        username = (session['nama'])
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM kategori WHERE id_user = %s",(session['id_user'],))
        kategori = cursor.fetchall()

        cursor.execute('''
            SELECT users.*, mapel.pelajaran
            FROM users 
            LEFT JOIN mapel ON users.id_mapel = mapel.id_mapel
            WHERE users.id_user = %s
        ''', (session['id_user'],))
        user_data = cursor.fetchone()

        cursor.execute('''
            SELECT soal.*, kategori.nama_kategori
            FROM soal 
            LEFT JOIN kategori ON kategori.kategori_id = soal.kategori_id
            WHERE kategori.id_user = %s
        ''', (session['id_user'],))
        soal = cursor.fetchall()

        return render_template('users/listUjian.html',level=level,username=username,kategori=kategori,user_data=user_data,soal=soal)
    else:
        return redirect(url_for('login'))

@app.route('/form-soal')
def formSoal():
    if 'islogin' in session:
        level = (session['level'])
        username = (session['nama'])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM kategori WHERE id_user = %s",(session['id_user'],))
        kategori = cursor.fetchall()

        return render_template('users/formSoal.html',level=level,username=username,kategori=kategori)
    else:
        return redirect(url_for('login'))


@app.route('/insert-soal', methods=['POST'])
def insertSoal():
    kategori_id = request.form['kategori_id']
    pertanyaan = request.form['pertanyaan']
    jawaban_a = request.form['jawaban_a']
    jawaban_b = request.form['jawaban_b']
    jawaban_c = request.form['jawaban_c']
    jawaban_d = request.form['jawaban_d']
    correct = request.form['correct']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO soal (kategori_id, pertanyaan, jawaban_a, jawaban_b, jawaban_c, jawaban_d, correct) VALUES (%s, %s, %s, %s, %s, %s, %s)", (kategori_id, pertanyaan, jawaban_a, jawaban_b, jawaban_c, jawaban_d, correct))
    mysql.connection.commit()
    flash('Soal Berhasil ditambahkan')
    return redirect(url_for('listUjian'))

@app.route('/edit-soal/<int:soal_id>', methods=['GET', 'POST'])
def editSoal(soal_id):
    if 'islogin' in session:
        level = session['level']
        if request.method == 'GET': 
            username = (session['nama'])
            cur = mysql.connection.cursor()
            cur.execute('''
                SELECT soal.*, kategori.nama_kategori
                FROM soal 
                LEFT JOIN kategori ON kategori.kategori_id = soal.kategori_id
                WHERE soal.soal_id = %s
            ''', (soal_id,))
            soal = cur.fetchone()
            cur.close()
            return render_template('users/formEditSoal.html', soal=soal,level=level,username=username)

        elif request.method == 'POST':
            kategori_id = request.form['kategori_id']
            pertanyaan = request.form['pertanyaan']
            jawaban_a = request.form['jawaban_a']
            jawaban_b = request.form['jawaban_b']
            jawaban_c = request.form['jawaban_c']
            jawaban_d = request.form['jawaban_d']
            correct = request.form['correct']

            cur = mysql.connection.cursor()
            cur.execute('''
                UPDATE soal
                SET kategori_id = %s, pertanyaan = %s, jawaban_a = %s, jawaban_b = %s, jawaban_c = %s, jawaban_d = %s, correct = %s
                WHERE soal_id = %s
            ''', (kategori_id, pertanyaan, jawaban_a, jawaban_b, jawaban_c, jawaban_d, correct, soal_id))
            mysql.connection.commit()
            flash('Soal Berhasil diubah')
            return redirect(url_for('listUjian'))
    
    else:
        return redirect(url_for('login'))


@app.route('/hapus-soal/<int:soal_id>', methods=['GET', 'POST'])
def hapusSoal(soal_id):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM soal WHERE soal_id = %s", (soal_id,))
        mysql.connection.commit()
        flash('Soal Berhasil dihapus')
        return redirect(url_for('listUjian'))

@app.route('/<string:materi_slug>/<int:id_aktifitas>')
def view_pdf(id_aktifitas,materi_slug):
    cur = mysql.connection.cursor()
    cur.execute("SELECT file FROM aktifitas WHERE id_aktifitas = %s", (id_aktifitas,))
    pdf_filename = cur.fetchone()
    cur.close()
    return render_template('users/viewPdf.html', pdf=pdf_filename)
    
@app.route('/<int:id_mapel>/<string:pelajaran_slug>')
def view_materi(id_mapel, pelajaran_slug):
    level = (session['level'])
    username = (session['nama'])
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM aktifitas WHERE id_mapel = %s", (id_mapel,))
    activities = cursor.fetchall()
    
    cursor.execute('''
            SELECT users.*, mapel.pelajaran
            FROM users 
            LEFT JOIN mapel ON users.id_mapel = mapel.id_mapel
            WHERE users.id_mapel = %s
    ''', (id_mapel,))
    row = cursor.fetchone()
    
    cursor.execute('''
            SELECT kategori.*
            FROM kategori 
            LEFT JOIN mapel ON kategori.id_mapel = mapel.id_mapel
            WHERE kategori.id_mapel = %s
    ''', (id_mapel,))
    ujian = cursor.fetchall()

    return render_template('users/materi.html', activities=activities,row=row,level=level,username=username,ujian=ujian)

@app.route('/ujian/<int:kategori_id>')
def ujian(kategori_id):
    level = (session['level'])
    username = (session['nama'])

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM soal WHERE kategori_id = %s", (kategori_id,))
    soal = cur.fetchall()

    cur.execute('''
            SELECT mapel.*
            FROM mapel 
            LEFT JOIN kategori ON mapel.id_mapel = kategori.id_mapel
            WHERE kategori.kategori_id = %s
    ''', (kategori_id,))
    row = cur.fetchone()

    return render_template('users/ujian.html',soal=soal,row=row,level=level,username=username,kategori_id=kategori_id)

# Action Admin
@app.route('/insert-kelas',methods=['POST'])
def insertKelas():
    id_jurusan = request.form['id_jurusan']
    kelas = request.form['kelas']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO kelas (id_jurusan,kelas) VALUES (%s,%s)" ,(id_jurusan,kelas))  
    mysql.connection.commit()
    flash('Kelas Berhasil ditambah')
    return redirect(url_for('kelas'))

@app.route('/edit-kelas/<int:id_kelas>', methods=['GET', 'POST'])
def editKelas(id_kelas):
    id_jurusan = request.form['id_jurusan']
    kelas = request.form['kelas']
    cur = mysql.connection.cursor()
    cur.execute("UPDATE kelas SET id_jurusan = %s, kelas = %s WHERE id_kelas = %s", (id_jurusan,kelas,id_kelas))
    mysql.connection.commit()
    flash('Kelas Berhasil diubah')
    return redirect(url_for('kelas'))
    
@app.route('/hapus-kelas/<int:id_kelas>', methods=['GET', 'POST'])
def hapusKelas(id_kelas):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM kelas WHERE id_kelas = %s", (id_kelas,))
        mysql.connection.commit()
        flash('Kelas Berhasil dihapus')
        return redirect(url_for('kelas'))

@app.route('/insert-mapel',methods=['POST','GET'])
def insertMapel():
    id_jurusan = request.form['id_jurusan']
    pelajaran= request.form['pelajaran']
    pelajaran_slug = generate_slug(pelajaran)
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO mapel (pelajaran,id_jurusan,pelajaran_slug) VALUES (%s,%s,%s)", (pelajaran,id_jurusan,pelajaran_slug))
    mysql.connection.commit()
    flash('Mata Pelajaran Berhasil ditambah')
    return redirect(url_for('mapel'))

@app.route('/edit-mapel/<int:id_mapel>', methods=['GET', 'POST'])
def editMapel(id_mapel):
    pelajaran = request.form['pelajaran']
    id_jurusan = request.form['id_jurusan']
    pelajaran_slug = generate_slug(pelajaran)

    cur = mysql.connection.cursor()
    cur.execute("UPDATE mapel SET pelajaran = %s, id_jurusan = %s, pelajaran_slug = %s WHERE id_mapel = %s", (pelajaran,id_jurusan,pelajaran_slug, id_mapel))
    mysql.connection.commit()
    flash('Mata Pelajaran Berhasil diubah')
    return redirect(url_for('mapel'))

@app.route('/hapus-mapel/<int:id_mapel>', methods=['GET', 'POST'])
def hapusMapel(id_mapel):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM mapel WHERE id_mapel = %s", (id_mapel,))
        mysql.connection.commit()
        flash('Mata Pelajaran Berhasil dihapus')
        return redirect(url_for('mapel'))

def generate_slug(text):
    text = text.lower()
    text = ''.join(e for e in text if (e.isalnum() or e == ' '))
    text = text.replace(' ', '-')
    return text

@app.route('/insert-jurusan',methods=['POST','GET'])
def insertJurusan():
    jurusan= request.form['jurusan']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO jurusan (jurusan) VALUES (%s)", (jurusan,))
    mysql.connection.commit()
    flash('Jurusan Berhasil ditambah')
    return redirect(url_for('jurusan'))

@app.route('/edit-jurusan/<int:id_jurusan>', methods=['GET', 'POST'])
def editJurusan(id_jurusan):
    jurusan = request.form['jurusan']
    cur = mysql.connection.cursor()
    cur.execute("UPDATE jurusan SET jurusan = %s WHERE id_jurusan = %s", (jurusan, id_jurusan))
    mysql.connection.commit()
    flash('Jurusan Berhasil diubah')
    return redirect(url_for('jurusan'))

@app.route('/hapus-jurusan/<int:id_jurusan>', methods=['GET', 'POST'])
def hapusJurusan(id_jurusan):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM jurusan WHERE id_jurusan = %s", (id_jurusan,))
    mysql.connection.commit()
    flash('Jurusan Berhasil dihapus')
    return redirect(url_for('jurusan'))
        
@app.route('/insert-akademik',methods=['POST','GET'])
def insertAkademik():
    tahun_akademik = request.form['tahun_akademik']
    semester = request.form['semester']
    status = request.form['status']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO akademik (tahun_akademik,semester,status) VALUES (%s,%s,%s)", (tahun_akademik,semester,status))
    mysql.connection.commit()
    flash('Akademik Berhasil ditambah')
    return redirect(url_for('akademik'))

@app.route('/edit-akademik/<int:id_akademik>', methods=['GET', 'POST'])
def editAkademik(id_akademik):
    tahun_akademik = request.form['tahun_akademik']
    semester = request.form['semester']
    status = request.form['status']
    cur = mysql.connection.cursor()
    cur.execute("UPDATE akademik SET tahun_akademik = %s, semester = %s, status = %s WHERE id_akademik = %s", (tahun_akademik,semester,status, id_akademik))
    mysql.connection.commit()
    flash('Akademik Berhasil diubah')
    return redirect(url_for('akademik'))

@app.route('/hapus-akademik/<int:id_akademik>', methods=['GET', 'POST'])
def hapusAkademik(id_akademik):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM akademik WHERE id_akademik = %s", (id_akademik,))
        mysql.connection.commit()
        flash('Akademik Berhasil dihapus')
        return redirect(url_for('akademik'))

#Action User
@app.route('/login')
def login():
    if 'islogin' in session:       
        return redirect(url_for('home'))
    else:
        return render_template('users/login.html')

@app.route('/score')
def score():
    return render_template('users/score.html')

@app.route('/insert-kategori',methods=['POST','GET'])
def insertKategori():
    id_user = session['id_user'] 
    id_mapel = request.form['id_mapel']
    nama_kategori = request.form['nama_kategori']
    kategori = request.form['kategori']
    date = request.form['date']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO kategori (id_user,id_mapel,nama_kategori,kategori,date) VALUES (%s,%s,%s,%s,%s)", (id_user,id_mapel,nama_kategori,kategori,date))
    mysql.connection.commit()
    flash('Akademik Berhasil ditambah')
    return redirect(url_for('listUjian'))   

@app.route('/edit-kategori/<int:kategori_id>', methods=['GET', 'POST'])
def editKategori(kategori_id):
    id_mapel = request.form['id_mapel']
    nama_kategori = request.form['nama_kategori']
    kategori = request.form['kategori']
    date = request.form['date']

    cur = mysql.connection.cursor()
    cur.execute("UPDATE kategori SET id_mapel = %s, nama_kategori = %s, kategori = %s, date = %s WHERE kategori_id = %s", (id_mapel,nama_kategori,kategori,date, kategori_id))
    mysql.connection.commit()
    flash('Kategori Berhasil diubah')
    return redirect(url_for('listUjian'))

@app.route('/hapus-kategori/<int:kategori_id>', methods=['GET', 'POST'])
def hapusKategori(kategori_id):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM kategori WHERE kategori_id = %s", (kategori_id,))
        mysql.connection.commit()
        flash('Kategori Berhasil dihapus')
        return redirect(url_for('listUjian'))

@app.route('/action-login', methods=['GET', 'POST'])
def actionLogin():
    if 'islogin' in session:
        return redirect(url_for('home'))
    if request.method == 'POST' and 'nama' in request.form and 'password' in request.form:
        nama = request.form['nama']
        password = request.form['password'] 

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE nama = %s', (nama,))
        account = cursor.fetchone()

        if account and check_password(password, account['password']):
            session['islogin'] = True
            session['id_user'] = account['id_user']
            session['nama'] = account['nama']
            session['level'] = account['level']
            if account['level'] == 'Admin':
                return redirect(url_for('dashboard'))
            elif account['level'] == 'Guru':
                return redirect(url_for('home'))    
        else:
            flash("User Tidak Ditemukan atau Password Salah")
            return redirect(url_for('login'))
    else:
        return render_template('users/login.html')

def check_password(input_password, stored_password):
    hashed_input_password = hashlib.sha256(input_password.encode()).hexdigest()
    return hashed_input_password == stored_password


@app.route('/insert-materi',methods=['POST', 'GET'])
def insertMateri():
    id_user = session['id_user']
    materi = request.form['materi']
    materi_slug = generate_slug(materi)
    id_kelas = request.form['id_kelas']
    id_mapel = request.form['id_mapel']
    link = request.form['link']
    file = request.files['file']
    date = request.form['date']

    if file:
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(app.config['UPLOAD_FILE_MATERI'])
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
    else:
        filename = None

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO aktifitas (id_user,id_kelas,id_mapel,materi,materi_slug,date,link,file) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)" ,(id_user,id_kelas,id_mapel,materi,materi_slug,date,link,filename))  
    mysql.connection.commit()
    flash('Materi berhasil disimpan')
    return redirect(url_for('home'))

@app.route('/delete-materi/<int:id_aktifitas>')
def deleteMateri(id_aktifitas):
    cur = mysql.connection.cursor()
    cur.execute("SELECT file FROM aktifitas WHERE id_aktifitas = %s", (id_aktifitas,))
    file_info = cur.fetchone()

    cur.execute("DELETE FROM aktifitas WHERE id_aktifitas = %s", (id_aktifitas,))
    mysql.connection.commit()

    if file_info and file_info['file']:
        file_path = os.path.join(app.config['UPLOAD_FILE_MATERI'], file_info['file'])
        if os.path.exists(file_path):
            os.remove(file_path)

    flash('Materi berhasil dihapus')
    return redirect(url_for('home'))

@app.route('/edit-profil/<int:id_user>', methods=['POST', 'GET'])
def editProfil(id_user):
    if request.method == 'POST':
            image = request.files['image']
            if image.filename != '':
                filename = secure_filename(image.filename)
                upload_dir = os.path.join(app.config['UPLOAD_FILE_PROFIL'])
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                file_path = os.path.join(upload_dir, filename)
                image.save(file_path)

                cur = mysql.connection.cursor()
                cur.execute("UPDATE users SET image = %s WHERE id_user = %s",
                            (filename, id_user))  
                mysql.connection.commit()
                cur.close()

                flash('Profile picture updated successfully')
            else:
                flash('No selected file')

    return redirect(url_for('profil')) 

@app.route('/logout')
def logout():
    level = session['level']  
    session.pop('islogin',None)
    session.clear()
    if level == 'Guru':
        return redirect(url_for('login'))
    elif level == 'Admin':
        return redirect(url_for('login'))
    else:
        return redirect(url_for('realtime'))

def get_correct_answers(kategori_id):
    correct_answers = {}
    cur = mysql.connection.cursor()
    cur.execute("SELECT soal_id, correct FROM soal WHERE kategori_id = %s", (kategori_id,))
    rows = cur.fetchall()
    print(rows)
    cur.close()
    print(rows)
    for row in rows:
        question_id = row['soal_id'] 
        correct_option = row['correct'] 
        print("Nilai id_soal:", question_id)
        print("Nilai correct:", correct_option)
        correct_answers[question_id] = correct_option 
    return correct_answers

def calculate_score(user_answers, correct_answers):
    correct_count = 0
    wrong_count = 0
    for question_id, user_choice in user_answers.items():
        if question_id.startswith('question_'):
            question_id = question_id[9:]
            correct_option = correct_answers.get(int(question_id), '')
            if correct_option and user_choice == correct_option:
                correct_count += 1
            else:
                wrong_count += 1
    return correct_count, wrong_count

@app.route('/submit-quiz/<int:kategori_id>', methods=['POST'])
def submit_quiz(kategori_id):
    if request.method == 'POST':
        user_answers = request.form
        correct_answers = get_correct_answers(kategori_id)
        print("Jawaban Pengguna:", user_answers)
        print("Jawaban yang Benar:", correct_answers)
        correct_count, wrong_count = calculate_score(user_answers, correct_answers)
        score = correct_count * 10
        total_questions = len(correct_answers)
        return render_template('users/score.html', score=score, total=total_questions, wrong_count=wrong_count,correct_count=correct_count)


# Fungsi untuk mendapatkan dan memproses frame
def get_coba():
    camera = 0
    video = cv2.VideoCapture(camera, cv2.CAP_DSHOW)
    faceCascade = cv2.CascadeClassifier('static/haarcascade_frontalface_default.xml')
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('static/training.xml')
    scanning = True
    start_time = time.time()
    confidence = 0 
    while True:
        check, frame = video.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            id, confidence = recognizer.predict(gray[y:y + h, x:x + w])

            user_name, user_level = fetch_user_name_from_database(id)

            print(user_name)

            if scanning:
                cv2.putText(frame, f"conf: {confidence}", (x + 40, y - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0))

            
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        if confidence > 75 and scanning:
            scanning = False 
            video.release()
            cv2.destroyAllWindows() 
       
@app.route('/coba')
def coba():
    return render_template('coba.html')
    
@app.route('/video_coba')
def video_coba():
    return Response(get_coba(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/panduan')
def panduan():
    pdf_file_path = os.path.join(app.static_folder, 'panduan.pdf') 
    return send_file(pdf_file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)


