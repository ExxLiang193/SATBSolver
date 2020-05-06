import re
from collections import namedtuple
from typing import Dict, Set, Tuple

from model.classifications import ACCSYM, INVS, ItvlToSemi, NoteNameToScalePos
from model.dt_def import FreqRange, NotePosPair
from model.multimap import SimpleBiMap
from model.satb_elements import AbstractNote
from model.solver_config import get_config


class Chord:
    def __init__(self, base_note, inv):
        self.base_note = AbstractNote(base_note)
        self.base_ess = self.ESSENTIAL
        self.inversion = inv
        self.itvls = {}

    def __repr__(self):
        return str((self.base_note, self.inversion, self.itvls))

    def _infer_note_name(self, scale_itvl: int, semi_itvl: int) -> str:
        nat_note_name, semi_pos = NoteNameToScalePos.get_relative_scale_pos(
            self.base_note.nat_note, scale_itvl
        )
        change = (self.base_note.semi_pos + semi_itvl - semi_pos) % 12
        if change >= 6:
            change -= 12
        return nat_note_name + ACCSYM.incr(ACCSYM.NAT, change)

    def get_itvl_note_mapping(self) -> SimpleBiMap:
        mapping = SimpleBiMap()
        for pos, itvl in self.itvls.items():
            mapping.set(pos, AbstractNote(self._infer_note_name(pos, itvl)))
        return mapping

    def get_key_pos_pairs(self) -> Set[NotePosPair]:
        return {NotePosPair(pos, AbstractNote(self._infer_note_name(pos, itvl)))
                for pos, itvl in self.itvls.items()}

    def get_note_freqs(self, exc=False) -> Dict[int, FreqRange]:
        freqs = {}
        for scale_pos in self.itvls.keys():
            freqs[scale_pos] = FreqRange(
                min_freq=1 if scale_pos in (self.CAD_ESSENTIAL if exc else self.base_ess) else 0,
                max_freq=1 if scale_pos in self.NON_DUP else (3 if exc else 2)
            )
        return freqs

    def annotate(self, formula_name: str) -> None:
        self.formula_name = formula_name

    def note_count(self) -> int:
        return len(self.itvls)

    def set_notes(self, *new: Tuple[int, int]) -> None:
        for (place, itv) in new:
            self.itvls[place] = itv

    def remove_notes(self, *targets: int) -> None:
        for place in targets:
            if place in self.itvls:
                del self.itvls[place]

    def add_ess_notes(self, target: int) -> None:
        self.base_ess |= {target}
        assert len(self.base_ess) <= get_config()['voice_count'], (
            'Number of essential notes exceeded when requiring note at pos {}'.format(target)
        )

    def replace_ess_notes(self, old: int, new: int) -> None:
        self.base_ess = self.base_ess - {old} | {new}
        assert len(self.base_ess) <= get_config()['voice_count'], (
            'Number of essential notes exceeded when replacing note requirement from '
            'pos {} to pos {}'
        ).format(old, new)


class BaseChord(Chord):
    ESSENTIAL = {1}

    def __init__(self, base_note, inv):
        super(BaseChord, self).__init__(base_note, inv)
        self.set_notes((1, ItvlToSemi.UNIS1), (5, ItvlToSemi.PERF5))

    def _get_diff(self, mod: str) -> int:
        assert mod in ('b', '#'), 'Modification to note is invalid'
        return 1 if mod == '#' else -1

    def add_sus(self, itvl: str) -> None:
        assert self.inversion == INVS.ROOT, 'Cannot add sustained note to non-root inversion'
        if itvl == '2':
            self.remove_notes(3)
            self.set_notes((2, ItvlToSemi.MAJ2))
            self.replace_ess_notes(3, 2)
        elif itvl == '4' or itvl is None:
            self.remove_notes(3)
            self.set_notes((4, ItvlToSemi.PERF4))
            self.replace_ess_notes(3, 4)
        else:
            raise ValueError('Suspended note {} is not of interval 2 or 4'.format(itvl))

    def modify_compound_note(self, mod: str) -> None:
        assert hasattr(self, 'COMPOUND_TARGET'), ('Only 9th, 11th, and 13th chords can have '
                                                  'compound note modified')
        diff = self._get_diff(mod)
        self.set_notes((self.COMPOUND_TARGET, self.itvls[self.COMPOUND_TARGET] + diff))

    def add_independant_note(self, scale_pos):
        assert scale_pos > 0, 'Added note must be value interval size'
        raise NotImplementedError

    def modify_arbitrary_notes(self, *mod_notes: str) -> None:
        for note in mod_notes:
            parts = re.search(r'^([b#])(\d+)$', note)
            mod, pos = parts.group(1), int(parts.group(2))
            diff = self._get_diff(mod)
            self.set_notes((pos, self.itvls[pos] + diff))
            self.add_ess_notes(pos)

# TRIADS


class Triad:
    ESSENTIAL = BaseChord.ESSENTIAL | {3, 5}
    CAD_ESSENTIAL = BaseChord.ESSENTIAL | {3}
    NON_DUP = {}

    def get_base_with_inv(self):
        if self.inversion == INVS.ROOT:
            return self.get_itvl_note_mapping().get(1)
        elif self.inversion == INVS.TRI_FIRST:
            return self.get_itvl_note_mapping().get(3)
        elif self.inversion == INVS.TRI_SECOND:
            return self.get_itvl_note_mapping().get(5)
        else:
            raise ValueError('Invalid inversion {} encountered'.format(self.inversion))


class MAJChord(Triad, BaseChord):
    def __init__(self, base_note, inv):
        super(MAJChord, self).__init__(base_note, inv)
        self.set_notes((3, ItvlToSemi.MAJ3))


class MINChord(Triad, BaseChord):
    def __init__(self, base_note, inv):
        super(MINChord, self).__init__(base_note, inv)
        self.set_notes((3, ItvlToSemi.MIN3))


class DIMChord(Triad, BaseChord):
    def __init__(self, base_note, inv):
        super(DIMChord, self).__init__(base_note, inv)
        self.set_notes((3, ItvlToSemi.MIN3), (5, ItvlToSemi.DIM5))


class AUGChord(Triad, BaseChord):
    def __init__(self, base_note, inv):
        super(AUGChord, self).__init__(base_note, inv)
        self.set_notes((3, ItvlToSemi.MAJ3), (5, ItvlToSemi.AUG5))

# 7TH CHORDS


class COMP7Chord:
    ESSENTIAL = BaseChord.ESSENTIAL | {3, 7}
    NON_DUP = {3, 7}

    def get_base_with_inv(self):
        if self.inversion == INVS.ROOT:
            return self.get_itvl_note_mapping().get(1)
        elif self.inversion == INVS.SEV_FIRST:
            return self.get_itvl_note_mapping().get(3)
        elif self.inversion == INVS.SEV_SECOND:
            return self.get_itvl_note_mapping().get(5)
        elif self.inversion == INVS.SEV_THIRD:
            return self.get_itvl_note_mapping().get(7)
        else:
            raise ValueError('Invalid inversion {} encountered'.format(self.inversion))


class MAJ7Chord(COMP7Chord, MAJChord):
    def __init__(self, base_note, inv):
        super(MAJ7Chord, self).__init__(base_note, inv)
        self.set_notes((7, ItvlToSemi.MAJ7))


class MIN7Chord(COMP7Chord, MINChord):
    def __init__(self, base_note, inv):
        super(MIN7Chord, self).__init__(base_note, inv)
        self.set_notes((7, ItvlToSemi.MIN7))


class DOM7Chord(COMP7Chord, MAJChord):
    def __init__(self, base_note, inv):
        super(DOM7Chord, self).__init__(base_note, inv)
        self.set_notes((7, ItvlToSemi.MIN7))


class DIM7Chord(COMP7Chord, DIMChord):
    def __init__(self, base_note, inv):
        super(DIM7Chord, self).__init__(base_note, inv)
        self.set_notes((7, ItvlToSemi.DIM7))

# 9TH CHORDS


class COMP9Chord:
    COMPOUND_TARGET = 9
    ESSENTIAL = COMP7Chord.ESSENTIAL | {9}
    NON_DUP = {3, 7, 9}


class MAJ9Chord(COMP9Chord, MAJ7Chord):
    def __init__(self, base_note, inv):
        super(MAJ9Chord, self).__init__(base_note, inv)
        assert inv == INVS.ROOT, 'Compound 9th must be in root inversion'
        self.set_notes((9, ItvlToSemi.MAJ9))


class MIN9Chord(COMP9Chord, MIN7Chord):
    def __init__(self, base_note, inv):
        super(MIN9Chord, self).__init__(base_note, inv)
        assert inv == INVS.ROOT, 'Compound 9th must be in root inversion'
        self.set_notes((9, ItvlToSemi.MIN9))


class DOM9Chord(COMP9Chord, DOM7Chord):
    def __init__(self, base_note, inv):
        super(DOM9Chord, self).__init__(base_note, inv)
        assert inv == INVS.ROOT, 'Compound 9th must be in root inversion'
        self.set_notes((9, ItvlToSemi.MAJ9))

# 11TH CHORDS


class COMP11Chord:
    COMPOUND_TARGET = 11
    ESSENTIAL = COMP7Chord.ESSENTIAL | {11}
    NON_DUP = {3, 7, 11}


class MAJ11Chord(COMP11Chord, MAJ9Chord):
    def __init__(self, base_note, inv):
        super(MAJ11Chord, self).__init__(base_note, inv)
        assert inv == INVS.ROOT, 'Compound 11th must be in root inversion'
        self.set_notes((11, ItvlToSemi.PERF11))


class MIN11Chord(COMP11Chord, MIN9Chord):
    def __init__(self, base_note, inv):
        super(MIN11Chord, self).__init__(base_note, inv)
        assert inv == INVS.ROOT, 'Compound 11th must be in root inversion'
        self.set_notes((11, ItvlToSemi.PERF11))


class DOM11Chord(COMP11Chord, DOM9Chord):
    def __init__(self, base_note, inv):
        super(DOM11Chord, self).__init__(base_note, inv)
        assert inv == INVS.ROOT, 'Compound 11th must be in root inversion'
        self.set_notes((11, ItvlToSemi.PERF11))

# 13TH CHORDS


class COMP13Chord:
    COMPOUND_TARGET = 13
    ESSENTIAL = COMP7Chord.ESSENTIAL | {13}
    NON_DUP = {3, 7, 13}


class MAJ13Chord(COMP13Chord, MAJ11Chord):
    def __init__(self, base_note, inv):
        super(MAJ13Chord, self).__init__(base_note, inv)
        assert inv == INVS.ROOT, 'Compound 13th must be in root inversion'
        self.set_notes((13, ItvlToSemi.MAJ13))


class MIN13Chord(COMP13Chord, MIN11Chord):
    def __init__(self, base_note, inv):
        super(MIN13Chord, self).__init__(base_note, inv)
        assert inv == INVS.ROOT, 'Compound 13th must be in root inversion'
        self.set_notes((13, ItvlToSemi.MAJ13))


class DOM13Chord(COMP13Chord, DOM11Chord):
    def __init__(self, base_note, inv):
        super(DOM13Chord, self).__init__(base_note, inv)
        assert inv == INVS.ROOT, 'Compound 13th must be in root inversion'
        self.set_notes((13, ItvlToSemi.MAJ13))
