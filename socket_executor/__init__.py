import os.path
def get_static_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")