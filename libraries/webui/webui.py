import yaml
import os
from libraries import logger
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_user, login_required, logout_user
from .auth import authenticate, get_user_data

web_bp = Blueprint("web", __name__, url_prefix="/web", template_folder="templates", static_folder="static", static_url_path="/static")

log = logger.fileLogger()
log.initialize('WebUI')
log.info("Logging Initialized!")

with open (f"{os.path.dirname(__file__)}/lang/EN_int.yml", 'r') as f:
    lang = yaml.safe_load(f)


@web_bp.route("/", methods=["GET", "POST"])
def web_index():
    return render_template("index.html", lang=lang)

@web_bp.route("/login", methods=["GET", "POST"])
def status():
    return render_template("login.html", lang=lang)

@web_bp.route("/logout", methods=["POST"])
def logout():
    return redirect(url_for("web_index"))

@web_bp.route("/privacy-policy", methods=["GET", "POST"])
def privacy_policy():
    return render_template("privacy_policy.html", lang=lang)

@web_bp.route("/home", methods=["GET"])
def home():
    return render_template("home.html", lang=lang, user_data=get_user_data("User"))

@web_bp.route("/settings", methods=["GET"])
def settings():
    return False