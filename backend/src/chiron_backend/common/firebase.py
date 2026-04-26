import json
import logging

import firebase_admin
from firebase_admin import credentials

from chiron_backend.common.config import get_settings

logger = logging.getLogger(__name__)


def initialize_firebase() -> None:
    settings = get_settings()

    if not settings.firebase_database_url:
        logger.warning("Firebase database URL is not set. Realtime DB might not work correctly.")

    try:
        cred = None
        if settings.firebase_service_account_json:
            try:
                cert_dict = json.loads(settings.firebase_service_account_json)
                cred = credentials.Certificate(cert_dict)
                logger.info("Initialized Firebase credentials from JSON string.")
            except Exception as e:
                logger.error(f"Failed to parse firebase_service_account_json: {e}")
        elif settings.firebase_credentials_path:
            try:
                cred = credentials.Certificate(settings.firebase_credentials_path)
                logger.info(f"Initialized Firebase credentials from path: {settings.firebase_credentials_path}")
            except Exception as e:
                logger.error(f"Failed to load firebase credentials from path {settings.firebase_credentials_path}: {e}")

        if cred is None:
            logger.warning("No Firebase credentials provided. Attempting to initialize without explicit credentials.")
            firebase_admin.initialize_app(
                options={"databaseURL": settings.firebase_database_url}
            )
        else:
            firebase_admin.initialize_app(
                cred,
                options={"databaseURL": settings.firebase_database_url}
            )
        logger.info("Firebase application initialized successfully.")
    except ValueError as e:
        if "The default Firebase app already exists" in str(e):
            logger.info("Firebase application was already initialized.")
        else:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise
