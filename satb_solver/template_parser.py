import re
from collections import namedtuple
from typing import Iterator, List

from cached_property import cached_property

from model.chord_formulas import (AUGChord, Chord, DIM7Chord, DIMChord,
                                  DOM7Chord, DOM9Chord, DOM11Chord, DOM13Chord,
                                  MAJ7Chord, MAJ9Chord, MAJ11Chord, MAJ13Chord,
                                  MAJChord, MIN7Chord, MIN9Chord, MIN11Chord,
                                  MIN13Chord, MINChord)
from model.classifications import ACCSYM, INVS
from model.exceptions import UnknownChordError
from model.nt_def import FormulaParts


class TemplateParser:
    def __init__(self):
        pass

    @cached_property
    def formula_matcher(self):
        return re.compile(r"""^
            ([A-G])([b#])?                  # Main note
            (min|maj|aug|dim)?              # Base triad
            (?:([b#])?(7|9|11|13))?         # Compound notes
            (?:-(sus)(\d)?)?                # Sustained note
            (?:-(add\d+|                    # Independant added note
            [b#]\d+|                        # One note modification
            \([b#]\d+(?:,[b#]\d+)*\)))?     # Multiple note modification
            (?:_(6|43|42))?                 # Inversion
            $""", re.VERBOSE)

    def _resolve_base_match(self, parts: FormulaParts) -> Chord:
        chord_switcher = {
            ('maj', None): MAJChord, ('min', None): MINChord,
            ('dim', None): DIMChord, ('aug', None): AUGChord,

            ('maj', '7'): MAJ7Chord, ('min', '7'): MIN7Chord,
            ('dim', '7'): DIM7Chord, (None, '7'): DOM7Chord,

            ('maj', '9'): MAJ9Chord, ('min', '9'): MIN9Chord, (None, '9'): DOM9Chord,
            ('maj', '11'): MAJ11Chord, ('min', '11'): MIN11Chord, (None, '11'): DOM11Chord,
            ('maj', '13'): MAJ13Chord, ('min', '13'): MIN13Chord, (None, '13'): DOM13Chord
        }
        chord = chord_switcher.get((parts.triad or None, parts.compound_itvl or None))
        if chord is None:
            raise UnknownChordError('Unable to resolve chord with formula {}')
        return chord(parts.main_note + (parts.main_accid or ''), int(parts.inv or INVS.ROOT))

    def _resolve_addons(self, chord: Chord, parts: FormulaParts) -> Chord:
        if parts.modif.startswith('add'):
            chord.add_independant_note(parts.modif[3:])
        elif parts.modif.startswith('('):
            chord.modify_arbitrary_notes(*(parts.modif.strip('()').split(',')))
        else:
            chord.modify_arbitrary_notes(parts.modif)
        return chord

    def _resolve_modifications(self, chord: Chord, parts: FormulaParts) -> Chord:
        if parts.compound_accid:
            chord.modify_compound_note(parts.compound_accid)
        if parts.has_sus:
            chord.add_sus(parts.sus_itvl or None)
        if parts.modif:
            chord = self._resolve_addons(chord, parts)
        return chord

    def _get_composition(self, chord_formula: str) -> Chord:
        parsed_formula = self.formula_matcher.findall(chord_formula)
        assert len(parsed_formula) == 1, 'Only one formula on one line is allowed'
        parts = FormulaParts(*parsed_formula[0])

        base_chord = self._resolve_base_match(parts)
        full_chord = self._resolve_modifications(base_chord, parts)
        return full_chord

    def parse_template(self, template: List[str]) -> Iterator[Chord]:
        for formula in template:
            try:
                yield self._get_composition(formula)
            except UnknownChordError as e:
                e.message = e.message.format(formula)
                raise

    def parse_init_cond(self, init_notes: List[str]) -> Iterator[str]:
        notes = init_notes.split()
        assert len(notes) == 4, 'Initial SATB harmony is not 4-part'
        for note_str in notes:
            yield note_str
