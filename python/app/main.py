from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

from .api import health, members
from .config import config
from .errors import ApiException
from .openapi_info import CONTACT, DESCRIPTION

app = FastAPI(
    title="Ramblers Salesforce API - Python reference server",
    version="0.4.0",
    description=DESCRIPTION,
    contact=CONTACT,
    servers=[{"url": config.public_base_url}],
)

if config.auth_mode == "none":
    logging.getLogger(__name__).warning(
        "AUTH_MODE=none: inbound authentication is disabled (demo / local only). "
        "Set AUTH_MODE=entra in production."
    )


@app.exception_handler(ApiException)
async def _api_exception_handler(_request: Request, exc: ApiException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response().model_dump(by_alias=True, exclude_none=True),
    )


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


app.include_router(health.router)
app.include_router(members.router)
