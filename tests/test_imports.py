"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""

def test_import_app():
    from starlink_manager.application import StarlinkManagerApplication
    assert StarlinkManagerApplication

def test_config():
    from starlink_manager.app_config import StarlinkManagerConfig

    config = StarlinkManagerConfig()
    assert isinstance(config.to_dict(), dict)

def test_ui():
    from starlink_manager.app_ui import StarlinkManagerUI
    assert StarlinkManagerUI

def test_state():
    from starlink_manager.app_state import StarlinkManagerState
    assert StarlinkManagerState