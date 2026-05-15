from flask import Flask, render_template, session

from config import Config
from models import db, User


def create_app():
    app = Flask(__name__,
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    app.config.from_object(Config)

    db.init_app(app)

    @app.before_request
    def validate_session():
        if "user_id" in session:
            if not db.session.get(User, session["user_id"]):
                session.clear()

    from routes.auth import auth_bp
    from routes.check import check_bp
    from routes.results import results_bp
    from routes.groups import groups_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(check_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(groups_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", debug=False)
