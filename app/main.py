import logging
import os

import coloredlogs
from starlette.applications import Starlette

from app.routes import routes

logger = logging.getLogger(__name__)
coloredlogs.install(level="INFO")

app = Starlette(
    on_startup=[lambda: print("Server Ready")],
    on_shutdown=[lambda: print("Server Shutting Down")],
    routes=routes,
    debug=os.environ.get("ENVIRONMENT", "production") == "development",
)
