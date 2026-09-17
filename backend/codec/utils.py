import os
import importlib.util

# path where the vxlib.py file is located 
_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "v2xlib")


def load_v2xlib(
    env_var: str = "PYV2XLIB_VENDOR_DIR",
    module_filename: str = "v2xlib.py",
):
    """
    load v2xlib.py 
    """
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
