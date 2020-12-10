# -*- coding: utf-8 -*-
import os
import json
import sys
import tweepy
import hashlib
from flask import Flask, session, redirect, render_template, request, jsonify, abort, make_response
from flask_cors import CORS, cross_origin
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask, request, redirect, url_for
# ファイル名をチェックする関数
from werkzeug.utils import secure_filename
# 画像のダウンロード
from flask import send_from_directory, send_file
from bson.json_util import dumps
from pymongo import MongoClient
from pymongo import DESCENDING
from pymongo import ASCENDING

class MongoFindSample(object):
    def __init__(self, dbName, collectionName):
        self.client = MongoClient()
        self.db = self.client[dbName]
        self.collection = self.db.get_collection(collectionName)
        
    def find_one(self, projection=None, filter=None, sort=None):
        return self.collection.find_one(projection=projection, filter=filter, sort=sort)
    
    def find(self, projection=None, filter=None, sort=None):
        return self.collection.find(projection=projection, filter=filter, sort=sort)
    
mongo =MongoFindSample('output_stimulus', 'stimulus')
import time
app = Flask(__name__)
CORS(app, support_credentials=True)
@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    header['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    header['Access-Control-Allow-Methods'] = 'OPTIONS, HEAD, GET, POST, DELETE, PUT'
    return response
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stimulus.sqlite3'
db = SQLAlchemy(app)
ma = Marshmallow(app)
# 画像のアップロード先のディレクトリ
UPLOAD_FOLDER = './stimulus'
# アップロードされる拡張子の制限
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'gif'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
class Entry(db.Model):
    __tablename__ = "stimulus"
    id = db.Column('id', db.Integer, primary_key=True)
    stimulus_type = db.Column('stimulusType', db.String(120), nullable=False)
    label = db.Column('label', db.String(120), nullable=False)
    url = db.Column('url', db.String(120), nullable=False)
class EntrySchema(ma.ModelSchema):
    class Meta:
        model = Entry

def allwed_file(filename):
    # .があるかどうかのチェックと、拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/stimulus/<path:path>')
# ファイルを表示する
def download_file(path):
    return send_file('stimulus/'+path)

@app.route("/push_data", methods=["POST",'GET'])
@cross_origin(support_credentials=True)
def push_data():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "don't exist files"
        file = request.files['file']
        label = request.form['label']
        stimulus_type = request.form['stimulusType']
        if file.filename == '':
            return "don't exist files"
        
        if file and allwed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            entry = Entry(stimulus_type=stimulus_type, label=label, url=filename)
            db.session.add(entry)
            try:
                db.session.commit()
            except Exception as error:
                print(error.orig)
            return 'OK'
    return '''
        <!doctype html>
    <html>
        <head>
            <meta charset="UTF-8">
            <title>
                ファイルをアップロードして判定しよう
            </title>
        </head>
        <body>
            <h1>
                ファイルをアップロードして判定しよう
            </h1>
            <form method = post enctype = multipart/form-data>
            <p><input type=file name = file>
            <input name="label"></input>
            <input name="stimulusType"></input>
            <input type = submit value = Upload>
            </form>
        </body>
    '''
        # res = request.json
        # stimulus_type = res['type']
        # label = res['label']
        # url = res["url"]
        # entry = Entry(stimulus_type=stimulus_type, label=label, url=url)
        # db.session.add(entry)
        # try:
        #     db.session.commit()
        #     return 'ok'
        # except Exception as error:
        #     print(error.orig)

@app.route("/getData", methods=['POST','GET'])
@cross_origin(support_credentials=True)
def selectDataToDatabase():
    res = request.json
    print(res)
    time.sleep(5)
    label = res["label"]
    stimulus_type = res['type']
    if label =='' or stimulus_type == '':
        return abort(404, { 'id': label })
    print(label, stimulus_type)
    if stimulus_type == 'image':
        entries_schema = EntrySchema(many=True)
        answer = db.session.query(Entry.url,Entry.label).filter(Entry.stimulus_type == str(stimulus_type), Entry.label == str(label)).all()
        print("answer", answer)
    elif stimulus_type == 'word':
        result = mongo.find_one(filter={'title':label})
        print(result)
        del result["_id"]
        return jsonify({'entries': result})
    # elif stimulus_type == 'video':
    # else:

def main():
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
# --------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# --------------------------------------------------------------------------