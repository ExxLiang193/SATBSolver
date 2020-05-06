from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:
    from model.satb_elements import AbstractNote, Note, SATBChord


@dataclass(frozen=True)
class FormulaParts:
    main_note: str
    main_accid: str
    triad: str
    compound_accid: str
    compound_itvl: str
    has_sus: str
    sus_itvl: str
    modif: str
    inv: str


@dataclass(frozen=True)
class FreqRange:
    min_freq: int
    max_freq: int


@dataclass(frozen=True)
class NotePosPair:
    scale_pos: int
    note_repr: Union[AbstractNote, Note]


@dataclass(frozen=True)
class Transition:
    min_diff: int
    cur_pair: NotePosPair
    next_pair: NotePosPair

    @property
    def cur_abs_pos(self):
        return self.cur_pair.note_repr.abs_pos

    @property
    def next_abs_pos(self):
        return self.next_pair.note_repr.abs_pos

    @property
    def cur_scale_pos(self):
        return self.cur_pair.scale_pos

    @property
    def next_scale_pos(self):
        return self.next_pair.scale_pos

    @property
    def abs_pos_changed(self):
        return self.cur_abs_pos != self.next_abs_pos

    @property
    def abs_pos_diff(self):
        return abs(self.next_abs_pos - self.cur_abs_pos)


@dataclass(frozen=True)
class MatchConfig:
    matchings: Dict[int, Transition]


@dataclass(frozen=True)
class TransitionContext:
    cur_satb_chord: SATBChord
    next_satb_chord: SATBChord

    @property
    def cur_chord_formula(self):
        return self.cur_satb_chord.chord_formula

    @property
    def next_chord_formula(self):
        return self.next_satb_chord.chord_formula
