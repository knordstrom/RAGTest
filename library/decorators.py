import functools
from collections.abc import Collection, Mapping, Hashable
from frozendict import frozendict

class Decorators:
    
    @staticmethod
    def _deep_freeze(thing):
        if thing is None or isinstance(thing, str):
            return thing
        elif isinstance(thing, Mapping):
            vals = ((k, Decorators._deep_freeze(v)) for k, v in thing.items())
            return frozendict(vals)
        elif isinstance(thing, Collection):
            return tuple(Decorators._deep_freeze(i) for i in thing)
        elif not isinstance(thing, Hashable):
            raise TypeError(f"unfreezable type: '{type(thing)}'")
        else:
            return thing

    @staticmethod
    def deep_freeze_args(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            return func(*Decorators._deep_freeze(args), **Decorators._deep_freeze(kwargs))
        return wrapped