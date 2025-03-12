from flask import Flask, request, make_response
from flask import jsonify
from flask_cors import CORS
from config.config import parse_config
from minio import Minio
from minio.error import S3Error
from model.channel_resource import create_channel_resource, get_channel_resource_by_resource_id, change_channel_resource_enabled
from model.channel import Channel, create_channel, get_channel_by_id, update_channel, get_all_channels, get_channel_by_name
from model.monitoring_event import MonitoringEvent, get_monitoring_event_by_id, update_monitoring_event_status
from model.resource import Resource, create_resource, get_resource_by_id, update_resource, get_all_resources
from model.user import User, create_user, get_user_by_id, get_user_by_email, get_user_by_username, get_md5
from validators import validate_username, validate_email, validate_password, validate_uuid, validate_url,\
    validate_name, validate_description, validate_keywords, validate_interval, validate_polygon,\
    get_interval, validate_monitoring_event_status
import jwt
import datetime
import base64
from model.s3_interactor import create_bucket, add_object, get_object, get_image
from util.html_parser import extract_text_from_html
from util.cron import create_cron_job, kill_cron_job, update_cron_job
from util.utility import create_daemon_cron_job_for_resource, update_daemon_cron_job_for_resource,\
    get_last_snapshot_id, get_snapshot_times_by_resource_id, get_url_image_base_64
from functools import wraps

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True) 

cfg = parse_config()
print(cfg)


def token_required(f):
    @wraps(f)
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


@app.route('/users/reset', methods=['POST'])
@token_required
def reset():
    return jsonify({}), 200


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


@app.route('/channels/create', methods=['POST'])
@token_required
def new_channel():
    body = request.get_json()
    name = body.get('name')
    if name is None:
        return jsonify({'error': 'name is missing'}), 400
    if not validate_name(name):
        return jsonify({'error': 'name is invalid'}), 400
    channel = get_channel_by_name(cfg.postgres, name)
    if channel is not None:
        return jsonify({'error': 'channel already exists'}), 400
    params = body.get('params')
    if not params:
        return jsonify({'error': 'params are missing'}), 400
    channel = create_channel(cfg.postgres, params, name)
    return jsonify({'channel': {
        'id': channel.id,
        'name': channel.name,
        'enabled': channel.enabled,
    }}), 201


@app.route('/channels/all', methods=['GET'])
@token_required
def find_all_channels():
    channels = get_all_channels(cfg.postgres)
    return jsonify({'channels': 
                    [
                        {
                            'id': channel.id,
                            'name': channel.name,
                            'enabled': channel.enabled,
                        } for channel in channels
                    ]}), 200


@app.route('/channels/<channel_id>', methods=['GET'])
@token_required
def get_channel(channel_id: str):
    if not validate_uuid(channel_id):
        return jsonify({'error': 'channel_id is invalid'}), 400
    channel = get_channel_by_id(cfg.postgres, channel_id)
    if channel is None:
        return jsonify({'error': f'channel {channel_id} not found'}), 404
    return jsonify({'channel': {
        'id': channel.id,
        'enabled': channel.enabled,
        'name': channel.name,
    }}), 200


@app.route('/channels/<channel_id>', methods=['PATCH'])
@token_required
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


@app.route('/channels/<channel_id>', methods=['DELETE'])
@token_required
def delete_channel(channel_id: str):
    if not validate_uuid(channel_id):
        return jsonify({'error': 'channel_id is invalid'}), 400
    channel = get_channel_by_id(cfg.postgres, channel_id)
    if channel is None:
        return jsonify({'error': f'channel {channel_id} not found'}), 404
    update_channel(cfg.postgres, channel_id, None, False)
    return jsonify({}), 200


@app.route('/resources/create', methods=['POST'])
@token_required
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
        description = ''
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
    interval = get_interval(interval)
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

    create_daemon_cron_job_for_resource(resource, cfg.server)

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


@app.route('/resources/<resource_id>', methods=['GET'])
@token_required
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


@app.route('/resources/<resource_id>', methods=['PATCH'])
@token_required
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

    update_daemon_cron_job_for_resource(new_resource, cfg.server)

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


@app.route('/resources/<resource_id>', methods=['DELETE'])
@token_required
def delete_resource(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({'error': 'resource_id is invalid'}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({'error': 'resource not found'}), 404
    update_resource(cfg.postgres, resource_id, None, None, None, False, None)
    resource = get_resource_by_id(cfg.postgres, resource_id)
    update_daemon_cron_job_for_resource(resource, cfg.server)
    return jsonify({}), 200


@app.route('/resources/all', methods=['GET'])
@token_required
def all_resources():
    resources = get_all_resources(cfg.postgres)
    return jsonify({'resources': [{
        'id': resource.id,
        'url': resource.url,
        'name': resource.name,
        'description': resource.description,
        'keywords': resource.keywords,
        'interval': resource.interval,
        'make_screenshot': resource.make_screenshot,
        'enabled': resource.enabled,
        'areas': resource.polygon
    } for resource in resources]}), 200


@app.route('/add_channel_to_resource/', methods=['POST'])
@token_required
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


@app.route('/remove_channel_from_resource/', methods=['DELETE'])
@token_required
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


@app.route('/channels_by_resource/<resource_id>', methods=['GET'])
@token_required
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


@app.route('/events/<event_id>', methods=['GET'])
@token_required
def get_event(event_id: str):
    if not validate_uuid(event_id):
        return jsonify({'error': 'event_id is invalid'}), 400
    event = get_monitoring_event_by_id(cfg.postgres, event_id)
    if event is None:
        return jsonify({'error': f'event {event_id} not found'}), 404
    return jsonify({'event': event}), 200


@app.route('/events/<event_id>', methods=['PATCH'])
@token_required
def update_event(event_id: str):
    if not validate_uuid(event_id):
        return jsonify({'error': 'event_id is invalid'}), 400
    event = get_monitoring_event_by_id(cfg.postgres, event_id)
    if event is None:
        return jsonify({'error': f'event {event_id} not found'}), 404
    body = request.get_json()
    status = body.get('status')
    if status is not None and not validate_monitoring_event_status(status):
        return jsonify({'error': 'status is invalid'}), 400
    update_monitoring_event_status(cfg.postgres, event_id, status)
    return jsonify({}), 200


@app.route('/events/<event_id>/snapshot', methods=['GET'])
@token_required
def get_event_snapshot(event_id: str):
    image = get_object(cfg.s3, 'images', event_id + '.png')
    if image is None:
        return jsonify({'error': f'event {event_id} has no snapshot'}), 404
    image_base64 = base64.b64encode(image).decode('utf-8')
    return jsonify({
        'image': image_base64
    }), 200


@app.route('/events/<event_id>/text', methods=['GET'])
@token_required
def get_event_text(event_id: str):
    html = get_object(cfg.s3, 'htmls', event_id + '.html')
    if html is None:
        return jsonify({'error': f'event {event_id} has no html'}), 404
    text = extract_text_from_html(html)
    return jsonify({
        'text': text
    }), 200


@app.route('/resources/<resource_id>/last_snapshot_id', methods=['GET'])
@token_required
def get_event_last_snapshot_id(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({'error': 'resource_id is invalid'}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({'error': f'resource {resource_id} not found'}), 404
    last_snapshot = get_last_snapshot_id(cfg.s3, resource_id)
    return jsonify({
        'snapshot_id': last_snapshot
    }), 200


@app.route('/resource/<resource_id>/snapshot_times', methods=['GET'])
@token_required
def get_snapshot_times(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({'error': 'resource_id is invalid'}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({'error': f'resource {resource_id} not found'}), 400
    snapshots = get_snapshot_times_by_resource_id(cfg.s3, resource_id)
    return jsonify({'snapshots': [{'id': resource_id + '_' + str(snapshot[1]), 'time': snapshot[0]} for snapshot in snapshots]})


@app.route('/screenshot/', methods=['GET'])
@token_required
def get_screenshot():
    url = request.headers.get('url')
    if url is None:
        return jsonify({'error': 'url is missing'}), 400
    if not validate_url(url):
        return jsonify({'error': 'invalid url'}), 400
    screenshot = get_url_image_base_64(url)
    return jsonify({'screenshot': screenshot}), 200

if __name__ == '__main__':
    app.run(host=cfg.server.host, port=cfg.server.port, debug=True)
