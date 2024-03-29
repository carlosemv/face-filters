#!/usr/bin/env python
import os
import shutil
from flask import Flask, render_template, request, \
    Response, send_file, redirect, url_for
from camera import Camera

app = Flask(__name__)
camera = None

def get_camera():
    global camera
    if not camera:
        camera = Camera()

    return camera

@app.route('/')
def root():
    return redirect(url_for('index', mode='landmark'))

@app.route('/index/<mode>')
def index(mode):
    return render_template('index.html', mode=mode)

def gen(camera, mode):
    while True:
        frame = camera.get_frame(mode)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed/<mode>')
def video_feed(mode):
    camera = get_camera()
    return Response(gen(camera, mode),
        mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture/<mode>')
def capture(mode):
    camera = get_camera()
    stamp = camera.capture(mode)
    return redirect(url_for('show_capture', timestamp=stamp))

def stamp_file(timestamp):
    return 'captures/' + timestamp +".jpg"

# Sends image in "path" to "email", returns result message
# ("sent successfully", "error connecting", etc)
def send_capture(path, email, as_attachment=True):
    raise NotImplementedError

@app.route('/capture/image/<timestamp>', methods=['POST', 'GET'])
def show_capture(timestamp):
    path = stamp_file(timestamp)

    email_msg = None
    if request.method == 'POST':
        if request.form.get('email'):
            email_msg = send_capture(path, request.form['email'])
        else:
            email_msg = "Email field empty!"

    return render_template('capture.html',
        stamp=timestamp, path=path, email_msg=email_msg)

@app.route('/save/image/<timestamp>')
def save(timestamp):
    path = "static/" + stamp_file(timestamp)
    save_dir = "saved/"

    try:
        shutil.copy(path, save_dir)
    except OSError:
        os.mkdir(save_dir)
        shutil.copy(path, save_dir)

    return redirect(url_for('show_capture', timestamp=timestamp))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)