from flask import Flask, request, Response
from flask import jsonify
from flask_cors import CORS
from config.config import parse_config
from model.channel_resource import (
    create_channel_resource,
    get_channel_resource_by_resource_id,
    change_channel_resource_enabled,
    update_resource_channels,
)
from model.channel import (
    create_channel,
    get_channel_by_id,
    update_channel,
    get_all_channels,
    get_channel_by_name,
)
from model.monitoring_event import (
    get_monitoring_event_by_id,
    update_monitoring_event_status,
    filter_monitoring_events,
    filter_monitoring_events_for_report,
)
from model.resource import (
    create_resource,
    get_resource_by_id,
    update_resource,
    get_all_resources,
)
from model.user import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    get_user_by_username,
    get_md5,
)
from validators import (
    validate_username,
    validate_email,
    validate_password,
    validate_uuid,
    validate_url,
    validate_name,
    validate_description,
    validate_keywords,
    validate_interval,
    validate_polygon,
    get_interval,
    validate_monitoring_event_status,
    validate_date_time,
)
import jwt
import csv
import datetime
import io
import os
import json
import time
import base64
import logging
import uuid
from model.s3_interactor import get_object, get_object_created_at
from util.html_parser import extract_text_from_html
from util.utility import (
    create_daemon_cron_job_for_resource,
    update_daemon_cron_job_for_resource,
    get_last_snapshot_id,
    get_snapshot_times_by_resource_id,
    get_url_image_base_64,
)
from functools import wraps
import urllib.parse

app = Flask(__name__)

os.makedirs("/var/log/api", exist_ok=True)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": int(
                time.time() * 1000
            ),  # миллисекунды для совместимости с Loki
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "request_id": getattr(record, "request_id", ""),
            "path": getattr(record, "path", ""),
            "method": getattr(record, "method", ""),
            "user": getattr(record, "user", ""),
        }
        return json.dumps(log_record)


logger = logging.getLogger("api")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("/var/log/api/app.log")
file_handler.setFormatter(JsonFormatter())
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(JsonFormatter())
logger.addHandler(console_handler)


@app.before_request
def before_request():
    request.request_id = str(uuid.uuid4())


@app.after_request
def after_request(response):
    email = "unauthorized"
    bearer = request.headers.get("Authorization")
    if bearer is not None:
        data = bearer.split()
        if len(data) == 2:
            token = bearer.split()[1]
            if token:
                try:
                    email = jwt.decode(token, cfg.server.secret_key, algorithms="HS256")["user"]
                except Exception as error:
                    pass
    log_data = {
        "request_id": getattr(request, "request_id", ""),
        "path": request.path,
        "method": request.method,
        "status": response.status_code,
        "user": email
    }
    logger.info(
        f"Request processed: {request.method} {request.path} - {response.status_code}",
        extra=log_data,
    )
    return response


CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

cfg = parse_config()
print(cfg)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        bearer = request.headers.get("Authorization")
        if bearer is None:
            return jsonify({"error": "token is missing"}), 403
        data = bearer.split()
        if len(data) < 2:
            return jsonify({"error": "invalid auth token"}), 403
        token = data[1]
        if not token:
            return jsonify({"error": "token is missing"}), 403
        try:
            email = jwt.decode(token, cfg.server.secret_key, algorithms="HS256")["user"]
        except Exception as error:
            return jsonify({"error": "token is invalid/expired"}), 401
        user = get_user_by_email(cfg.postgres, email)
        if user is None:
            return jsonify({"error": f"user {email} not found"}), 404
        return f(*args, **kwargs)

    return decorated


@app.route("/liveness")
def liveness_check():
    logger.info(
        "Echoing data",
        extra={
            "request_id": getattr(request, "request_id", ""),
            "path": request.path,
            "method": request.method,
            "data": str("liveness check"),
        },
    )
    return jsonify({"status": "OK"}), 200


@app.route("/users/login", methods=["POST"])
def login():
    body = request.get_json()
    email = body.get("email")
    password = body.get("password")
    if not email or not password:
        return jsonify({"error": "Invalid credentials 1"}), 400
    user = get_user_by_email(cfg.postgres, email)
    password_hash = get_md5(password)
    if user is None or user.password != password_hash:
        return jsonify({"error": "Invalid credentials 2"}), 400
    token = jwt.encode(
        {
            "user": email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=1440),
        },
        cfg.server.secret_key,
    )
    return (
        jsonify(
            {
                "accessToken": token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "deleted_at": user.deleted_at,
                },
            }
        ),
        200,
    )


@app.route("/users/info", methods=["GET"])
def info():
    bearer = request.headers.get("Authorization")
    if not bearer:
        return jsonify({"error": "token is missing"}), 403
    token = bearer.split()[1]
    if not token:
        return jsonify({"error": "token is missing"}), 403
    try:
        email = jwt.decode(token, cfg.server.secret_key, algorithms="HS256")["user"]
    except Exception as error:
        return jsonify({"error": "token is invalid/expired"}), 401
    user = get_user_by_email(cfg.postgres, email)
    if user is None:
        return jsonify({"error": f"user {email} not found"}), 404
    return jsonify(
        {
            "user": {
                "email": user.email,
                "username": user.username,
                "id": user.id,
                "deleted_at": user.deleted_at,
            }
        }
    )


@app.route("/users/logout", methods=["POST"])
def logout():
    return jsonify({}), 200


@app.route("/users/reset", methods=["POST"])
@token_required
def reset():
    return jsonify({}), 200


@app.route("/users/register", methods=["POST"])
def register():
    body = request.get_json()
    username = body.get("username")
    email = body.get("email")
    password = body.get("password")
    if not username:
        return jsonify({"error": "username is missing"}), 400
    if not validate_username(username):
        return jsonify({"error": "username is invalid"}), 400
    if not email:
        return jsonify({"error": "email is missing"}), 400
    if not validate_email(email):
        return jsonify({"error": "email is invalid"}), 400
    if not password:
        return jsonify({"error": "password is missing"}), 400
    if not validate_password(password):
        return jsonify({"error": "password is invalid"}), 400
    if get_user_by_username(cfg.postgres, username) != None:
        return jsonify({"error": "user already exists"}), 400
    user = create_user(cfg.postgres, username, password, email)
    return (
        jsonify(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                }
            }
        ),
        201,
    )


@app.route("/channels/create", methods=["POST"])
@token_required
def new_channel():
    body = request.get_json()
    name = body.get("name")
    if name is None:
        return jsonify({"error": "name is missing"}), 400
    if not validate_name(name):
        return jsonify({"error": "name is invalid"}), 400
    channel = get_channel_by_name(cfg.postgres, name)
    if channel is not None:
        return jsonify({"error": "channel already exists"}), 400
    type = body.get("type")
    if type is None:
        return jsonify({"error": "type is missing"}), 400
    if not validate_name(type):
        return jsonify({"error": "type is invalid"}), 400
    params = body.get("params")
    if not params:
        return jsonify({"error": "params are missing"}), 400
    channel = create_channel(cfg.postgres, params, type, name)
    return (
        jsonify(
            {
                "channel": {
                    "id": channel.id,
                    "type": channel.type,
                    "name": channel.name,
                    "enabled": channel.enabled,
                    "params": channel.params,
                }
            }
        ),
        201,
    )


@app.route("/channels/all", methods=["GET"])
@token_required
def find_all_channels():
    channels = get_all_channels(cfg.postgres)
    return (
        jsonify(
            {
                "channels": [
                    {
                        "id": channel.id,
                        "type": channel.type,
                        "name": channel.name,
                        "enabled": channel.enabled,
                        "params": channel.params,
                    }
                    for channel in channels
                ]
            }
        ),
        200,
    )


@app.route("/channels/<channel_id>", methods=["GET"])
@token_required
def get_channel(channel_id: str):
    if not validate_uuid(channel_id):
        return jsonify({"error": "channel_id is invalid"}), 400
    channel = get_channel_by_id(cfg.postgres, channel_id)
    if channel is None:
        return jsonify({"error": f"channel {channel_id} not found"}), 404
    return (
        jsonify(
            {
                "channel": {
                    "id": channel.id,
                    "enabled": channel.enabled,
                    "type": channel.type,
                    "name": channel.name,
                    "params": channel.params,
                }
            }
        ),
        200,
    )


@app.route("/channels/<channel_id>", methods=["PATCH"])
@token_required
def patch_channel(channel_id: str):
    if not validate_uuid(channel_id):
        return jsonify({"error": "channel_id is invalid"}), 400
    channel_old = get_channel_by_id(cfg.postgres, channel_id)
    if channel_old is None:
        return jsonify({"error": f"channel {channel_id} not found"}), 404
    body = request.get_json()
    params = body.get("params")
    enabled = body.get("enabled")
    update_channel(cfg.postgres, channel_id, params, enabled)
    return jsonify({}), 200


@app.route("/channels/<channel_id>", methods=["DELETE"])
@token_required
def delete_channel(channel_id: str):
    if not validate_uuid(channel_id):
        return jsonify({"error": "channel_id is invalid"}), 400
    channel = get_channel_by_id(cfg.postgres, channel_id)
    if channel is None:
        return jsonify({"error": f"channel {channel_id} not found"}), 404
    update_channel(cfg.postgres, channel_id, None, False)
    return jsonify({}), 200


@app.route("/resources/create", methods=["POST"])
@token_required
def new_resource():
    body = request.get_json()
    url = body.get("url")
    if not url:
        return jsonify({"error": "url is missing"}), 400
    if not validate_url(url):
        return jsonify({"error": "url is invalid"}), 400
    name = body.get("name")
    if not name:
        return jsonify({"error": "name is missing"}), 400
    if not validate_name(name):
        return jsonify({"error": "name is invalid"}), 400
    description = body.get("description")
    if not description:
        description = ""
    if not validate_description(description):
        return jsonify({"error": "description is invalid"}), 400
    keywords = body.get("keywords")
    if keywords is not None and not validate_keywords(keywords):
        return jsonify({"error": "keywords are invalid"}), 400
    interval = body.get("interval")
    if not interval:
        return jsonify({"error": "interval is missing"}), 400
    starts_from = body.get("starts_from")
    if starts_from is not None:
        starts_from = validate_date_time(starts_from)
        if not starts_from:
            return (
                jsonify(
                    {
                        "error": "starts_from is invalid. Expected Unix timestamp (integer)"
                    }
                ),
                400,
            )
    if not validate_interval(interval):
        return jsonify({"error": "interval is invalid"}), 400
    interval = get_interval(interval)
    make_screenshot = False
    sensitivity = body.get("sensitivity")
    if sensitivity:
        make_screenshot = True
    zone_type = None
    polygon = None
    if sensitivity:
        zone_type = body.get("zone_type")
        if not zone_type:
            return jsonify({"error": "zone_type is missing"}), 400
        if zone_type not in ["fullPage", "zone"]:
            return jsonify({"error": "zone_type is invalid"}), 400
        polygon = None
        if zone_type == "zone":
            polygon = body.get("areas")
            if polygon:
                for area in polygon:
                    area["sensitivity"] = sensitivity
                    if not validate_polygon(area):
                        return jsonify({"error": "polygon is invalid"}), 400
        else:
            polygon = {"sensitivity": sensitivity}
    channels = body.get("channels")
    if channels is None:
        return jsonify({"error": "at least one channel should be specified"}), 400
    for channel_id in channels:
        channel = get_channel_by_id(cfg.postgres, channel_id)
        if channel is None:
            return jsonify({"error": f"channel {channel_id} not found"}), 404
    resource = create_resource(
        cfg.postgres,
        url,
        name,
        description,
        keywords,
        interval,
        starts_from,
        make_screenshot,
        polygon,
    )
    for channel_id in channels:
        create_channel_resource(cfg.postgres, channel_id, resource.id)

    create_daemon_cron_job_for_resource(resource, cfg.server)

    # Convert starts_from to Unix timestamp for response
    starts_from_timestamp = (
        int(resource.starts_from.timestamp()) if resource.starts_from else None
    )

    return (
        jsonify(
            {
                "resource": {
                    "id": resource.id,
                    "url": resource.url,
                    "name": resource.name,
                    "description": resource.description,
                    "channels": channels,
                    "keywords": resource.keywords,
                    "interval": resource.interval,
                    "starts_from": starts_from_timestamp,
                    "make_screenshot": resource.make_screenshot,
                    "enabled": resource.enabled,
                    "areas": resource.polygon,
                }
            }
        ),
        201,
    )


@app.route("/resources/<resource_id>", methods=["GET"])
@token_required
def get_resource(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({"error": "resource_id is invalid"}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({"error": f"resource {resource_id} not found"}), 404
    all_channels = get_channel_resource_by_resource_id(cfg.postgres, resource_id)
    active_channels = []
    for channel in all_channels:
        if channel.enabled:
            active_channels.append(channel.channel_id)

    # Convert starts_from to Unix timestamp for response
    starts_from_timestamp = (
        int(resource.starts_from.timestamp()) if resource.starts_from else None
    )

    return (
        jsonify(
            {
                "resource": {
                    "id": resource.id,
                    "url": resource.url,
                    "name": resource.name,
                    "description": resource.description,
                    "channels": active_channels,
                    "keywords": resource.keywords,
                    "interval": resource.interval,
                    "starts_from": starts_from_timestamp,
                    "make_screenshot": resource.make_screenshot,
                    "enabled": resource.enabled,
                    "areas": resource.polygon,
                }
            }
        ),
        200,
    )


@app.route("/resources/<resource_id>", methods=["PATCH"])
@token_required
def patch_resorce(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({"error": "resource_id is invalid"}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({"error": f"resource {resource_id} not found"}), 404
    body = request.get_json()
    description = body.get("description")
    if description is not None and not validate_description(description):
        return jsonify({"error": "description is invalid"}), 400
    keywords = body.get("keywords")
    if keywords is not None and not validate_keywords(keywords):
        return jsonify({"error": "keywords are invalid"}), 400
    interval = body.get("interval")
    if interval is not None:
        if not validate_interval(interval):
            return jsonify({"error": "interval is invalid"}), 400
        interval = get_interval(interval)
    enabled = body.get("enabled")
    polygon = body.get("areas")
    if isinstance(polygon, list):
        polygon[0]['sensitivity'] = resource.polygon[0]['sensitivity']
    else:
        polygon['sensitivity'] = resource.polygon['sensitivity']
    if polygon is None:
        polygon = resource.polygon
    channels = body.get("channels")
    if channels is not None:
        for channel_id in channels:
            if not validate_uuid(channel_id):
                return jsonify({"error": f"channel uuid {channel_id} is invalid"}), 400
            channel = get_channel_by_id(cfg.postgres, channel_id)
            if channel is None:
                return jsonify({"error": f"channel {channel_id} not found"}), 404
    
    sensitivity = body.get("sensitivity")
    if polygon is None and sensitivity is not None:
        return jsonify({"error": "sensitivity and polygon are mutually exclusive"}), 400
    if sensitivity is not None:
        if not isinstance(sensitivity, float) or (sensitivity < 0 or sensitivity > 100):
            return jsonify({"error": "sensitivity is invalid"}), 400
        polygon['sensitivity'] = sensitivity

    # Handle starts_from in PATCH request
    starts_from = body.get("starts_from")
    if starts_from is not None:
        starts_from = validate_date_time(starts_from)
        if not starts_from:
            return (
                jsonify(
                    {
                        "error": "starts_from is invalid. Expected Unix timestamp (integer)"
                    }
                ),
                400,
            )

    update_resource(
        cfg.postgres,
        resource_id,
        description,
        keywords,
        interval,
        enabled,
        polygon,
        starts_from,
    )
    new_resource = get_resource_by_id(cfg.postgres, resource_id)

    if channels is not None:
        update_resource_channels(cfg.postgres, resource_id, channels)

    update_daemon_cron_job_for_resource(new_resource, cfg.server)

    # Convert starts_from to Unix timestamp for response
    starts_from_timestamp = (
        int(new_resource.starts_from.timestamp()) if new_resource.starts_from else None
    )

    return (
        jsonify(
            {
                "resource": {
                    "id": new_resource.id,
                    "url": new_resource.url,
                    "name": new_resource.name,
                    "description": new_resource.description,
                    "channels": channels,
                    "keywords": new_resource.keywords,
                    "interval": new_resource.interval,
                    "starts_from": starts_from_timestamp,
                    "make_screenshot": new_resource.make_screenshot,
                    "enabled": new_resource.enabled,
                    "areas": new_resource.polygon,
                }
            }
        ),
        200,
    )


@app.route("/resources/<resource_id>", methods=["DELETE"])
@token_required
def delete_resource(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({"error": "resource_id is invalid"}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({"error": f"resource {resource_id} not found"}), 404
    update_resource(cfg.postgres, resource_id, None, None, None, False, None)
    resource = get_resource_by_id(cfg.postgres, resource_id)
    update_daemon_cron_job_for_resource(resource, cfg.server)
    return jsonify({}), 200


@app.route("/resources/all", methods=["GET"])
@token_required
def all_resources():
    resources = get_all_resources(cfg.postgres)
    result = []
    for resource in resources:
        all_channels = get_channel_resource_by_resource_id(cfg.postgres, resource.id)
        active_channels = []
        for channel in all_channels:
            if channel.enabled:
                active_channels.append(channel.channel_id)

        # Convert starts_from to Unix timestamp for response
        starts_from_timestamp = (
            int(resource.starts_from.timestamp()) if resource.starts_from else None
        )

        result.append(
            {
                "id": resource.id,
                "url": resource.url,
                "name": resource.name,
                "description": resource.description,
                "channels": active_channels,
                "keywords": resource.keywords,
                "interval": resource.interval,
                "starts_from": starts_from_timestamp,
                "make_screenshot": resource.make_screenshot,
                "enabled": resource.enabled,
                "areas": resource.polygon,
            }
        )
    return jsonify({"resources": result}), 200


@app.route("/add_channel_to_resource/", methods=["POST"])
@token_required
def add_channel_to_resource():
    body = request.get_json()
    resource_id = body.get("resource_id")
    channel_id = body.get("channel_id")
    if not resource_id or not channel_id:
        return jsonify({"error": "resource_id and channel_id are required"}), 400
    if not validate_uuid(resource_id) or not validate_uuid(channel_id):
        return jsonify({"error": "resource_id and channel_id are invalid"}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({"error": f"resource {resource_id} not found"}), 404
    channel = get_channel_by_id(cfg.postgres, channel_id)
    if channel is None:
        return jsonify({"error": f"channel {channel_id} not found"}), 404
    linked_channels = get_channel_resource_by_resource_id(cfg.postgres, resource_id)
    for item in linked_channels:
        if item.channel_id == channel_id and item.enabled:
            return jsonify({"message": "channel already linked to resource"}), 200
    create_channel_resource(cfg.postgres, channel_id, resource_id)
    return jsonify({"message": "channel linked to resource"}), 201


@app.route("/remove_channel_from_resource/", methods=["DELETE"])
@token_required
def remove_channel_from_resource():
    body = request.get_json()
    resource_id = body.get("resource_id")
    channel_id = body.get("channel_id")
    if not resource_id or not channel_id:
        return jsonify({"error": "resource_id and channel_id are required"}), 400
    if not validate_uuid(resource_id) or not validate_uuid(channel_id):
        return jsonify({"error": "resource_id and channel_id are invalid"}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({"error": f"resource {resource_id} not found"}), 404
    channel = get_channel_by_id(cfg.postgres, channel_id)
    if channel is None:
        return (
            jsonify(
                {
                    "error": f"channel {channel_id} never was linked to resource {resource_id}"
                }
            ),
            400,
        )
    if not channel.enabled:
        return (
            jsonify(
                {
                    "message": f"channel {channel_id} is already unlinked from resource {resource_id}"
                }
            ),
            202,
        )
    change_channel_resource_enabled(cfg.postgres, channel_id, resource_id, False)
    return jsonify({}), 200


@app.route("/channels_by_resource/<resource_id>", methods=["GET"])
@token_required
def get_channels_by_resource(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({"error": "resource_id is invalid"}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({"error": f"resource {resource_id} not found"}), 404
    channels = get_channel_resource_by_resource_id(cfg.postgres, resource_id)
    active_channels = []
    for channel in channels:
        if channel.enabled:
            active_channels.append(channel.channel_id)
    return jsonify({"channels": active_channels}), 200


@app.route("/events/<event_id>", methods=["GET"])
@token_required
def get_event(event_id: str):
    if not validate_uuid(event_id):
        return jsonify({"error": "event_id is invalid"}), 400
    event = get_monitoring_event_by_id(cfg.postgres, event_id)
    if event is None:
        return jsonify({"error": f"event {event_id} not found"}), 404
    return jsonify({"event": event}), 200


@app.route("/events/<event_id>", methods=["PATCH"])
@token_required
def update_event(event_id: str):
    if not validate_uuid(event_id):
        return jsonify({"error": "event_id is invalid"}), 400
    event = get_monitoring_event_by_id(cfg.postgres, event_id)
    if event is None:
        return jsonify({"error": f"event {event_id} not found"}), 404
    body = request.get_json()
    status = body.get("status")
    if status is not None and not validate_monitoring_event_status(status):
        return jsonify({"error": "status is invalid"}), 400
    if status in ["CREATED", "NOTIFIED"]:
        return jsonify({"error": "this status cannot be set manually"})
    update_monitoring_event_status(cfg.postgres, event_id, status)
    return jsonify({}), 200


@app.route("/events/<snapshot_id>/screenshot", methods=["GET"])
@token_required
def get_event_snapshot(snapshot_id: str):
    image = get_object(cfg.s3, "images", snapshot_id + ".png")
    if image is None:
        return jsonify({"error": f"screenshot {snapshot_id} not found"}), 404
    image_base64 = base64.b64encode(image).decode("utf-8")
    return jsonify({"image": image_base64}), 200


@app.route("/events/<snapshot_id>/text", methods=["GET"])
@token_required
def get_event_text(snapshot_id: str):
    html = get_object(cfg.s3, "htmls", snapshot_id + ".html")
    if html is None:
        return jsonify({"error": f"snapshot {snapshot_id} not found"}), 404
    text = extract_text_from_html(html)
    return jsonify({"text": text}), 200


@app.route("/events/<snapshot_id>/html", methods=["GET"])
@token_required
def get_event_html(snapshot_id: str):
    html = get_object(cfg.s3, "htmls", snapshot_id + ".html")
    if html is None:
        return jsonify({"error": f"snapshot {snapshot_id} not found"}), 404
    return jsonify({"html": html.decode("utf-8")}), 200


@app.route("/resources/<resource_id>/last_snapshot_id", methods=["GET"])
@token_required
def get_event_last_snapshot_id(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({"error": "resource_id is invalid"}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({"error": f"resource {resource_id} not found"}), 404
    last_snapshot = get_last_snapshot_id(cfg.s3, resource_id)
    return jsonify({"snapshot_id": last_snapshot}), 200


@app.route("/resources/<resource_id>/snapshot_times", methods=["GET"])
@token_required
def get_snapshot_times(resource_id: str):
    if not validate_uuid(resource_id):
        return jsonify({"error": "resource_id is invalid"}), 400
    resource = get_resource_by_id(cfg.postgres, resource_id)
    if resource is None:
        return jsonify({"error": f"resource {resource_id} not found"}), 400
    snapshots = get_snapshot_times_by_resource_id(cfg.s3, resource_id)
    return jsonify(
        {
            "snapshots": [
                {"id": resource_id + "_" + str(snapshot[1]), "time": snapshot[0]}
                for snapshot in snapshots
            ]
        }
    )


@app.route("/screenshot", methods=["POST"])
@token_required
def get_screenshot():
    body = request.get_json()
    url = body.get("url")
    if url is None:
        return jsonify({"error": "url is required"}), 400
    if not validate_url(url):
        return jsonify({"error": "invalid url"}), 400
    screenshot = get_url_image_base_64(url)
    return jsonify({"screenshot": screenshot}), 200


@app.route("/events/filter", methods=["POST"])
@token_required
def get_filtred_events():
    body = request.get_json()
    resource_ids = body.get("resource_ids")
    if resource_ids is not None:
        if type(resource_ids) is not list:
            return jsonify({"error": "resource_ids should be list"}), 400
        for resource_id in resource_ids:
            if not validate_uuid(resource_id):
                return jsonify({"error": "invalid resource_id value"}), 400
    start_time = body.get("start_time")
    if start_time is not None:
        start_time = validate_date_time(start_time)
        if start_time is None:
            return jsonify({"error": "start_time is invalid"}), 400
    end_time = body.get("end_time")
    if end_time is not None:
        end_time = validate_date_time(end_time)
        if end_time is None:
            return jsonify({"error": "end_time is invalid"}), 400
    if start_time is not None and end_time is not None and start_time > end_time:
        return jsonify({"error": "end_time is more than start_time"}), 400
    event_type = body.get("event_type")
    if event_type is not None and event_type not in ["keyword", "image"]:
        return jsonify({"error", "type is invalid"}), 400
    events = filter_monitoring_events(
        cfg.postgres, resource_ids, start_time, end_time, event_type
    )
    return jsonify({"events": events}), 200


@app.route("/report", methods=["POST"])
@token_required
def generate_repot():
    body = request.get_json()
    event_ids = body.get("event_ids")
    snapshot_ids = body.get("snapshot_ids")
    if event_ids is not None:
        if not isinstance(event_ids, list):
            return jsonify({"error": "event_ids should be list"}), 400
        for event_id in event_ids:
            event = get_monitoring_event_by_id(cfg.postgres, event_id)
            if event is None:
                return jsonify({"error": f"event {event_id} not found"}), 404
    if snapshot_ids is not None:
        if not isinstance(snapshot_ids, list):
            return jsonify({"error": "snapshot_ids should be list"}), 400
        for snapshot_id in snapshot_ids:
            if not isinstance(snapshot_id, str):
                return jsonify({"error": "snapshot_ids should be list of strings"}), 400
            if (
                get_object_created_at(cfg.s3, "images", snapshot_id + ".png") is None
                and get_object_created_at(cfg.s3, "htmls", snapshot_id + ".html")
                is None
            ):
                return jsonify({"error": f"snapshot {snapshot_id} not found"}), 404
    filtred_events = filter_monitoring_events_for_report(
        cfg.postgres, snapshot_ids, event_ids
    )
    event_types_by_snapshot = dict()
    if snapshot_ids is not None:
        for snapshot_id in snapshot_ids:
            event_types_by_snapshot[snapshot_id] = {
                "image": False,
                "text": False,
                "resource_id": snapshot_id[:-2],
            }
    for event in filtred_events:
        if event.snapshot_id not in event_types_by_snapshot:
            event_types_by_snapshot[event.snapshot_id] = {
                "image": False,
                "text": False,
                "resource_id": event.resource_id,
            }
        if "image" in event.name:
            event_types_by_snapshot[event.snapshot_id]["image"] = True
        else:
            event_types_by_snapshot[event.snapshot_id]["text"] = True

    csv_output = io.StringIO()
    csv_writer = csv.writer(csv_output)
    csv_writer.writerow(["resource_id", "snapshot_id", "time", "image", "text"])
    for snapshot_id in event_types_by_snapshot.keys():
        snapshot_time = get_object_created_at(cfg.s3, "images", snapshot_id + ".png")
        if snapshot_time is None:
            snapshot_time = get_object_created_at(
                cfg.s3, "htmls", snapshot_id + ".html"
            )
        csv_writer.writerow(
            [
                event_types_by_snapshot[snapshot_id]["resource_id"],
                snapshot_id,
                snapshot_time,
                event_types_by_snapshot[snapshot_id]["image"],
                event_types_by_snapshot[snapshot_id]["text"],
            ]
        )
    csv_content = csv_output.getvalue()
    response = Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=data.csv"},
    )
    return response


@app.route("/events/list", methods=["POST"])
@token_required
def get_events_list():
    body = request.get_json()
    event_ids = body.get("event_ids")
    snapshot_ids = body.get("snapshot_ids")
    if event_ids is not None:
        if not isinstance(event_ids, list):
            return jsonify({"error": "event_ids should be list"}), 400
        for event_id in event_ids:
            event = get_monitoring_event_by_id(cfg.postgres, event_id)
            if event is None:
                return jsonify({"error": f"event {event_id} not found"}), 404
    if snapshot_ids is not None:
        if not isinstance(snapshot_ids, list):
            return jsonify({"error": "snapshot_ids should be list"}), 400
        for snapshot_id in snapshot_ids:
            if not isinstance(snapshot_id, str):
                return jsonify({"error": "snapshot_ids should be list of strings"}), 400
            if (
                get_object_created_at(cfg.s3, "images", snapshot_id + ".png") is None
                and get_object_created_at(cfg.s3, "htmls", snapshot_id + ".html")
                is None
            ):
                return jsonify({"error": f"snapshot {snapshot_id} not found"}), 404
    filtred_events = filter_monitoring_events_for_report(
        cfg.postgres, snapshot_ids, event_ids
    )
    event_types_by_snapshot = dict()
    if snapshot_ids is not None:
        for snapshot_id in snapshot_ids:
            event_types_by_snapshot[snapshot_id] = {
                "image": False,
                "text": False,
                "resource_id": snapshot_id[:-2],
            }
    for event in filtred_events:
        if event.snapshot_id not in event_types_by_snapshot:
            event_types_by_snapshot[event.snapshot_id] = {
                "image": False,
                "text": False,
                "resource_id": event.resource_id,
            }
        if "image" in event.name:
            event_types_by_snapshot[event.snapshot_id]["image"] = True
        else:
            event_types_by_snapshot[event.snapshot_id]["text"] = True

    result = []
    for snapshot_id in event_types_by_snapshot.keys():
        snapshot_time = get_object_created_at(cfg.s3, "images", snapshot_id + ".png")
        if snapshot_time is None:
            snapshot_time = get_object_created_at(
                cfg.s3, "htmls", snapshot_id + ".html"
            )
        result.append(
            {
                "resource_id": event_types_by_snapshot[snapshot_id]["resource_id"],
                "snapshot_id": snapshot_id,
                "snapshot_time": snapshot_time,
                "image_changed": event_types_by_snapshot[snapshot_id]["image"],
                "text_changed": event_types_by_snapshot[snapshot_id]["text"],
            }
        )
    return jsonify({"events": result}), 200


@app.route("/events/all", methods=["GET"])
@token_required
def get_all_events():
    events = filter_monitoring_events(cfg.postgres, None, None, None, None)
    return jsonify({"events": events}), 200


if __name__ == "__main__":
    app.run(host=cfg.server.host, port=cfg.server.port, debug=cfg.server.debug)
