"""
Dynamically load objects
"""

import inspect
import os
import sys


from .config import register_config, get_actual_base_path

__all__ = [
    'modules_config',
    'load_ref',
    'make_ref',
]


def modules_setup(name, config):
    cfg = config[name]
    for ref in cfg["imports"]:
        base_path = get_actual_base_path(config)
        # print("[load]", ref, base_path)
        load_ref(ref, base_path=base_path)


register_config(
    name="modules",
    default={
        "imports": [],
    },
    setup_callback=modules_setup)

    
def load_ref(obj_reference, paths=None, base_path=None):
    """Loads an object from a python module.

       Parameters
       ----------
       obj_reference: str
           Reference to a python symbol, for instance 'pkg.mdl' to
           load the python module ``pkg.mdl``, or 'pkg.mdl:symbol'
           to load ``symbol`` from the python module ``pkg.mdl``.
           A path can be provided, for instance: '/a/b/pkg.mdl:symbol'.
       paths: str or list
           Search path to be added to ``sys.path``.
       base_path: str
           Base path for relative paths.

       Returns
       -------
       object
           The loaded object.

       Raises
       ------
       ImportError
           If the object cannot be loaded.
    """
    if paths is None:
        paths = []
    else:
        paths = list(paths)
    tokens = obj_reference.rsplit("/", 1)
    if len(tokens) == 1:
        obj_reference = tokens[0]
    else:
        pth, obj_reference = tokens
        paths.append(pth)
    abs_paths = []
    for pth in paths:
        if not os.path.isabs(pth):
            if base_path is None:
                pth = os.path.abspath(pth)
            else:
                pth = os.path.normpath(os.path.join(base_path, pth))
        abs_paths.append(pth)
    tokens = obj_reference.split(":", 1)
    module_name = tokens[0]
    fromlist = module_name.split(".")[:-1]
    old_sys_path = sys.path
    if abs_paths:
        sys.path = abs_paths[:]
        sys.path.extend(old_sys_path)
    try:
        module = __import__(module_name, fromlist=fromlist)
    finally:
        sys.path = old_sys_path
    if len(tokens) == 1:
        obj = module
    else:
        symbol = tokens[1]
        obj = getattr(module, symbol)
    return obj


def make_ref(obj):
    """Makes a reference to the object; the returned string can be used as argument
       to load_obj.

       Parameters
       ----------
       obj: object
           The given object

       Returns
       -------
       str
           The object's reference.
    """
    name = None
    for key in '__qualname__', '__name__':
        val = getattr(obj, key, None)
        if val is not None:
            name = val
            break
    if name is None:
        raise ValueError("cannot make a ref to {!r}: object has no name".format(obj))
    if inspect.ismodule(obj):
        return name
    else:
        module_name = getattr(obj, "__module__", None)
        if module_name is None:
            raise ValueError("cannot make a ref to {!r}: object has no module".format(obj))
        return module_name + ":" + name
