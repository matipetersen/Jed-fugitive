"""
JSON codec for game state.

Turns the game's object graph (Player, Weapon, ForceAbility, Quest, NPC...)
into plain JSON and back, so saves keep *everything* the player owns instead
of a hand-picked list of fields.

* Only classes from ``jedi_fugitive.*`` are encoded or rebuilt (a save file
  can never make the loader import or construct anything else).
* Shared references survive: an object reached twice is stored once and
  rebuilt as one object (``__id__`` / ``__ref__``); cycles are fine.
* Tuples, sets, enums and dicts with non-string keys round-trip exactly.
* Live links that belong to the running session (the GameManager, the UI,
  curses windows, functions) are dropped and must be re-attached by the
  loader; ``SKIP`` lists object attribute names that are always dropped.
"""
import enum
import importlib
import types

ALLOWED_PREFIX = 'jedi_fugitive.'
SKIP = frozenset({'game', 'ui', 'stdscr', 'gfx', 'messages', '_cached_stats'})


class _Drop:
    pass


DROP = _Drop()


def _qualname(cls):
    return f"{cls.__module__}:{cls.__qualname__}"


def _allowed(cls):
    return cls.__module__.startswith(ALLOWED_PREFIX)


def _resolve(qual):
    module, _, name = qual.partition(':')
    if not module.startswith(ALLOWED_PREFIX):
        raise ValueError(f"refusing to load class from {module}")
    obj = importlib.import_module(module)
    for part in name.split('.'):
        obj = getattr(obj, part)
    return obj


class Encoder:
    def __init__(self, skip=SKIP, stop_types=()):
        self.skip = set(skip)
        self.stop_types = tuple(stop_types)
        self.memo = {}

    def encode(self, v):
        if v is None or isinstance(v, (bool, int, float, str)):
            return v
        if isinstance(v, (types.FunctionType, types.MethodType, types.BuiltinFunctionType, type, types.ModuleType)):
            return DROP
        if self.stop_types and isinstance(v, self.stop_types):
            return DROP
        if isinstance(v, enum.Enum):
            if not _allowed(type(v)):
                return DROP
            return {'__enum__': _qualname(type(v)), 'name': v.name}
        if isinstance(v, list):
            return [x for x in (self.encode(i) for i in v) if x is not DROP]
        if isinstance(v, tuple):
            return {'__tuple__': [self._keep(self.encode(i)) for i in v]}
        if isinstance(v, (set, frozenset)):
            return {'__set__': [x for x in (self.encode(i) for i in v) if x is not DROP]}
        if isinstance(v, dict):
            if all(isinstance(k, str) for k in v):
                out = {}
                for k, x in v.items():
                    e = self.encode(x)
                    if e is not DROP:
                        out[k] = e
                if any(k.startswith('__') and k.endswith('__') for k in out):
                    return {'__dict__': out}
                return out
            pairs = []
            for k, x in v.items():
                ek, ex = self.encode(k), self.encode(x)
                if ek is not DROP and ex is not DROP:
                    pairs.append([ek, ex])
            return {'__items__': pairs}
        cls = type(v)
        if not _allowed(cls) or not hasattr(v, '__dict__'):
            return DROP
        key = id(v)
        if key in self.memo:
            return {'__ref__': self.memo[key]}
        oid = len(self.memo) + 1
        self.memo[key] = oid
        state = {}
        for k, x in vars(v).items():
            if k in self.skip:
                continue
            e = self.encode(x)
            if e is not DROP:
                state[k] = e
        return {'__obj__': _qualname(cls), '__id__': oid, 'state': state}

    @staticmethod
    def _keep(x):
        return None if x is DROP else x


class Decoder:
    def __init__(self):
        self.objects = {}

    def decode(self, v):
        if v is None or isinstance(v, (bool, int, float, str)):
            return v
        if isinstance(v, list):
            return [self.decode(i) for i in v]
        if not isinstance(v, dict):
            return v
        if '__ref__' in v:
            return self.objects[v['__ref__']]
        if '__obj__' in v:
            cls = _resolve(v['__obj__'])
            obj = cls.__new__(cls)
            self.objects[v['__id__']] = obj
            for k, x in v['state'].items():
                try:
                    object.__setattr__(obj, k, self.decode(x))
                except Exception:
                    pass
            return obj
        if '__enum__' in v:
            return _resolve(v['__enum__'])[v['name']]
        if '__tuple__' in v:
            return tuple(self.decode(i) for i in v['__tuple__'])
        if '__set__' in v:
            return set(self.decode(i) for i in v['__set__'])
        if '__items__' in v:
            return {self.decode(k): self.decode(x) for k, x in v['__items__']}
        if '__dict__' in v:
            return {k: self.decode(x) for k, x in v['__dict__'].items()}
        return {k: self.decode(x) for k, x in v.items()}


def encode(value, skip=SKIP, stop_types=()):
    out = Encoder(skip, stop_types).encode(value)
    return None if out is DROP else out


def decode(data):
    return Decoder().decode(data)
