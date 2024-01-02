from flask import Flask
from flask_mysqldb import MySQL
import os

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'learning'
mysql = MySQL(app)

# Define the upload directory
app.config['UPLOAD_FILE_MATERI'] = 'static/materi/'
app.config['FOTO_PROFIL'] = 'static/profil/'
app.config['DATASET'] = 'Dataset'

with app.app_context():
    cur = mysql.connection.cursor()
        
    # Migrasi Data
    cur = mysql.connection.cursor()

    #Detection Average
    cur.execute("DELETE FROM users")
    cur.execute("ALTER TABLE users DROP id_user")
    cur.execute("ALTER TABLE users ADD  id_user INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST")

    #Result Deteksi
    cur.execute("DELETE FROM kelas")
    cur.execute("ALTER TABLE kelas DROP id_kelas")
    cur.execute("ALTER TABLE kelas ADD id_kelas INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST")

    #Detection
    cur.execute("DELETE FROM mapel")
    cur.execute("ALTER TABLE mapel DROP id_mapel")
    cur.execute("ALTER TABLE mapel ADD id_mapel INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST")

    #Users
    cur.execute("DELETE FROM jurusan")
    cur.execute("ALTER TABLE jurusan DROP id_jurusan")
    cur.execute("ALTER TABLE jurusan ADD id_jurusan INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST")

    #Aktifitas
    cur.execute("DELETE FROM aktifitas")
    cur.execute("ALTER TABLE aktifitas DROP id_aktifitas")
    cur.execute("ALTER TABLE aktifitas ADD id_aktifitas INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST")

    def delete_uploaded_files():
        upload_dir = app.config['UPLOAD_FILE_MATERI']
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def delete_profil_files():
        upload_dir = app.config['FOTO_PROFIL']
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def delete_dataset_files():
        upload_dir = app.config['DATASET']
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

    #Matkul
    cur.execute("DELETE FROM akademik")
    cur.execute("ALTER TABLE akademik DROP id_akademik")
    cur.execute("ALTER TABLE akademik ADD  id_akademik INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST")
    mysql.connection.commit()

    #Matkul
    cur.execute("DELETE FROM kategori")
    cur.execute("ALTER TABLE kategori DROP kategori_id")
    cur.execute("ALTER TABLE kategori ADD kategori_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST")
    mysql.connection.commit()

    #Matkul
    cur.execute("DELETE FROM soal")
    cur.execute("ALTER TABLE soal DROP soal_id")
    cur.execute("ALTER TABLE soal ADD soal_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST")
    mysql.connection.commit()

    #Matkul
    cur.execute("DELETE FROM jadwal")
    cur.execute("ALTER TABLE jadwal DROP id_jadwal")
    cur.execute("ALTER TABLE jadwal ADD id_jadwal INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST")
    mysql.connection.commit()

delete_uploaded_files()
delete_dataset_files()
delete_profil_files()