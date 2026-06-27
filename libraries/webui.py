from flask import Blueprint

web_bp = Blueprint("web", __name__, url_prefix="/web")

@web_bp.route("/")
def web_index():
    return "Web module is enabled"

@web_bp.route("/status")
def status():
    return {"success": True, "status": "ok"}