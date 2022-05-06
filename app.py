# setting up connection to database
from pymongo import MongoClient
client = MongoClient('mongodb+srv://test:sparta@cluster0.ocllx.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.dbsparta

# flask package for server side
# render_template and redirect allow us to create concise href anchors
from flask import Flask, render_template, request, jsonify, redirect
app = Flask(__name__)

# when app is run, index.html template will be returned
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/main')
def mainpage():
    return render_template('main.html')

@app.route('/detail')
def mypage():
    return render_template('detail.html')

# for links such as github and blog links, we need to add redirect after return
@app.route('/gittin')
def gittin(): return redirect("https://github.com/kti0940")


@app.route("/profile", methods=["POST"])
def web_post():
    # receives data from the ajax jQuery call
    name_receive = request.form['name_give']
    hi_receive = request.form['hi_give']
    # stores the data into a dictionary
    doc = {
        'name': name_receive,
        'hi': hi_receive,
    }
    #uploads to mongoDB
    db.introduce.insert_one(doc)
    #returns message if connection successful
    return jsonify({'msg': '작성완료!'})


@app.route("/profile", methods=["GET"])
def web_get():
    # receives data from mongoDB and stores it into a list
    intro_list = list(db.introduce.find({}, {'_id': False}))
    # returns the jsonified list to client side
    return jsonify({'intro': intro_list})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)