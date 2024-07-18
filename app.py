import json
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson.json_util import dumps
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "MyApp"
app.config['MONGO_URI'] = "mongodb://localhost:27017/User"
mongo = PyMongo(app)

#create new users
@app.route('/add', methods=['POST'])
def create_user():
    _json        = request.json
    _name        = _json['name']
    _email       = _json['email']
    _pasword     = _json['password']
    _dob  = _json['dob']
    if _name and _email and _pasword and _dob and request.method == "POST":
        hashed_password = generate_password_hash(_pasword)
        formatted_dob = datetime.strptime(_dob, '%d-%m-%Y').strftime('%Y-%m-%d')
        _id = mongo.db.user.insert_one({
            "user_name" : _name,
            "user_email" : _email,
            "user_password" : hashed_password,
            "user_dob" : formatted_dob,
            "created_at" : datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        }) 
        if _id:
            resp = jsonify("User added successfully")
            resp.status = 200
            return resp
    else:
        not_found() 
#list users whoes bithday is between same month
@app.route("/find_user", methods = ['POST'])
def find_user():
    _json = request.json
    from_date = _json['from_date']
    to_date = _json['to_date']
    if from_date and to_date and request.method == 'POST':
        
        record = mongo.db.user.find({
            "user_dob":{ 
                    "$gte" : from_date,
                    "$lte" : to_date
            }
        })
        return json.loads(dumps(record))
    
#list users sharing birthday in a same month (group by month)
@app.route("/list_user_by_bithday", methods = ['GET'])
def list_user():
   
    if request.method == 'GET':
        pipeline = [
            {
                "$project": {
                "year": { "$year": { "$toDate": "$user_dob" } },
                "dob_month" : {"$month" : {"$toDate" : "$user_dob"}},
                "day" : {"$dayOfMonth" : {"$toDate" : "$user_dob"}},
                "user_name" : 1
                }
            },
            {
                "$group": {
                "_id": { "year": "$year" },
                "user_name" : { "$push" : {"user_name" : "$user_name", "month" : "$dob_month", "day" : "$day"}},
                "count": { "$sum": 1 }
                }
            },
            {
                "$sort": { "_id.year": 1 }
            }
        ]


        record = mongo.db.user.aggregate(pipeline)
        
        return json.loads(dumps(record))

@app.errorhandler(404)
def not_found(error = None):
    msg = {
        "status" : 404,
        "message" : "not Found" + request
    }
    return jsonify(msg)

if __name__ == "__main__":
    app.run(debug=True)

