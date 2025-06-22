from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

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
