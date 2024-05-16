import ast
import functools
import inspect
import textwrap
import weakref

import cachetools


def cache(func: callable):
    """Cache a function based on the ids of its dependencies."""

    # Create weak value cache to store (id) -> (object) mappings for all the
    # dependencies of the function
    func_dependency_cache = weakref.WeakValueDictionary()

    # Create a LRU cache to map (*ids) -> (return value) for the function,
    # where *ids are the ids of the dependencies
    func_return_cache = cachetools.LRUCache(maxsize=128)

    source = inspect.getsource(func)
    source = textwrap.dedent(source)
    root = ast.parse(source)

    # Find the FunctionDef node for the function
    nodes = {
        node
        for node in ast.walk(root)
        if isinstance(node, ast.FunctionDef)
        and node.name == func.__name__
    }
    if len(nodes) != 1:
        raise ValueError(f"Found {len(nodes)} nodes for {func.__name__}, expected 1")

    function_def = nodes.pop()

    # Find all the names and attribute lookups in the function
    names = set()
    attributes = set()
    for node in ast.walk(function_def):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            attributes.add((node.value.id, node.attr))

    sig = inspect.signature(func)
    missing_argument_sentinel = object()

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        ids = {
            **{
                name: id(bound_args.arguments[name])
                for name in names & bound_args.arguments.keys()
            },
            **{
                (value, attr): id(getattr(
                    bound_args.arguments[value], attr, missing_argument_sentinel))
                for value, attr in attributes
                if value in bound_args.arguments
            }
        }
        func_return_key = tuple(ids.items())

        for key in func_dependency_cache:
            try:
                ids[key]
            except KeyError:
                break
        else:
            try:
                return func_return_cache[func_return_key]
            except KeyError:
                result = func(*args, **kwargs)
                func_return_cache[func_return_key] = result
                return result

        func_dependency_cache.update(ids)

        result = func(*args, **kwargs)
        func_return_cache[func_return_key] = result
        return result

    return new_func


class cached_property(property):
    """A property with performant caching of the getter method."""

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        super().__init__(cache(fget), fset, fdel, doc)

        if fset is not None:
            raise TypeError("Cached properties do not support setters")

        if fdel is not None:
            raise TypeError("Cached properties do not support deleters")

    def setter(self, fset):
        raise TypeError("Cached properties do not support setters")
