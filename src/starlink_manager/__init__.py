from pydoover.docker import run_app

from .application import StarlinkManagerApplication
from .app_config import StarlinkManagerConfig

def main():
    """
    Run the application.
    """
    run_app(StarlinkManagerApplication(config=StarlinkManagerConfig()))
