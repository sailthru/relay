import importlib
import logging
log = logging.getLogger('relay.util')


def log_raise(msg, extra={}, err_kls=Exception):
    log.error(msg, extra=extra)
    raise err_kls("%s ||| %s" % (
        msg, ' '.join('='.join([str(k), str(v)]) for k, v in extra.items())))


class InvalidImportPath(Exception):
    pass


def load_obj_from_path(import_path, prefix=None, ld=dict()):
    """
    import a python object from an import path

    `import_path` - a python import path.  For instance:
            mypackage.module.func
        or
            mypackage.module.class
    `prefix` (str) - a value to prepend to the import path
        if it isn't already there.  For instance:
            load_obj_from_path('module.func', prefix='mypackage')
        is the same as
            load_obj_from_path('mypackage.module.func')
    `ld` (dict) key:value data to pass to the logger if an error occurs
    """
    if prefix and not import_path.startswith(prefix):
        import_path = '.'.join([prefix, import_path])

    log.debug(
        'attempting to load a python object from an import path',
        extra=dict(import_path=import_path, **ld))
    try:
        mod = importlib.import_module(import_path)
        return mod  # yay, we found a module.  return it
    except:
        pass  # try to extract an object from a module
    try:
        path, obj_name = import_path.rsplit('.', 1)
    except ValueError:
        log_raise(
            ("import path needs at least 1 period in your import path."
             " An example import path is something like: module.obj"),
            dict(import_path=import_path, **ld), InvalidImportPath)
    try:
        mod = importlib.import_module(path)
    except ImportError:
        newpath = path.replace(prefix, '', 1).lstrip('.')
        log.debug(
            "Could not load import path.  Trying a different one",
            extra=dict(oldpath=path, newpath=newpath))
        path = newpath
        mod = importlib.import_module(path)
    try:
        obj = getattr(mod, obj_name)
    except AttributeError:
        log_raise(
            ("object does not exist in given module."
             " Your import path is not"
             " properly defined because the given `obj_name` does not exist"),
            dict(import_path=path, obj_name=obj_name, **ld),
            InvalidImportPath)
    return obj


def coroutine(func):
    def f(*args, **kwargs):
        g = func(*args, **kwargs)
        next(g)
        return g
    return f
