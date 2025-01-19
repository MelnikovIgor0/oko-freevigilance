from flask import Flask, request, make_response
from flask import jsonify
import migrator
from config.config import parse_config
from model.user import User, create_user
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
            jwt.decode(token, app.config['secret_key'], algorithms="HS256")
        except Exception as error:
            return jsonify({'error': 'token is invalid/expired'})
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET'])
def dummy_login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        print('here1')
        return jsonify({'error': 'Invalid credentials'})
    if auth.password != 'password':
        print('here2')
        return jsonify({'error': 'Invalid credentials'})
    print('here3')
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

if __name__ == '__main__':
    app.run(debug=True, port=cfg.server.port)
