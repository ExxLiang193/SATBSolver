import re
from typing import List, Tuple

# from model.chord_formulas import Chord
from model.classifications import ACCSYM, NoteNameToSemi
from model.nt_def import NotePosPair


class AbstractNote:
    def __init__(self, note_str: str):
        assert isinstance(note_str, str)
        self._parse_note_str(note_str)

    def _key(self):
        return tuple((self.note_name, self.semi_pos))

    def __repr__(self):
        return str(self._key())

    def __hash__(self):
        return hash(self._key())

    def __eq__(self, other):
        return self._key() == other._key()

    def _parse_note_str(self, note_str: str) -> None:
        parts = re.search(r'^([A-G])(bb|b|#|x)?$', note_str)
        if parts is None:
            raise ValueError('Abstract note {} is not valid.'.format(note_str))
        self.nat_note, self.accid = parts.group(1), parts.group(2) or ''
        if self.accid not in (ACCSYM.SHSH, ACCSYM.SH, ACCSYM.FL, ACCSYM.FLFL, ACCSYM.NAT):
            raise ValueError('Abstract note {} has invalid accidental symbol.'.format(note_str))
        self.note_name = self.nat_note + self.accid
        self.semi_pos = NoteNameToSemi.get(self.note_name)


class Note(AbstractNote):
    def __init__(self, abstract_note: AbstractNote, octave: int):
        self._concretize_note(abstract_note, octave)

    def _key(self) -> Tuple[str, int, int]:
        return tuple((self.note_name, self.octave, self.semi_pos))

    @property
    def abs_pos(self) -> int:
        return self.octave * 12 + self.semi_pos

    def _concretize_note(self, abstract_note: AbstractNote, octave: int) -> None:
        self.nat_note = abstract_note.nat_note
        self.accid = abstract_note.accid
        self.octave = octave
        self.note_name = abstract_note.note_name
        self.semi_pos = abstract_note.semi_pos


class SATBChord:
    def _key(self) -> Tuple[AbstractNote, ...]:
        return tuple(sorted([note_key_pair.note_repr for note_key_pair in self.key_pos_pairs],
                            key=lambda note: note.abs_pos))

    def __repr__(self):
        return str(self.key_pos_pairs)

    def __init__(self, chord_formula, key_pos_pairs: List[NotePosPair]):
        self.key_pos_pairs = key_pos_pairs or []
        self.chord_formula = chord_formula


class SATBSequence:
    def _key(self) -> Tuple[AbstractNote, ...]:
        return self.most_recent_chord._key()

    def __repr__(self):
        return str([repr(chord) for chord in self.sequence]) + ' ' + str(self.seq_cost)

    def __hash__(self):
        return hash(self._key())

    def __eq__(self, other):
        if isinstance(other, SATBSequence):
            return self._key() == other._key()

    def __init__(self, init_satb_chord: SATBChord, cost: int = 0):
        self.sequence = [init_satb_chord]
        self.seq_cost = cost

    def add_satb_chord(self, satb_chord: SATBChord, chord_cost: int):
        self.sequence.append(satb_chord)
        self.seq_cost += chord_cost
        return self

    @property
    def most_recent_chord(self) -> SATBChord:
        return self.sequence[-1]
