# Mengimport package yg diperlukan
import cv2, time
import os
from PIL import Image
import realtime
from flask_mysqldb import MySQL, MySQLdb
import MySQLdb.cursors

from flask import Flask, Response, redirect, url_for,current_app

def get_frame():
    camera = 0
    video = cv2.VideoCapture(camera, cv2.CAP_DSHOW)
    faceCascade = cv2.CascadeClassifier('static/haarcascade_frontalface_default.xml')
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('static/training.xml')
    
    while True:
        check, frame = video.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            id, conf = recognizer.predict(gray[y:y + h, x:x + w])
            
            user_name = fetch_user_name_from_database(id)
               
            cv2.putText(frame, user_name, (x + 40, y - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0))

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cv2.destroyAllWindows()
    video.release()

def fetch_user_name_from_database(user_id):
    try:
        conn = MySQLdb.connect(host="localhost", user="root", passwd="", db="learning")
        cur = conn.cursor()
        cur.execute("SELECT name FROM user WHERE id = %s", (user_id,))
        result = cur.fetchone()
        
        if result:
            return result[0]
        else:
            return 'Unknown'
    except Exception as e:
        print(f"An error occurred while fetching user data: {e}")
        return 'Unknown'
    finally:
        cur.close()
        conn.close()


# def get_frame():
#     camera = 0
#     video = cv2.VideoCapture(camera, cv2.CAP_DSHOW)
#     faceDeteksi = cv2.CascadeClassifier('static/haarcascade_frontalface_default.xml')
#     recognizer = cv2.face.LBPHFaceRecognizer_create()
#     recognizer.read('static/training.xml')
#     a = 0
#     while True:
#         a = a + 1
#         check, frame = video.read()
#         abu = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         wajah = faceDeteksi.detectMultiScale(abu, 1.3, 5)
#         for (x, y, w, h) in wajah:
#             cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
#             id, conf = recognizer.predict(abu[y:y + h, x:x + w])
#             if id == 1:
#                 id = 'Mifta'
#             else:
#                 id = 'Unknown'
                
#             cv2.putText(frame, str(id), (x + 40, y - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0))
#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame_bytes = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

#     video.release()
#     cv2.destroyAllWindows()



