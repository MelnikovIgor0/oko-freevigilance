from flask import Flask, request, make_response
from flask import jsonify
from flask_cors import CORS

import migrator
from config.config import parse_config
from model.user import User, create_user, get_user_by_email, get_user_by_username, get_md5
from model.channel import Channel, create_channel, get_channel_by_id, update_channel
from validators import validate_username, validate_email, validate_password, validate_uuid
import jwt
import datetime

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)  

cfg = parse_config()
print(cfg)

# migrator.migrate(cfg.postgres)

def token_required(f):
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'error': 'token is missing'}), 403
        try:
            jwt.decode(token, cfg.server.secret_key, algorithms="HS256")
        except Exception as error:
            return jsonify({'error': 'token is invalid/expired'})
        return f(*args, **kwargs)
    return decorated

@app.route('/users/login', methods=['POST'])
def login():
    body = request.get_json()
    email = body.get('email')
    password = body.get('password')
    if not email or not password:
        return jsonify({'error': 'Invalid credentials 1'}), 400
    user = get_user_by_email(cfg.postgres, email)
    password_hash = get_md5(password)
    if user is None or user.password != password_hash:
        return jsonify({'error': 'Invalid credentials 2'}), 400
    token = jwt.encode(
        {
            'user': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=1440)
        },
        cfg.server.secret_key,
    )
    return jsonify({'accessToken': token, 'user': {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'deleted_at': user.deleted_at,
    }})

@app.route('/access', methods=['GET'])
@token_required
def dummy_secret_handler():
    return jsonify({'message': 'valid jwt token'})

@app.route('/users/register', methods=['POST'])
def register():
    body = request.get_json()
    username = body.get('username')
    email = body.get('email')
    password = body.get('password')
    if not username:
        return jsonify({'error': 'username is missing'}), 400
    if not validate_username(username):
        return jsonify({'error': 'username is invalid'}), 400
    if not email:
        return jsonify({'error': 'email is missing'}), 400
    if not validate_email(email):
        return jsonify({'error': 'email is invalid'}), 400
    if not password:
        return jsonify({'error': 'password is missing'}), 400
    if not validate_password(password):
        return jsonify({'error': 'password is invalid'}), 400
    if get_user_by_username(cfg.postgres, username) != None:
        return jsonify({'error': 'user already exists'}), 400
    user = create_user(cfg.postgres, username, password, email)
    return jsonify({'user': {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'deleted_at': user.deleted_at,
    }}), 201

@app.route('/users/info', methods=['POST'])
def info():
    bearer = request.headers.get('Authorization')

    if not bearer:
        return jsonify({'error': 'token is missing'}), 403
    
    token = bearer.split()[1]
    if not token:
        return jsonify({'error': 'token is missing'}), 403
    try:
        email = jwt.decode(token, cfg.server.secret_key, algorithms="HS256")['user']
    except Exception as error:
        return jsonify({'error': 'token is invalid/expired'})
    
    user = get_user_by_email(cfg.postgres, email)
    if user is None:
        return jsonify({'error': 'user not found'}), 404
    
    return jsonify({'user': user})

@app.route('/users/logout', methods=['POST'])
def logout():
    return jsonify({})

@token_required
@app.route('/channels/create', methods=['POST'])
def new_channel():
    body = request.get_json()
    params = body.get('params')
    if not params:
        return jsonify({'error': 'params are missing'}), 400
    print('the params: ', type(params), params)
    channel = create_channel(cfg.postgres, params)
    return jsonify({'channel': {
        'id': channel.id,
        'params': channel.params,
        'enabled': channel.enabled,
    }}), 201

@token_required
@app.route('/channels/<channel_id>', methods=['GET'])
def get_channel(channel_id: str):
    if not validate_uuid(channel_id):
        return jsonify({'error': 'channel_id is invalid'}), 400
    channel = get_channel_by_id(cfg.postgres, channel_id)
    if channel is None:
        return jsonify({'error': 'channel not found'}), 404
    return jsonify({'channel': {
        'id': channel.id,
        'params': channel.params,
        'enabled': channel.enabled,
    }}), 200

@token_required
@app.route('/channels/<channel_id>', methods=['PATCH'])
def patch_channel(channel_id: str):
    if not validate_uuid(channel_id):
        return jsonify({'error': 'channel_id is invalid'}), 400
    channel_old = get_channel_by_id(cfg.postgres, channel_id)
    if channel_old is None:
        return jsonify({'error': 'channel not found'}), 404
    body = request.get_json()
    params = body.get('params')
    enabled = body.get('enabled')
    print('pre here')
    update_channel(cfg.postgres, channel_id, params, enabled)
    print('here')
    return jsonify({'channel': {
        'id': channel_id,
        'params': channel_old.params if params is None else params,
        'enabled': channel_old.enabled if enabled is None else enabled,
    }}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=cfg.server.port)
