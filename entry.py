import uvicorn
from uvicorn.config import LOGGING_CONFIG

LOG_FILE = "app.log"

if __name__ == "__main__":
    # This configuration ensures that all loggers, including the root logger
    # used by your application, will output messages at the 'trace' level.
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(levelprefix)s %(asctime)s - %(message)s"
    LOGGING_CONFIG["formatters"]["access"]["fmt"] = '%(levelprefix)s %(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s'

    # Add a file handler to the logging configuration
    LOGGING_CONFIG["handlers"]["file"] = {
        "formatter": "default",
        "class": "logging.handlers.RotatingFileHandler",
        "filename": LOG_FILE,
        "maxBytes": 1024 * 1024 * 5,  # 5 MB
        "backupCount": 3,
    }

    # Update loggers to use the new file handler in addition to the default console handler
    # The 'uvicorn.error' logger does not have a 'handlers' key by default, so we create it.
    LOGGING_CONFIG["loggers"]["uvicorn"]["handlers"].append("file")
    LOGGING_CONFIG["loggers"]["uvicorn.error"]["handlers"] = ["default", "file"]
    LOGGING_CONFIG["loggers"]["uvicorn.access"]["handlers"].append("file")

    # Configure the root logger to capture application-level logs
    LOGGING_CONFIG["loggers"][""] = {
        "handlers": ["default", "file"],
        "level": "DEBUG",
    }

    uvicorn.run(
        "login_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="trace",
        log_config=LOGGING_CONFIG,
    )
