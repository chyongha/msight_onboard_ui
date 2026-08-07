import os
import importlib.util

# This file lives at msight_onboard_ui/backend/codec/utils.py, so three
# levels up is the project root — where v2xlib.py actually sits today.
# Computed relative to this file rather than hardcoded as an absolute
# path, so it still resolves correctly on any machine this runs on.
_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "v2xlib")


def load_v2xlib(
    env_var: str = "PYV2XLIB_VENDOR_DIR",
    module_filename: str = "v2xlib.py",
):
    """
    Load vendor-provided v2xlib.py from a directory specified by an
    environment variable, falling back to the project root (where it
    lives today) if the env var isn't set.

    Usage:
        v2xlib = load_v2xlib()
    """
    # Falls back to _PROJECT_ROOT, not None, so PYV2XLIB_VENDOR_DIR no
    # longer needs to be set by hand for the common case (v2xlib.py
    # sitting right in the project folder). Still fully overridable via
    # the env var if v2xlib.py ever needs to live somewhere else (e.g. a
    # real deployment that doesn't want this huge generated file checked
    # into version control at all).
    vendor_dir = os.environ.get(env_var, _PROJECT_ROOT)

    module_path = os.path.join(vendor_dir, module_filename)
    if not os.path.isfile(module_path):
        raise FileNotFoundError(f"Vendor module file not found: {module_path}")

    spec = importlib.util.spec_from_file_location("v2xlib_vendor", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to create import spec for: {module_path}")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
