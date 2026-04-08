from __future__ import annotations

from typing import Any

import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError, RevokedIdTokenError
from firebase_admin.exceptions import FirebaseError

from app.auth.models import UserContext
from app.core.config import Settings
from app.core.exceptions import AuthenticationError


class FirebaseTokenVerifier:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _get_or_create_app(self) -> Any:
        try:
            return firebase_admin.get_app(self._settings.firebase_app_name)
        except ValueError:
            credential = (
                credentials.Certificate(self._settings.firebase_credentials_path)
                if self._settings.firebase_credentials_path
                else credentials.ApplicationDefault()
            )
            options: dict[str, str] = {}
            if self._settings.firebase_project_id:
                options["projectId"] = self._settings.firebase_project_id
            return firebase_admin.initialize_app(
                credential=credential,
                options=options or None,
                name=self._settings.firebase_app_name,
            )

    def verify_token(self, token: str) -> UserContext:
        if not token:
            raise AuthenticationError(
                code="UNAUTHORIZED",
                message="Invalid or missing authentication token",
            )

        try:
            firebase_app = self._get_or_create_app()
            decoded = auth.verify_id_token(token, app=firebase_app)
        except ExpiredIdTokenError as exc:
            raise AuthenticationError(
                code="TOKEN_EXPIRED",
                message="Authentication token has expired",
            ) from exc
        except InvalidIdTokenError as exc:
            raise AuthenticationError(
                code="INVALID_TOKEN",
                message="Invalid or missing authentication token",
            ) from exc
        except RevokedIdTokenError as exc:
            raise AuthenticationError(
                code="INVALID_TOKEN",
                message="Authentication token has been revoked",
            ) from exc
        except (ValueError, FirebaseError) as exc:
            raise AuthenticationError(
                code="INVALID_TOKEN",
                message="Unable to verify authentication token",
            ) from exc

        return UserContext(uid=decoded["uid"], email=decoded.get("email"))
