from abc import ABC, abstractmethod


class AbstractBiMap(ABC):
    @abstractmethod
    def _add_mapping(self, key, value):
        raise NotImplementedError

    def items(self, inv=False):
        return self.backward_map.items() if inv else self.forward_map.items()

    def keys(self, inv=False):
        return self.backward_map.keys() if inv else self.forward_map.keys()

    def values(self, inv=False):
        return self.backward_map.values() if inv else self.forward_map.values()

    def get(self, key, inv=False):
        return self.backward_map.get(key) if inv else self.forward_map.get(key)

    def set(self, key, value):
        self._add_mapping(key, value)


class SimpleBiMap(AbstractBiMap):
    def _add_mapping(self, key, value):
        if key in self.forward_map:
            raise KeyError('A simple bimap encountered an illegal forward overwrite.')
        else:
            self.forward_map[key] = value
        if value in self.backward_map:
            raise KeyError('A simple bimap encountered an illegal backward overwrite.')
        else:
            self.backward_map[value] = key

    def __init__(self, mappings=None):
        self.forward_map, self.backward_map = {}, {}
        for key, value in (mappings or []):
            self.set(key, value)


class OneWayMultiMap(AbstractBiMap):
    def _add_mapping(self, key, value):
        if self.multi_forward:
            if key in self.forward_map:
                self.forward_map[key].add(value)
            else:
                self.forward_map[key] = {value}
            if value in self.backward_map:
                raise KeyError('A multi forward map encountered an illegal backward overwrite.')
            else:
                self.backward_map[value] = key
        else:
            if key in self.forward_map:
                raise KeyError('A multi backward map encountered an illegal forward overwrite.')
            else:
                self.forward_map[key] = value
            if value in self.backward_map:
                self.backward_map[value].add(key)
            else:
                self.backward_map[value] = {key}

    def __init__(self, mappings=None, dir=None):
        if dir not in ('forward', 'backward'):
            raise ValueError('OneWayMultiMap specified invalid direction upon init.')
        self.multi_forward = (dir == 'forward')
        self.forward_map, self.backward_map = {}, {}
        for key, value in (mappings or []):
            self.set(key, value)


class TwoWayMultiMap(AbstractBiMap):
    def _add_mapping(self, key, value):
        if key in self.forward_map:
            self.forward_map[key].add(value)
        else:
            self.forward_map[key] = {value}
        if value in self.backward_map:
            self.backward_map[value].add(key)
        else:
            self.backward_map[value] = {key}

    def __init__(self, mappings=None):
        self.forward_map, self.backward_map = {}, {}
        for key, value in (mappings or []):
            self.set(key, value)
