#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import pymongo
from flask import Flask
from flask import request
from flask import render_template

app = Flask(__name__)


def isvalid_md5(hash_string):
    p = re.compile(r'^[a-f0-9]{32}$')
    return p.match(hash_string.lower())


def isvalid_sha1(hash_string):
    p = re.compile(r'^[a-f0-9]{40}$')
    return p.match(hash_string.lower())


def isvalid_sha224(hash_string):
    p = re.compile(r'^[a-f0-9]{56}$')
    return p.match(hash_string.lower())


def isvalid_sha256(hash_string):
    p = re.compile(r'^[a-f0-9]{64}$')
    return p.match(hash_string.lower())


def isvalid_sha384(hash_string):
    p = re.compile(r'^[a-f0-9]{96}$')
    return p.match(hash_string.lower())


def isvalid_sha512(hash_string):
    p = re.compile(r'^[a-f0-9]{128}$')
    return p.match(hash_string.lower())


def connect_database():
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    return client.hashes


@app.route('/')
def show_homepage():
    return render_template('home.html')


@app.route('/legal')
def show_legal():
    return render_template('legal.html')


@app.route('/privacy')
def show_privacy():
    return render_template('privacy.html')


def handle_pagination(param_skip, param_limit):
    entries = range(param_skip, (param_skip + param_limit * 10), param_limit)
    last_entry = (entries[-1] + param_limit)

    if not entries[0] < 1:
        first_entry = (entries[0] - param_limit)
    else:
        first_entry = 0

    return first_entry, last_entry, entries


@app.route('/mail', methods=['GET'])
def show_mail_address_list():
    db = connect_database()
    collection = db.mail_address

    try:
        param_skip = int(request.args.get('skip'))
    except (ValueError, TypeError) as e:
        param_skip = 0

    try:
        param_limit = int(request.args.get('limit'))
    except (ValueError, TypeError) as e:
        param_limit = 10

    pagination_list = handle_pagination(param_skip, param_limit)
    result_list = list(collection.find({}).skip(param_skip).limit(param_limit))
    return render_template('mail.html',
                           url='/mail',
                           mail_address_list=result_list,
                           entries=pagination_list[2],
                           last_entry=pagination_list[1],
                           first_entry=pagination_list[0],
                           pagination_visible=True,
                           search_visible=True)


@app.route('/mail/q/<param_query>', methods=['GET'])
def show_mail_address(param_query):
    db = connect_database()
    collection = db.mail_address

    try:
        param_skip = int(request.args.get('skip'))
    except (ValueError, TypeError) as e:
        param_skip = 0

    try:
        param_limit = int(request.args.get('limit'))
    except (ValueError, TypeError) as e:
        param_limit = 10

    result_list = list(collection.find({}).skip(param_skip).limit(param_limit))
    return render_template('mail.html',
                           mail_address_list=result_list,
                           search_visible=True)


@app.route('/hash/encrypt', methods=['GET'])
def show_encrypt_form():
    return render_template('encrypt.html',
                           search_visible=True)


@app.route('/hash/encrypt/search', methods=['GET'])
def show_encrypt_result():
    db = connect_database()
    collection = db.password

    try:
        param_query = request.args.get('q')
    except (ValueError, TypeError) as e:
        param_query = ''

    result_list = list(collection.find({'password': param_query}))
    return render_template('encrypt.html',
                           hash_list=result_list,
                           search_visible=True)


@app.route('/hash/decrypt', methods=['GET'])
def show_hash_list():
    db = connect_database()
    collection = db.password

    try:
        param_skip = int(request.args.get('skip'))
    except (ValueError, TypeError) as e:
        param_skip = 0

    try:
        param_limit = int(request.args.get('limit'))

        if param_limit > 200:
            param_limit = 200
    except (ValueError, TypeError) as e:
        param_limit = 10

    pagination_list = handle_pagination(param_skip, param_limit)
    result_list = list(collection.find().skip(param_skip).limit(param_limit))
    return render_template('decrypt.html',
                           url='/hash/decrypt',
                           hash_list=result_list,
                           entries=pagination_list[2],
                           last_entry=pagination_list[1],
                           first_entry=pagination_list[0],
                           pagination_visible=True,
                           search_visible=True)


@app.route('/hash/decrypt/search', methods=['GET'])
def show_hash():
    db = connect_database()
    collection = db.password

    try:
        param_query = request.args.get('q')
    except (ValueError, TypeError) as e:
        param_query = ''

    md5 = isvalid_md5(param_query)
    sha1 = isvalid_sha1(param_query)
    sha224 = isvalid_sha224(param_query)
    sha256 = isvalid_sha256(param_query)
    sha384 = isvalid_sha384(param_query)
    sha512 = isvalid_sha512(param_query)

    if md5:
        result_list = list(collection.find({'hash.md5': md5.group(0)}))
    elif sha1:
        result_list = list(collection.find({'hash.sha1': sha1.group(0)}))
    elif sha224:
        result_list = list(collection.find({'hash.sha224': sha224.group(0)}))
    elif sha256:
        result_list = list(collection.find({'hash.sha256': sha256.group(0)}))
    elif sha384:
        result_list = list(collection.find({'hash.sha384': sha384.group(0)}))
    elif sha512:
        result_list = list(collection.find({'hash.sha512': sha512.group(0)}))
    else:
        result_list = list(collection.find({'password': param_query}))

    return render_template('decrypt.html',
                           hash_list=result_list,
                           pagination_visible=False,
                           search_visible=True)


if __name__ == '__main__':
    app.run()
