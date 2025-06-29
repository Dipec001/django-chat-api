from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async


class CustomResponseMiddleware(MiddlewareMixin):
    """
    Middleware to wrap all DRF responses in a consistent format.
    """

    def process_response(self, request, response):
        # Exclude browsable API, Swagger docs, etc.
        excluded_paths = ["/swagger/", "/docs/", "/admin/", "/redoc/"]
        if any(path in request.path for path in excluded_paths):
            return response

        if hasattr(response, "data") and isinstance(response.data, dict):
            is_success = 200 <= response.status_code < 300
            data = {
                "success": is_success,
                "data": response.data if is_success else None,
                "errors": response.data if not is_success else None,
                "status": response.status_code,
            }
            return JsonResponse(data, status=response.status_code)
        
        return response


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        from rest_framework_simplejwt.tokens import UntypedToken
        from django.contrib.auth.models import AnonymousUser

        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]

        scope["user"] = AnonymousUser()

        if token:
            try:
                validated_token = UntypedToken(token)
                user = await self.get_user_from_token(validated_token)
                scope["user"] = user
            except Exception:
                pass  # keep user as AnonymousUser

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, validated_token):
        from rest_framework_simplejwt.authentication import JWTAuthentication
        jwt_auth = JWTAuthentication()
        return jwt_auth.get_user(validated_token)
