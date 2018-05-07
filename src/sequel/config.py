"""
Configuration
"""

import json
import os
import random
import numpy as np


__all__ = [
    "get_rcdir",
    "get_config_filename",
    "default_config",
    "get_config",
    "get_actual_config_filename",
    "get_actual_base_path",
    "set_config",
    "load_config",
    "dump_config",
    "write_config",
    "reset_config",
    "update_config",
    "setup_config",
]

RCDIR = os.path.normpath(os.path.abspath(os.path.join(os.path.expanduser("~"), ".sequel")))
CONFIG_FILENAME = os.path.join(RCDIR, "sequel.config")

CONFIG = None

CONFIG_REGISTRY = {}

def register_config(name, default, setup_callback=None):
    CONFIG_REGISTRY[name] = (default, setup_callback)


def get_rcdir():
    return RCDIR


def get_config_filename():
    return CONFIG_FILENAME


def _setup_sequel_config(name, config):
    sequel_config = config[name]
    random_seed = sequel_config["random_seed"]
    random.seed(random_seed)
    np.random.seed(random_seed)


register_config(
    name="sequel",
    default={
        "random_seed": 2,
    },
    setup_callback=_setup_sequel_config)


def default_config():
    config =  {
        "__internal__": {"filename": None},
    }
    for name, (sub_config, setup) in CONFIG_REGISTRY.items():
        config[name] = sub_config
    return config


def setup_config(config=None):
    if config is None:
        config = get_config()
    for name in config:
        setup_callback = CONFIG_REGISTRY.get(name, (None, None))[1]
        if setup_callback:
            setup_callback(name, config)


def set_config(config=None):
    if config is None:
        config = load_config()
    global CONFIG
    CONFIG = config


def get_config():
    if CONFIG is None:
        set_config()
    return CONFIG
    
    
def get_actual_config_filename(config=None):
    if config is None:
        config = get_config()
    return config["__internal__"]["filename"]


def get_actual_base_path(config=None):
    filename = get_actual_config_filename(config)
    if filename is None:
        return os.getcwd()
    else:
        return os.path.dirname(os.path.normpath(os.path.abspath(filename)))


def make_abs_path(pathname, config=None):
    if config is None:
        config = get_config()
    if not os.path.isabs(pathname):
        config_filename = get_actual_config_filename(config)
        if filename is None:
            pathname = os.path.abspath(pathname)
        else:
            dirname = os.path.dirname(os.path.abspath(config_filename))
            pathname = os.path.join(dirname, pathname)
    return pathname


def reset_config():
    write_config(default_config(), None)


def load_config(filename=None):
    if filename is None and os.path.exists(get_config_filename()):
        filename = get_config_filename()
    data = default_config()
    if filename:
        with open(filename, "r") as fp:
            data.update(json.load(fp))
        data["__internal__"]["filename"] = os.path.abspath(filename)
    return data


def write_config(config, filename=None):
    if filename is None:
        filename = get_config_filename()
    dump_config(config, filename)


def dump_config(config, filename=None):
    config = config.copy()
    config.pop("__internal__", None)
    json_data = json.dumps(config, indent=4, sort_keys=True)
    if filename is None:
        print(json_data)
    elif isinstance(filename, str):
        dirname = os.path.dirname(os.path.abspath(filename))
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, "w") as file:
            file.write(json_data)
    else:
        raise TypeError("invalid filename {!r}".format(filename))


def update_config(config, key, value):
    tokens = [x.strip() for x in key.split(".")]
    if tokens:
        cfg = config
        for token in tokens[:-1]:
            cfg = cfg.setdefault(token, {})
        cfg[tokens[-1]] = value
