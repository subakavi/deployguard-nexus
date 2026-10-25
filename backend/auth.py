"""
Amazon Cognito (hosted login) authentication for DeployGuard Nexus.

Authentication is OFF unless AUTH_ENABLED=true, so local development and
the CI test-suite keep working without any AWS configuration.

Required environment variables when AUTH_ENABLED=true:
    FLASK_SECRET_KEY      long random string (signs the session cookie)
    COGNITO_USER_POOL_ID  e.g. ap-southeast-2_XXXXXXXXX
    COGNITO_CLIENT_ID     app client id (no client secret)
    COGNITO_DOMAIN        hosted-UI domain, without https://
    APP_BASE_URL          e.g. https://deployguard-subakavi.duckdns.org
    AWS_REGION            e.g. ap-southeast-2
"""

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from functools import wraps

from flask import Blueprint, g, jsonify, redirect, request, session

auth_bp = Blueprint("auth", __name__)

_jwks_client = None


def auth_enabled():
    return os.getenv("AUTH_ENABLED", "false").lower() == "true"


def _cfg(name):
    return os.getenv(name, "")


def _base_url():
    return _cfg("APP_BASE_URL").rstrip("/")


def _issuer():
    return (
        f"https://cognito-idp.{_cfg('AWS_REGION')}"
        f".amazonaws.com/{_cfg('COGNITO_USER_POOL_ID')}"
    )


def current_user():
    return session.get("user")


# ---------------------------------------------------------
# DECORATORS
# ---------------------------------------------------------

def login_required(view):
    """API routes: return 401 JSON when not logged in."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not auth_enabled():
            g.user = None
            return view(*args, **kwargs)

        user = current_user()
        if not user:
            return jsonify({
                "error": "Authentication required",
                "login": "/login"
            }), 401

        g.user = user
        return view(*args, **kwargs)

    return wrapper


def page_login_required(view):
    """Page routes: redirect to the login page when not logged in."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not auth_enabled():
            g.user = None
            return view(*args, **kwargs)

        user = current_user()
        if not user:
            return redirect("/login")

        g.user = user
        return view(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------
# COGNITO HELPERS
# ---------------------------------------------------------

def _exchange_code(code):
    """Swap the one-time login code for tokens (server to Cognito, TLS)."""

    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "client_id": _cfg("COGNITO_CLIENT_ID"),
        "code": code,
        "redirect_uri": _base_url() + "/auth/callback"
    }).encode("utf-8")

    req = urllib.request.Request(
        f"https://{_cfg('COGNITO_DOMAIN')}/oauth2/token",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _verify_id_token(id_token):
    """Verify signature, issuer, audience and expiry of the ID token."""

    global _jwks_client

    import jwt
    from jwt import PyJWKClient

    if _jwks_client is None:
        _jwks_client = PyJWKClient(
            _issuer() + "/.well-known/jwks.json"
        )

    signing_key = _jwks_client.get_signing_key_from_jwt(id_token)

    claims = jwt.decode(
        id_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=_cfg("COGNITO_CLIENT_ID"),
        issuer=_issuer()
    )

    if claims.get("token_use") != "id":
        raise ValueError("Not an ID token")

    return claims


# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

@auth_bp.route("/login")
def login():

    if not auth_enabled():
        return redirect("/")

    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state

    query = urllib.parse.urlencode({
        "client_id": _cfg("COGNITO_CLIENT_ID"),
        "response_type": "code",
        "scope": "openid email",
        "redirect_uri": _base_url() + "/auth/callback",
        "state": state
    })

    return redirect(
        f"https://{_cfg('COGNITO_DOMAIN')}/oauth2/authorize?{query}"
    )


@auth_bp.route("/auth/callback")
def callback():

    if not auth_enabled():
        return redirect("/")

    if request.args.get("error"):
        return jsonify({
            "error": "Login was not completed",
            "detail": request.args.get("error_description", "")
        }), 400

    code = request.args.get("code")
    state = request.args.get("state")
    expected_state = session.pop("oauth_state", None)

    if not code or not state or state != expected_state:
        return jsonify({"error": "Invalid login state"}), 400

    try:
        tokens = _exchange_code(code)
        claims = _verify_id_token(tokens["id_token"])
    except Exception as error:
        print(f"Login failed: {error}")
        return jsonify({"error": "Login verification failed"}), 401

    email = (claims.get("email") or "").lower()

    if not email or not claims.get("email_verified", False):
        return jsonify({"error": "A verified email is required"}), 403

    session.clear()
    session["user"] = {"sub": claims["sub"], "email": email}

    # Subscribe this user's email to their own alerts (once confirmed
    # by the user through the standard AWS confirmation email).
    try:
        from notification_manager import subscribe_user_email
        subscribe_user_email(email)
    except Exception as error:
        print(f"Alert subscription skipped: {error}")

    return redirect("/")


@auth_bp.route("/logout")
def logout():

    session.clear()

    if not auth_enabled():
        return redirect("/")

    query = urllib.parse.urlencode({
        "client_id": _cfg("COGNITO_CLIENT_ID"),
        "logout_uri": _base_url() + "/"
    })

    return redirect(
        f"https://{_cfg('COGNITO_DOMAIN')}/logout?{query}"
    )


@auth_bp.route("/auth/me")
def me():

    if not auth_enabled():
        return jsonify({"authEnabled": False})

    user = current_user()

    if not user:
        return jsonify({"error": "Authentication required"}), 401

    return jsonify({"authEnabled": True, "email": user["email"]})