from flask import Flask, render_template, request, jsonify, redirect, send_file, send_from_directory, url_for
from psutil import users
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from flask import Flask, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from detect import *
from pathlib import Path
import argparse
import os
import sys
import cv2
import numpy as np
import base64
import subprocess

from detect import parse_opt, run 

app = Flask(__name__)

# Konfigurasi SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/ffc'  # Ganti dengan koneksi database yang sesuai
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model Tabel User
class User(db.Model):
    __tablename__ = 'user'
    nama_user = db.Column(db.String(100))
    email_user = db.Column(db.String(100), unique=True, primary_key=True)
    pw_user = db.Column(db.String(100))

detect_path = os.path.abspath("ffc/yolov5-master")
sys.path.append(detect_path)


# Route untuk halaman pendaftaran
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nama_user = request.form['nama_user']
        email_user = request.form['email_user']
        pw_user = request.form['pw_user']
        
        new_user = User(nama_user=nama_user, email_user=email_user, pw_user=pw_user)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('about'))

    return render_template('register.html')

# Route untuk halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_user = request.form['email_user']
        pw_user = request.form['pw_user']
        
        user = User.query.filter_by(email_user=email_user, pw_user=pw_user).first()
        if user:
            return redirect(url_for('about'))
        else:
            return "Login gagal. Cek kembali email dan password."

    return render_template('masuk.html')

# Endpoint untuk halaman Home
@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/home')
def rumah():
    return render_template('Home.html')

@app.route('/daftar')
def daftar():
    return render_template('daftar.html')

@app.route('/masuk')
def masuk():
    return render_template('login.html')

# Endpoint untuk halaman About
@app.route('/About')
def about():
    return render_template('about.html')

# Endpoint untuk halaman Team
@app.route('/Team')
def team():
    return render_template('team.html')

# Endpoint untuk halaman Fresh Fruit Classification (FFC)
@app.route('/ffc')
def ffc():
    return render_template('FreshFruitClassification.html')

@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    if 'image' in data:
        image_data = data['image'].split(',')[1]  # Mengambil bagian base64 data gambar
        image_data = bytes(image_data, 'utf-8')
        with open('runs/source/gambar.png', 'wb') as file:  # Menyimpan gambar ke runs/source
            file.write(base64.decodebytes(image_data))
        return jsonify({'status': 'success'})
    return jsonify({'status': 'failed'})

@app.route('/get_detected_image')
def get_detected_image():
    experiment_number = get_latest_experiment_number()
    if experiment_number is not None:
        save_dir = Path(f'runs/detect/exp{experiment_number}')  # Sesuaikan dengan struktur direktori yang benar
        image_path = save_dir / 'gambar.png'
        return send_from_directory(str(save_dir), 'gambar.png')
    else:
        return "No exp dir found."

def get_latest_experiment_number():
    detect_dir = Path('runs/detect')
    experiment_dirs = [d for d in os.listdir(detect_dir) if os.path.isdir(detect_dir / d) and d.startswith('exp')]
    if experiment_dirs:
        experiment_numbers = [int(d[3:]) for d in experiment_dirs if d[3:].isdigit()]
        return max(experiment_numbers) if experiment_numbers else None
    else:
        return None

@app.route('/detect_image', methods=['GET'])
def detect_image():
    weights = 'best.pt'
    source_image = 'runs/source/gambar.png'  # Ubah path sesuai dengan lokasi gambar Anda
    
    detection_command = f"python detect.py --weights {weights} --source {source_image}"
    
    try:
        subprocess.run(detection_command.split(), check=True)
        experiment_number = get_latest_experiment_number()
        if experiment_number is not None:
            save_dir = Path(f'runs/detect/exp{experiment_number}')  # Sesuaikan dengan struktur direktori yang benar
            image_path = save_dir / 'gambar.png'
            return send_file(image_path, as_attachment=True)  # Mengirim hasil deteksi sebagai file
        else:
            return "No exp dir found."
    except subprocess.CalledProcessError as e:
        return f"Error during detection: {str(e)}"

if __name__ == '__main__':
    app.run(debug=False, port=800)
