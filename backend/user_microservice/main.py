from flask import Flask, request, make_response
from flask import jsonify
from config.config import parse_config
from model.channel_resource import create_channel_resource, get_channel_resource_by_resource_id, change_channel_resource_enabled
from model.channel import Channel, create_channel, get_channel_by_id, update_channel
from model.resource import Resource, create_resource, get_resource_by_id, update_resource
from model.user import User, create_user, get_user_by_id, get_user_by_username, get_md5
from validators import validate_username, validate_email, validate_password, validate_uuid, validate_url,\
    validate_name, validate_description, validate_keywords, validate_interval, validate_polygon
import jwt
import datetime

app = Flask(__name__)

cfg = parse_config()
print(cfg)

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
    password_hash = get_md5(auth.password)
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

@token_required
@app.route('/channels/create', methods=['POST'])
def new_channel():
    body = request.get_json()
    params = body.get('params')
    if not params:
        return jsonify({'error': 'params are missing'}), 400
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
    update_channel(cfg.postgres, channel_id, params, enabled)
    return jsonify({'channel': {
        'id': channel_id,
        'params': channel_old.params if params is None else params,
        'enabled': channel_old.enabled if enabled is None else enabled,
    }}), 200

@token_required
@app.route('/resources/create', methods=['POST'])
def new_resource():
    body = request.get_json()
    url = body.get('url')
    if not url:
        return jsonify({'error': 'url is missing'}), 400
    if not validate_url(url):
        return jsonify({'error': 'url is invalid'}), 400
    name = body.get('name')
    if not name:
        return jsonify({'error': 'name is missing'}), 400
    if not validate_name(name):
        return jsonify({'error': 'name is invalid'}), 400
    description = body.get('description')
    if not description:
        return jsonify({'error': 'description is missing'}), 400
    if not validate_description(description):
        return jsonify({'error': 'description is invalid'}), 400
    keywords = body.get('keywords')
    if not keywords:
        return jsonify({'error': 'keywords are missing'}), 400
    if not validate_keywords(keywords):
        return jsonify({'error': 'keywords are invalid'}), 400
    interval = body.get('interval')
    if not interval:
        return jsonify({'error': 'interval is missing'}), 400
    if not validate_interval(interval):
        return jsonify({'error': 'interval is invalid'}), 400
    make_screenshot = False
    sensitivity = body.get('sensitivity')
    if sensitivity:
        make_screenshot = True
    zone_type = None
    polygon = None
    if sensitivity:
        zone_type = body.get('zone_type')
        if not zone_type:
            return jsonify({'error': 'zone_type is missing'}), 400
        if zone_type not in ['fullPage','zone']:
            return jsonify({'error': 'zone_type is invalid'}), 400
        polygon = None
        if zone_type == 'zone':
            polygon = body.get('area')
            if polygon:
                polygon['sensitivity'] = sensitivity
                if not validate_polygon(polygon):
                    print("polygon", polygon)
                    return jsonify({'error': 'polygon is invalid'}), 400
    channels = body.get('channels')
    if channels is None:
        return jsonify({'error': 'at least one channel should be specified'}), 400
    for channel_id in channels:
        channel = get_channel_by_id(cfg.postgres, channel_id)
        if channel is None:
            return jsonify({'error': 'channel not found'}), 404
    
    resource = create_resource(cfg.postgres, url, name, description, keywords, interval, make_screenshot, polygon)
    for channel_id in channels:
        create_channel_resource(cfg.postgres, channel_id, resource.id)
    return jsonify({'resource': {
        'id': resource.id,
        'url': resource.url,
        'name': resource.name,
        'description': resource.description,
        'keywords': resource.keywords,
        'interval': resource.interval,
        'make_screenshot': resource.make_screenshot,
        'enabled': resource.enabled,
        'area': resource.polygon
    }})

@token_required
@app.route('/resources/<resource_id>', methods=['GET'])
def get_resource(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({'error': 'resource_id is invalid'})
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({'error': 'resource not found'}), 404
    return jsonify({'resource': {
        'id': resource.id,
        'url': resource.url,
        'name': resource.name,
        'description': resource.description,
        'keywords': resource.keywords,
        'interval': resource.interval,
        'make_screenshot': resource.make_screenshot,
        'enabled': resource.enabled,
        'area': resource.polygon
    }}), 200

@token_required
@app.route('/resources/<resource_id>', methods=['PATCH'])
def patch_resorce(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({'error': 'resource_id is invalid'}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({'error': 'resource not found'}), 404
    body = request.get_json()
    description = body.get('description')
    if description is not None and not validate_description(description):
        return jsonify({'error': 'description is invalid'}), 400
    keywords = body.get('keywords')
    if keywords is not None and not validate_keywords(keywords):
        return jsonify({'error': 'keywords are invalid'}), 400
    interval = body.get('interval')
    if interval is not None and not validate_interval(interval):
        return jsonify({'error': 'interval is invalid'}), 400
    enabled = body.get('enabled')
    polygon = body.get('area')
    if polygon is not None and not validate_polygon(polygon):
        return jsonify({'error': 'polygon is invalid'}), 400
    update_resource(cfg.postgres, resource_id, description, keywords, interval, enabled, polygon)
    new_resource = get_resource_by_id(cfg.postgres, resource_id)
    return jsonify({'resource': {
        'id': new_resource.id,
        'url': new_resource.url,
        'name': new_resource.name,
        'description': new_resource.description,
        'keywords': new_resource.keywords,
        'interval': new_resource.interval,
        'make_screenshot': new_resource.make_screenshot,
        'enabled': new_resource.enabled,
        'area': new_resource.polygon
    }}), 200

if __name__ == '__main__':
    app.run(debug=True, port=cfg.server.port)
