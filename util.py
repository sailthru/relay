import importlib
import logging
log = logging.getLogger('relay.util')


def log_raise(msg, extra={}, err_kls=Exception):
    log(msg, extra=extra)
    raise err_kls(msg)


class InvalidImportPath(Exception):
    pass


def load_obj_from_path(import_path, ld=dict()):
    """
    import a python object from an import path like:

        mypackage.module.func
        or
        mypackage.module.class

    """
    log.debug(
        'attempting to load a python object from an import path',
        extra=dict(import_path=import_path, **ld))
    try:
        path, obj_name = import_path.rsplit('.', 1)
    except ValueError:
        log_raise(
            ("import path needs at least 1 period in your import path."
             " An example import path is something like: module.obj"),
            dict(import_path=import_path, **ld), InvalidImportPath)
    mod = importlib.import_module(path)
    try:
        obj = getattr(mod, obj_name)
    except AttributeError:
        log_raise(
            ("object does not exist in given module."
             " Your import path is not"
             " properly defined because the given `obj_name` does not exist"),
            dict(import_path=import_path, obj_name=obj_name, **ld),
            InvalidImportPath)
    return obj