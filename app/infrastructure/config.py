import os


class Settings:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./randomgift.db")
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    frontend_after_login = os.getenv("FRONTEND_AFTER_LOGIN", "http://localhost:3000/dashboard")
    frontend_verification_url = os.getenv("FRONTEND_VERIFICATION_URL", "http://localhost:3000/verify-email")
    verification_base_url = os.getenv("VERIFICATION_BASE_URL", "http://localhost:8000/api/auth/verify-email")
    mail_host = os.getenv("MAIL_HOST", "localhost")
    mail_port = int(os.getenv("MAIL_PORT", "1025"))
    mail_from = os.getenv("MAIL_FROM", "no-reply@randomgift.local")
    jwt_secret_key = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_TO_A_LONG_RANDOM_SECRET_BEFORE_DEPLOYMENT")
    cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")


settings = Settings()
