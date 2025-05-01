from flask import (
    Flask,
    redirect,
    url_for,
    request,
    flash
)
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)
from models import (
    db,
    User,
    Resource,
    Channel,
    ChannelResource,
    MonitoringEvent,
    MonitoringEventStatus
)
import os
from dataclasses import dataclass
import yaml
import hashlib

@dataclass
class PostgresConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

config_file = os.getenv("CONFIG_FILE", "config.yaml")
with open(config_file, "r") as file:
    data = yaml.safe_load(file)
cfg = PostgresConfig(**data["postgres"])

app = Flask(__name__)
app.config['SECRET_KEY'] = data['server']['secret_key']
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.database}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class UserModelView(AdminModelView):
    column_list = ['id', 'name', 'email', 'deleted_at']
    form_excluded_columns = ['password']
    column_searchable_list = ['name', 'email']
    column_filters = ['deleted_at']
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.password = generate_password_hash(form.password.data)


class ResourceModelView(AdminModelView):
    column_list = ['id', 'name', 'url', 'enabled', 'make_screenshot', 'interval', 'starts_from']
    column_searchable_list = ['name', 'url']
    column_filters = ['enabled', 'make_screenshot']
    form_widget_args = {
        'monitoring_polygon': {
            'rows': 10
        }
    }


class ChannelModelView(AdminModelView):
    column_list = ['id', 'name', 'type', 'enabled']
    column_searchable_list = ['name', 'type']
    column_filters = ['enabled', 'type']
    form_widget_args = {
        'params': {
            'rows': 10
        }
    }


class ChannelResourceModelView(AdminModelView):
    column_list = ['channel_id', 'resource_id', 'enabled']
    column_filters = ['enabled']


class MonitoringEventModelView(AdminModelView):
    column_list = ['id', 'name', 'resource_id', 'created_at', 'status']
    column_searchable_list = ['name']
    column_filters = ['status', 'created_at']


admin = Admin(app, name='Admin Panel', template_mode='bootstrap4')
admin.add_view(UserModelView(User, db.session))
admin.add_view(ResourceModelView(Resource, db.session))
admin.add_view(ChannelModelView(Channel, db.session))
admin.add_view(ChannelResourceModelView(ChannelResource, db.session))
admin.add_view(MonitoringEventModelView(MonitoringEvent, db.session))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.password == hashlib.md5(password.encode()).hexdigest() and user.is_active():
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.index'))
        
        flash('Invalid email or password')
    
    return '''
    <form method="post">
        <p>Email: <input type="email" name="email" required></p>
        <p>Password: <input type="password" name="password" required></p>
        <p><input type="submit" value="Login"></p>
    </form>
    '''


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
def index():
    return redirect(url_for('admin.index'))


if __name__ == '__main__':
    app.run(host=data['server']['host'], debug=True, port=data['server']['admin_panel_port'])
