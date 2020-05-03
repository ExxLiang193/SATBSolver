import logging

from model.multimap import OneWayMultiMap

log = logging.getLogger('classifications')


class ACCSYM:
    FLFL = 'bb'
    FL = 'b'
    NAT = ''
    SH = '#'
    SHSH = 'x'
    ORDER = [FLFL, FL, NAT, SH, SHSH]

    @classmethod
    def _get_next_acc(cls, acc, adj):
        new_acc_pos = cls.ORDER.index(acc) + adj
        try:
            return cls.ORDER[new_acc_pos]
        except IndexError:
            log.error('Attempted adjustment of {} to {}'.format(adj, acc))
            return acc

    @classmethod
    def incr(cls, acc, amt=1):
        return cls._get_next_acc(acc, amt)

    @classmethod
    def decr(cls, acc, amt=1):
        return cls._get_next_acc(acc, -amt)


class NoteNameToScalePos:
    ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    MAP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

    @classmethod
    def get_relative_scale_pos(cls, cur_note, scale_itvl):
        assert cur_note in cls.ORDER
        new_note = cls.ORDER[(cls.ORDER.index(cur_note) + scale_itvl - 1) % 7]
        return new_note, cls.MAP[new_note]


class _NoteNameToSemi(OneWayMultiMap):
    ACCID = {ACCSYM.FLFL: -2, ACCSYM.FL: -1, ACCSYM.NAT: 0, ACCSYM.SH: 1, ACCSYM.SHSH: 2}

    def setup(self):
        for note, smts in NoteNameToScalePos.MAP.items():
            for accid, offset in self.ACCID.items():
                self.set(note + accid, (smts + offset) % 12)


NoteNameToSemi = _NoteNameToSemi(dir='backward')
NoteNameToSemi.setup()


class ItvlToSemi:
    UNIS_ITVS = [1, 8, 15]
    UNIS_TYPES = {'UNIS': 0}
    PERF_ITVS = [4, 5, 11, 12]
    PERF_TYPES = {'DIM': -1, 'PERF': 0, 'AUG': 1}
    MAJ_ITVS = [2, 3, 6, 7, 9, 10, 13, 14]
    MAJ_TYPES = {'DIM': -2, 'MIN': -1, 'MAJ': 0, 'AUG': 1}
    SCALE_MAP = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}

    @classmethod
    def setup(cls):
        sets = [(cls.UNIS_ITVS, cls.UNIS_TYPES),
                (cls.PERF_ITVS, cls.PERF_TYPES),
                (cls.MAJ_ITVS, cls.MAJ_TYPES)]
        for itvl_group, itvl_types in sets:
            for itv in itvl_group:
                for pref, offset in itvl_types.items():
                    setattr(ItvlToSemi, pref + str(itv),
                            cls.SCALE_MAP[(itv - 1) % 7 + 1] + offset)


ItvlToSemi.setup()


class INVS:
    ROOT = 0
    FIRST = 6
    SECOND = 43
    THIRD = 42
