from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

from .config import settings

oauth = OAuth(Config(environ={"GOOGLE_CLIENT_ID": settings.google_client_id, "GOOGLE_CLIENT_SECRET": settings.google_client_secret}))
if settings.google_client_id and settings.google_client_secret:
    oauth.register(name="google", client_id=settings.google_client_id, client_secret=settings.google_client_secret, server_metadata_url="https://accounts.google.com/.well-known/openid-configuration", client_kwargs={"scope": "openid email profile"})


def is_configured() -> bool:
    return bool(settings.google_client_id and settings.google_client_secret)
