import os
from functools import wraps
from multiprocessing.dummy import Pool as ThreadPool
import json
from datetime import date, datetime
import six
import csv
import hashlib
from importlib import import_module
from pkgutil import iter_modules
import time


def decorator_time(func):
    def wrapper(*args, **kwargs):
        before = time.time()
        ret = func(*args, **kwargs)
        print(str(time.time() - before))
        return ret
    return wrapper


def decorator_time2(t):
    def wrapper1(func):
        def wrapper2(*args, **kwargs):
            before = time.time()
            ret = func(*args, **kwargs)
            if time.time() - before < t:
                print('good')
            else:
                print('bad')
            return ret
        return wrapper2
    return wrapper1


def write_csv(result, file_obj):
    headers = result[0].keys()
    f_csv = csv.DictWriter(file_obj, headers)
    f_csv.writeheader()
    for d in result:
        f_csv.writerow(d)
    file_obj.close()


def export_file(result, file_obj):
    """将结果保存成文件，并关闭文件类型
    @param result: 结果
    @type  result: [{}, {}]

    @param file_obj: 文件流对象
    @type  file_obj: file_obj
    """
    if result:
        filename, ext = os.path.splitext(os.path.basename(file_obj.name))
        n = len(result)
        columns = result[0].keys()
        try:
            if ext in ('.csv', '.xls', '.xlsx'):
                import pandas as pd
                df = pd.DataFrame(result, columns=columns)
                if ext == '.csv':
                    df.to_csv(file_obj.name, index=False, encoding='utf-8-sig')
                elif ext in ('.xls', '.xlsx'):
                    df.to_excel(file_obj.name, index=False, encoding='utf-8')
            elif ext == '.json':
                json.dump(result, file_obj, ensure_ascii=False, indent=4)
            else:
                file_obj.write(','.join()+'\n')
                file_obj.writelines(
                    (','.join(_.values(columns))+'\n' for _ in result))
        except Exception as e:
            with open('dump.json', 'w') as f_dump:
                json.dump(result, f_dump, ensure_ascii=False, indent=4)
            print(f'获取了{n}条数据，保存至：dump.json')
        else:
            print(f'获取了{n}条数据，保存至：{file_obj.name}')
    else:
        print('未获取到任何数据')


def multify(func):
    @wraps(func)
    def wrapper(info, n):
        with ThreadPool(n) as pool:
            result = pool.starmap(func, info)
        rv = [x for x in result if x['result'] == 'yes']
        return rv
    return wrapper


def get_settings(settings):
    return {tmp: getattr(settings, tmp)
            for tmp in dir(settings) if tmp.isupper()}


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type %s not serializable" % type(obj))


def bytes_to_str(s, encoding='utf-8'):
    """Returns a str if a bytes object is given."""
    if six.PY3 and isinstance(s, bytes):
        return s.decode(encoding)
    return s


def load_object(path):
    """Load an object given its absolute object path, and return it.

    object can be a class, function, variable or an instance.
    path ie: 'scrapy.downloadermiddlewares.redirect.RedirectMiddleware'
    """

    try:
        dot = path.rindex('.')
    except ValueError:
        raise ValueError("Error loading object '%s': not a full path" % path)

    module, name = path[:dot], path[dot+1:]
    mod = import_module(module)

    try:
        obj = getattr(mod, name)
    except AttributeError:
        raise NameError(
            "Module '%s' doesn't define any object named '%s'" %
            (module, name))

    return obj


def walk_modules(path):
    """Loads a module and all its submodules from the given module path and
    returns them. If *any* module throws an exception while importing, that
    exception is thrown back.

    For example: walk_modules('scrapy.utils')
    """

    mods = []
    mod = import_module(path)
    mods.append(mod)
    if hasattr(mod, '__path__'):
        for _, subpath, ispkg in iter_modules(mod.__path__):
            fullpath = path + '.' + subpath
            if ispkg:
                mods += walk_modules(fullpath)
            else:
                submod = import_module(fullpath)
                mods.append(submod)
    return mods


def to_bytes(text, encoding=None, errors='strict'):
    """Return the binary representation of `text`. If `text`
    is already a bytes object, return it as-is."""
    if isinstance(text, bytes):
        return text
    if not isinstance(text, six.string_types):
        raise TypeError('to_bytes must receive a unicode, str or bytes '
                        'object, got %s' % type(text).__name__)
    if encoding is None:
        encoding = 'utf-8'
    return text.encode(encoding, errors)


def obj_fingerprint(obj):
    """将一个对象hash化

    :obj: TODO
    :returns: TODO

    """
    fp = hashlib.sha1(to_bytes(str(obj))).digest()
    return fp
