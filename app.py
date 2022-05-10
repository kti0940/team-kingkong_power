from pymongo import MongoClient
import jwt
import datetime
import hashlib

from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'KINGKONG'

client = MongoClient(
    'mongodb+srv://test:sparta@cluster0.sca5z.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.Kinkong


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})
        if user_info:
            return render_template('mainpage.html', user_info=user_info)
        else:
            print('에러')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('loginpage.html', msg=msg)

# 회원가입 기능


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    id_receive = request.form['id_give']
    name_receive = request.form['name_give']
    username_receive = request.form['username_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    doc = {
        'id': id_receive,
        'name': name_receive,
        'username': username_receive,
        'pw': pw_hash,
        "profile_pic": "",
        'profile_pic_real': 'profile_pics/profile_placeholder.png'
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

# id 중복확인


@app.route('/sign_up/check_id', methods=['POST'])
def check_id():
    id_receive = request.form['id_give']
    exists = bool(db.users.find_one({"id": id_receive}))

    return jsonify({'result': 'success', 'exists': exists})

# username 중복확인


@app.route('/sign_up/check_username', methods=['POST'])
def check_username():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))

    return jsonify({'result': 'success', 'exists': exists})

# 로그인기능


@app.route('/sign_in', methods=['POST'])
def sign_in():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'id': id_receive, 'pw': pw_hash})

    if result is None:
        result = db.users.find_one({'username': id_receive, 'pw': pw_hash})

    if result is not None:
        payload = {
            'id': result['id'],
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

# 각 사용자의 프로필과 글을 모아볼 수 있는 공간


@app.route('/user/<username>')
def user(username):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 로그인한 아이디가 db의 'id'이랑 같은게 있나
        my_info = db.users.find_one({"id": payload['id']}, {"_id": False})

        # 내 프로필이면 True, 다른 사람 프로필 페이지면 False  / 자신의 유저네임 동일한지
        status = (username == my_info['username'])

        user_info = db.users.find_one({"username": username}, {"_id": False})

        return render_template('detail.html', user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/update_profile', methods=['POST'])
def save_img():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        username = payload["id"]

        new_doc = {}

        if 'file_give' in request.files:
            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/{username}.{extension}"
            file.save("./static/"+file_path)
            new_doc["profile_pic"] = filename
            new_doc["profile_pic_real"] = file_path
        db.users.update_one({'username': payload['id']}, {'$set': new_doc})

        return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/mainpage')
def main():
    return render_template('mainpage.html')

@app.route('/detailpage')
def detail():
    return render_template('detailpage.html')

@app.route('/content', methods=['POST'])
def posting():

    content_txt_receive = request.form["content_txt_give"]

    content_photo = request.files["content_photo_give"]

    extension = content_photo.filename.split('.')[-1]

    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

    filename = f'content_photo-{mytime}'

    save_to = f'static/{filename}.{extension}'
    content_photo.save(save_to)

    doc = {
        'content_txt': content_txt_receive,
        'content_photo': f'{filename}.{extension}',
    }
    db.content.insert_one(doc)

    return jsonify({'msg': '업로드 완료!'})


@app.route('/listing', methods=['GET'])
def listing():
    contents = list(db.content.find({}, {'_id': False}))
    return jsonify({'contents': contents})



if __name__ == '__mainpage__':
    app.run('0.0.0.0', port=5000, debug=True)
