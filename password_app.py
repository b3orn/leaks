#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import pymongo
import datetime
from flask import Flask
from flask import request
from flask import jsonify
from flask import render_template
from datetime import datetime

app = Flask(__name__)


def get(iterable, keys):
    try:
        result = iterable

        for key in keys:
            result = result[key]

        return result

    except (KeyError, IndexError) as e:
        return None


def guess_hash(hash_string):
    m = re.match(r'^[0-9a-fA-F]+$', hash_string)

    if m:
        hash = {
            32: 'hash.md5',
            40: 'hash.sha1',
            56: 'hash.sha224',
            64: 'hash.sha256',
            96: 'hash.sha384',
            128: 'hash.sha512'
        }

        if len(hash_string) in hash:
            return hash[len(hash_string)], hash_string.lower()

    return 'password', hash_string


def search_hash_or_password(collection, param_query):
    key, hash = guess_hash(param_query)
    
    return list(collection.find({key: hash}, {'_id': 0}))


def handle_pagination(param_skip, param_limit):
    entries = range(param_skip, (param_skip + param_limit * 8), param_limit)
    last_entry = (entries[-1] + param_limit)

    if not entries[0] < 1:
        first_entry = (entries[0] - param_limit)
    else:
        first_entry = 0

    return first_entry, last_entry, entries


def connect_database():
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    return client.hashes


@app.route('/', methods=['GET'])
def show_homepage():
    db = connect_database()
    collection_hash = db.password
    collection_mail = db.mail_address
    amount_hashes = collection_hash.count()
    amount_mails = collection_mail.count()

    return render_template('home.html',
                           amount_hashes='{:,}'.format(amount_hashes),
                           amount_mails='{:,}'.format(amount_mails),
                           alert_visible=True)


@app.route('/legal', methods=['GET'])
def show_legal():
    return render_template('legal.html')


@app.route('/privacy', methods=['GET'])
def show_privacy():
    return render_template('privacy.html')


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
                           mail_address_list=result_list,
                           entries_visible=False,
                           search_visible=True)


@app.route('/mail/search', methods=['GET'])
def lookup_mail_address():
    db = connect_database()
    collection = db.mail_address

    try:
        param_query = request.args.get('q')
    except (ValueError, TypeError) as e:
        param_query = ''

    result_list = list(collection.find({'mail': param_query}))

    return render_template('mail.html',
                           mail_address_list=result_list,
                           entries_visible=True,
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


@app.route('/api/hash/<param_query>', methods=['GET'])
def api_query_hash(param_query):
    db = connect_database()
    collection = db.password

    return jsonify(search_hash_or_password(collection, param_query))


@app.route('/hash/latest', methods=['GET'])
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
    result_list = list(collection.find().skip(
        param_skip).limit(param_limit).sort([('$natural', -1)]))

    return render_template('latest.html',
                           url='/hash/latest',
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

    result_list = search_hash_or_password(collection, param_query)

    return render_template('home.html',
                           hash_list=result_list,
                           pagination_visible=False,
                           search_visible=True)


@app.route('/api/cert/<param_query>', methods=['GET'])
def api_query_cert(param_query):
    db = connect_database()
    collection = db.cert

    result_list = list(collection.find(
        {'subject.common_name': param_query}, {'_id': 0}))

    cert = result_list[0]['cert'].replace('\n', '<br>')

    valid_not_before = datetime.strptime(
        result_list[0]['valid_not_before'].replace('Z', ''),
        '%Y%m%d%H%M%S'
    ).strftime('%d.%m.%Y %H:%M')

    valid_not_after = datetime.strptime(
        result_list[0]['valid_not_after'].replace('Z', ''),
        '%Y%m%d%H%M%S'
    ).strftime('%d.%m.%Y %H:%M')

    subject_alt_names = ', '.join(result_list[0]['subject']['alt_names'])
    subject_common_name = result_list[0]['subject']['common_name']

    subject_organization = result_list[0]['subject']['organization']
    subject_common_name = result_list[0]['subject']['common_name']
    subject_locality = result_list[0]['subject']['locality']
    subject_country_name = result_list[0]['subject']['country_name']
    subject_state = result_list[0]['subject']['state_or_province_name']

    issuer_organization = get(result_list, [0, 'issuer', 'organization'])
    issuer_common_name = get(result_list, [0, 'issuer', 'common_name'])
    issuer_locality = get(result_list, [0, 'issuer', 'locality'])
    issuer_country_name = get(result_list, [0, 'issuer', 'country_name'])
    issuer_state = get(result_list, [0, 'issuer', 'state_or_province_name'])

    return render_template('certificate.html',
                           subject_common_name=subject_common_name,
                           subject_organization=subject_organization,
                           subject_country_name=subject_country_name,
                           subject_locality=subject_locality,
                           subject_state=subject_state,
                           subject_alt_names=subject_alt_names,
                           issuer_state=issuer_state,
                           issuer_locality=issuer_locality,
                           issuer_common_name=issuer_common_name,
                           issuer_country_name=issuer_country_name,
                           issuer_organization=issuer_organization,
                           valid_not_before=valid_not_before,
                           valid_not_after=valid_not_after,
                           cert_list=result_list,
                           cert=cert)


if __name__ == '__main__':
    app.run(debug=True)
