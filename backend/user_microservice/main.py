from flask import Flask, request, make_response
from flask import jsonify
import migrator
from config.config import parse_config
from model.user import User, create_user, get_user_by_id, get_user_by_username, get_md5
from validators import validate_username, validate_email, validate_password, validate_uuid
import jwt
import datetime

app = Flask(__name__)

cfg = parse_config()
print(cfg)

migrator.migrate(cfg.postgres)

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
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'error': 'Invalid credentials'})
    user = get_user_by_username(cfg.postgres, auth.username)
    print(user)
    password_hash = get_md5(auth.password)
    print(password_hash)
    if user is None or user.password != password_hash:
        return jsonify({'error': 'Invalid credentials'})
    token = jwt.encode(
        {
            'user': auth.username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=1440)
        },
        cfg.server.secret_key,
    )
    return token

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
    print(body)
    print(username, email, password)
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

if __name__ == '__main__':
    app.run(debug=True, port=cfg.server.port)
