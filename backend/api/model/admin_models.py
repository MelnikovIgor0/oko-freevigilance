import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    JSONB
)
import enum

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    deleted_at = db.Column(db.DateTime)
    
    def is_active(self):
        return self.deleted_at is None
    
    def get_id(self):
        return self.id


class Resource(db.Model):
    __tablename__ = 'resources'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(1024))
    key_words = db.Column(ARRAY(db.String(255)))
    interval = db.Column(db.String(255), nullable=False)
    starts_from = db.Column(db.DateTime)
    make_screenshot = db.Column(db.Boolean, nullable=False)
    enabled = db.Column(db.Boolean, nullable=False)
    monitoring_polygon = db.Column(JSONB)
    
    channels = db.relationship('Channel', secondary='channel_resource', back_populates='resources')


class Channel(db.Model):
    __tablename__ = 'channels'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    params = db.Column(JSONB, nullable=False)
    enabled = db.Column(db.Boolean, nullable=False)
    
    resources = db.relationship('Resource', secondary='channel_resource', back_populates='channels')


class ChannelResource(db.Model):
    __tablename__ = 'channel_resource'
    
    channel_id = db.Column(db.String(36), db.ForeignKey('channels.id'), primary_key=True)
    resource_id = db.Column(db.String(36), db.ForeignKey('resources.id'), primary_key=True)
    enabled = db.Column(db.Boolean, nullable=False)


class MonitoringEventStatus(enum.Enum):
    CREATED = "CREATED"
    NOTIFIED = "NOTIFIED"
    WATCHED = "WATCHED"
    REACTED = "REACTED"


class MonitoringEvent(db.Model):
    __tablename__ = 'monitoring_events'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    snapshot_id = db.Column(db.String(46), nullable=False)
    resource_id = db.Column(db.String(36), db.ForeignKey('resources.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.Enum(MonitoringEventStatus), nullable=False)
    
    resource = db.relationship('Resource')
