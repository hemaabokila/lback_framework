import json
from typing import Any, Dict, Optional

from lback.core.response import Response


def json_response(data: Any, status: int = 200, headers: Optional[Dict[str, str]] = None) -> Response:
    """
    Helper to return JSON responses with appropriate headers.
    """
    if headers is None:
        headers = {}
    
    headers['Content-Type'] = 'application/json'
    
    response = Response(body=json.dumps(data).encode('utf-8'), headers=headers)
    response.status_code = status 
    return response
