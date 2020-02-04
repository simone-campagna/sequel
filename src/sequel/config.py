"""
Configuration
"""

import collections
import copy
import functools
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile

from .lazy import numpy


__all__ = [
    "get_rcdir",
    "get_config_filename",
    "default_config",
    "get_config",
    "get_rl_init_filename",
    "get_rl_history_filename",
    "get_rl_quiz_history_filename",
    "get_actual_config_filename",
    "get_actual_base_path",
    "set_config",
    "load_config",
    "dump_config",
    "write_config",
    "reset_config",
    "update_config",
    "get_config_key",
    "setup_config",
    "show_config",
]

RCDIR = Path.home().joinpath(".sequel")
CONFIG_FILENAME = RCDIR.joinpath("sequel.config")
RL_INIT_FILENAME = RCDIR.joinpath("sequel.rl-init")
RL_HISTORY_FILENAME = RCDIR.joinpath("sequel.rl-history")
RL_QUIZ_HISTORY_FILENAME = RCDIR.joinpath("sequel.rl-quiz-history")

CONFIG = None

CONFIG_REGISTRY = {}


def get_rl_history_filename():
    return RL_HISTORY_FILENAME


def get_rl_quiz_history_filename():
    return RL_QUIZ_HISTORY_FILENAME


def get_rl_init_filename():
    return RL_INIT_FILENAME


def register_config(name, default, setup_callback=None):
    CONFIG_REGISTRY[name] = (default, setup_callback)


def get_rcdir():
    return RCDIR


def get_config_filename():
    return CONFIG_FILENAME


def _setup_sequel_config(name, config):
    sequel_config = config[name]
    random_seed = sequel_config["random_seed"]
    if random_seed is not None:
        random.seed(random_seed)
        numpy.module().random.seed(random_seed)


register_config(
    name="sequel",
    default={
        "editor": "vim",
        "random_seed": None,
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
        return Path.cwd()
    else:
        return Path(filename).resolve()


def make_abs_path(pathname, config=None):
    if config is None:
        config = get_config()
    pathname = Path(pathname)
    if not pathname.is_absolute():
        config_filename = get_actual_config_filename(config)
        if filename is None:
            pathname = pathname.absolute()
        else:
            dirname = config_filename.parent
            pathname = dirname.joinpath(pathname)
    return pathname


def reset_config():
    config = default_config()
    write_config(config, None)
    return config


def load_config(filename=None):
    if filename is None and get_config_filename().exists():
        filename = get_config_filename()
    data = default_config()
    if filename:
        with open(filename, "r") as fp:
            data.update(json.load(fp))
        data["__internal__"]["filename"] = filename.resolve()
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
        filename = Path(filename)
        dirname = filename.absolute().parent
        if not dirname.is_dir():
            dirname.mkdir(parents=True)
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


def merge_config(config, cfg):
    for key, value in cfg.items():
        if key not in config:
            raise KeyError(key)
        if isinstance(key, collections.Mapping):
            merge_config(config[key], value)
        else:
            config[key] = value


def get_config_key(config, key):
    tokens = [x.strip() for x in key.split(".")]
    val = config
    for token in tokens:
        val = val[token]
    return val


def get_config_key(config, key):
    tokens = [x.strip() for x in key.split(".")]
    if tokens:
        cfg = config
        for token in tokens[:-1]:
            cfg = cfg.setdefault(token, {})
        return cfg[tokens[-1]]


@functools.singledispatch
def yield_config_items(value, key, prefix):
    yield (key, value)


@yield_config_items.register(collections.abc.Mapping)
def _(value, key, prefix):
    for skey, svalue in value.items():
        sk = prefix + skey
        sp = sk + '.'
        yield from yield_config_items(svalue, sk, sp)


@yield_config_items.register(list)
@yield_config_items.register(tuple)
@yield_config_items.register(set)
def _(value, key, prefix):
    for scount, svalue in enumerate(value):
        sk = "{}[{}]".format(prefix, scount)
        sp = sk + '.'
        yield from yield_config_items(svalue, sk, sp)


def get_config_items(config=None, keys=None):
    if config is None:
        config = get_config()
    config = config.copy()
    config.pop("__internal__", None)
    if keys:
        for key in keys:
            yield from yield_config_items(get_config_key(config, key), key, key + '.')
    else:
        yield from yield_config_items(config, '', '')


def show_config(config=None, keys=None, prefix='', print_function=print, sort_keys=False):
    kviter = get_config_items(config=config, keys=keys)
    if sort_keys:
        kviter = sorted(kviter, key=lambda x: x[0])
    for key, value in kviter:
        print_function("{} = {!r}".format(key, value))


def edit_config(config=None):
    if config is None:
        config = get_config()
    with tempfile.TemporaryDirectory() as tmpd:
        tmpd = Path(tmpd)
        tmpf = tmpd.joinpath("sequel.config")
        write_config(config, tmpf)
        returncode = subprocess.call([config['sequel']['editor'], tmpf])
        if returncode == 0:
            return load_config(tmpf)
        else:
            print("ERR: edit command failed", file=sys.stderr)
            return config
