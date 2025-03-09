from flask import Flask, request, make_response
from flask import jsonify
from flask_cors import CORS
from config.config import parse_config
from minio import Minio
from minio.error import S3Error
from model.channel_resource import create_channel_resource, get_channel_resource_by_resource_id, change_channel_resource_enabled
from model.channel import Channel, create_channel, get_channel_by_id, update_channel
from model.resource import Resource, create_resource, get_resource_by_id, update_resource
from model.user import User, create_user, get_user_by_id, get_user_by_email, get_user_by_username, get_md5
from validators import validate_username, validate_email, validate_password, validate_uuid, validate_url,\
    validate_name, validate_description, validate_keywords, validate_interval, validate_polygon
import jwt
import datetime
import base64

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True) 

cfg = parse_config()
print(cfg)

def token_required(f):
    def decorated(*args, **kwargs):
        bearer = request.headers.get('Authorization')
        if not bearer:
            return jsonify({'error': 'token is missing'}), 403
        token = bearer.split()[1]
        if not token:
            return jsonify({'error': 'token is missing'}), 403
        try:
            email = jwt.decode(token, cfg.server.secret_key, algorithms="HS256")['user']
        except Exception as error:
            return jsonify({'error': 'token is invalid/expired'}), 401
        user = get_user_by_email(cfg.postgres, email)
        if user is None:
            return jsonify({'error': 'user not found'}), 404
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
    }}), 200

@app.route('/users/info', methods=['GET'])
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
        return jsonify({'error': 'token is invalid/expired'}), 401
    user = get_user_by_email(cfg.postgres, email)
    if user is None:
        return jsonify({'error': 'user not found'}), 404
    return jsonify({'user': user})

@app.route('/users/logout', methods=['POST'])
def logout():
    return jsonify({}), 200

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
        return jsonify({'error': f'channel {channel_id} not found'}), 404
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
        return jsonify({'error': f'channel {channel_id} not found'}), 404
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
            polygon = body.get('areas')
            if polygon:
                for area in polygon:
                    area['sensitivity'] = sensitivity
                    if not validate_polygon(area):
                        return jsonify({'error': 'polygon is invalid'}), 400
    channels = body.get('channels')
    if channels is None:
        return jsonify({'error': 'at least one channel should be specified'}), 400
    for channel_id in channels:
        channel = get_channel_by_id(cfg.postgres, channel_id)
        if channel is None:
            return jsonify({'error': f'channel {channel_id} not found'}), 404
    
    resource = create_resource(cfg.postgres, url, name, description, keywords, interval, make_screenshot, polygon)
    for channel_id in channels:
        create_channel_resource(cfg.postgres, channel_id, resource.id)

    # TODO: тут еще надо завести крон джобу

    return jsonify({'resource': {
        'id': resource.id,
        'url': resource.url,
        'name': resource.name,
        'description': resource.description,
        'keywords': resource.keywords,
        'interval': resource.interval,
        'make_screenshot': resource.make_screenshot,
        'enabled': resource.enabled,
        'areas': resource.polygon
    }}), 201

@token_required
@app.route('/resources/<resource_id>', methods=['GET'])
def get_resource(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({'error': 'resource_id is invalid'}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({'error': f'resource {resource_id} not found'}), 404
    return jsonify({'resource': {
        'id': resource.id,
        'url': resource.url,
        'name': resource.name,
        'description': resource.description,
        'keywords': resource.keywords,
        'interval': resource.interval,
        'make_screenshot': resource.make_screenshot,
        'enabled': resource.enabled,
        'areas': resource.polygon
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
    polygon = body.get('areas')
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
        'areas': new_resource.polygon
    }}), 200

@token_required
@app.route('/add_channel_to_resource/', methods=['POST'])
def add_channel_to_resource():
    body = request.get_json()
    resource_id = body.get('resource_id')
    channel_id = body.get('channel_id')
    if not resource_id or not channel_id:
        return jsonify({'error': 'resource_id and channel_id are required'}), 400
    if not validate_uuid(resource_id) or not validate_uuid(channel_id):
        return jsonify({'error': 'resource_id and channel_id are invalid'}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({'error': f'resource {resource_id} not found'}), 404
    channel = get_channel_by_id(cfg.postgres, channel_id)
    if channel is None:
        return jsonify({'error': f'channel {channel_id} not found'}), 404
    linked_channels = get_channel_resource_by_resource_id(cfg.postgres, resource_id)
    for item in linked_channels:
        if item.channel_id == channel_id and item.enabled:
            return jsonify({'message': 'channel already linked to resource'}), 200
    create_channel_resource(cfg.postgres, channel_id, resource_id)
    return jsonify({'message': 'channel linked to resource'}), 201

@token_required
@app.route('/remove_channel_from_resource/', methods=['DELETE'])
def remove_channel_from_resource():
    body = request.get_json()
    resource_id = body.get('resource_id')
    channel_id = body.get('channel_id')
    if not resource_id or not channel_id:
        return jsonify({'error': 'resource_id and channel_id are required'}), 400
    if not validate_uuid(resource_id) or not validate_uuid(channel_id):
        return jsonify({'error': 'resource_id and channel_id are invalid'}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({'error': f'resource {resource_id} not found'}), 404
    channel = get_channel_by_id(cfg.postgres, channel_id)
    if channel is None:
        return jsonify({'error': f'channel {channel_id} never was linked to resource {resource_id}'}), 400
    if not channel.enabled:
        return jsonify({'message': f'channel {channel_id} is already unlinked from resource {resource_id}'}), 202
    change_channel_resource_enabled(cfg.postgres, channel_id, resource_id, False)
    return jsonify({}), 200

@token_required
@app.route('/channels_by_resource/<resource_id>', methods=['GET'])
def get_channels_by_resource(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({'error': 'resource_id is invalid'}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({'error': f'resource {resource_id} not found'}), 404
    channels = get_channel_resource_by_resource_id(cfg.postgres, resource_id)
    active_channels = []
    for channel in channels:
        if channel.enabled:
            active_channels.append(channel.channel_id)
    return jsonify({'channels': active_channels}), 200

@token_required
@app.route('/events/create', methods=['POST'])
def create_event():
    print(request.files)
    if 'example_screenshot_5.png' not in request.files:
        return jsonify({'error': 'screenshot is required'}), 400
    image = request.files['example_screenshot_5.png']
    if image is None:
        return jsonify({'error': 'screenshot is required'}), 400
    image_string = base64.b64encode(image.read())
    print(type(image_string), image_string, type(image_string))
    return jsonify({}), 200

if __name__ == '__main__':
    app.run(host=cfg.server.host, port=cfg.server.port, debug=True)
