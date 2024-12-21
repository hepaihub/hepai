
import httpx
from .openai_api.adapted_openai._exceptions import APIStatusError


class HAPIStatusError(APIStatusError):
    response: httpx.Response
    status_code: int
    request_id: str | None

    def __init__(self, message: str, *, response: httpx.Response, body: object | None) -> None:
        super().__init__(message, response=response, body=body)

