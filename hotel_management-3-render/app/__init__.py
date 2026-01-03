from flask import Flask
from .config import Config
from .extensions import db, login_manager
import os  
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Import blueprints INSIDE the function
    from .routes.auth_routes import auth_bp
    from .routes.menu_routes import menu_bp
    from .routes.order_routes import order_bp
    from .routes.employee_routes import employee_bp
    from .routes.billing_routes import billing_bp
    from .routes.inventory_routes import inventory_bp
    from .routes.report_routes import report_bp
    from .routes.dashboard_routes import dashboard_bp
    from .routes.attendance_routes import attendance_bp

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(attendance_bp)

    # Tables create only in development ya manual migration mein
    # Production mein db.create_all() mat chalao — flask-migrate use karo
    if os.getenv('FLASK_ENV') == 'development':
        with app.app_context():
            db.create_all()
            # Default admin user (sirf development mein)
            from .models.user import User, Role
            from werkzeug.security import generate_password_hash

            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', role=Role.ADMIN)
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()

    return app
