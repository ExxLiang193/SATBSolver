from abc import ABC, abstractmethod
from collections import Counter
from itertools import combinations

from model.chord_formulas import DOM7Chord, DOM9Chord, DOM11Chord, DOM13Chord
from model.satb_elements import AbstractNote, Note


class AbstractRule(ABC):
    @classmethod
    @abstractmethod
    def validate(cls, *args, **kwargs):
        raise NotImplementedError


class AllNotesMatchedRule(AbstractRule):
    NOTE_COUNT = 4

    @classmethod
    def validate(cls, matchings, transition_context):
        return len(matchings) == cls.NOTE_COUNT


class ValidParallelIntervalRule(AbstractRule):
    VALID_PARALLEL_INTERVALS = {3, 4, 8, 9}

    @classmethod
    def validate(cls, raw_matchings, transition_context):
        for pair in combinations(raw_matchings, 2):
            pair_one, pair_two = pair[0], pair[1]
            if (
                (
                    (pair_two.next_note.note_repr.abs_pos -
                     pair_one.next_note.note_repr.abs_pos) % 12 ==
                    (pair_two.cur_note.note_repr.abs_pos -
                     pair_one.cur_note.note_repr.abs_pos) % 12
                ) &
                (
                    (pair_two.next_note.note_repr.abs_pos - pair_one.next_note.note_repr.abs_pos)
                    not in cls.VALID_PARALLEL_INTERVALS
                ) &
                (
                    not (pair_one.cur_note.note_repr.abs_pos == 
                         pair_one.next_note.note_repr.abs_pos)
                )
            ):
                return False
        return True


class VoicesNotExceedingOctaveNorCrossingRule(AbstractRule):
    @classmethod
    def validate(cls, raw_matchings, transition_context):
        for i in range(2, len(raw_matchings)):
            pair_one = raw_matchings[i - 1]
            pair_two = raw_matchings[i]
            # There should not any perfect unisons nor intervals exceeding an octave
            if (
                (pair_two.next_note.note_repr.abs_pos - pair_one.next_note.note_repr.abs_pos <= 0) |
                (pair_two.next_note.note_repr.abs_pos - pair_one.next_note.note_repr.abs_pos > 12)
            ):
                return False
        return True


class VoicesWithinRangeRule(AbstractRule):
    SOP_RANGE = (Note(AbstractNote('C'), 4), Note(AbstractNote('C'), 6))  # Soprano
    MS_RANGE = (Note(AbstractNote('A'), 3), Note(AbstractNote('G'), 5))  # Mezzo Soprano
    ALT_RANGE = (Note(AbstractNote('F'), 3), Note(AbstractNote('D'), 5))  # Alto
    TEN_RANGE = (Note(AbstractNote('C'), 3), Note(AbstractNote('A'), 4))  # Tenor
    BAR_RANGE = (Note(AbstractNote('G'), 2), Note(AbstractNote('F'), 4))  # Baritone
    BASS_RANGE = (Note(AbstractNote('E'), 2), Note(AbstractNote('E'), 4))  # Bass

    FOUR_VOICES = [BASS_RANGE, TEN_RANGE, ALT_RANGE, SOP_RANGE]
    FIVE_VOICES = [BASS_RANGE, BAR_RANGE, TEN_RANGE, ALT_RANGE, SOP_RANGE]
    SIX_VOICES = [BASS_RANGE, BAR_RANGE, TEN_RANGE, ALT_RANGE, MS_RANGE, SOP_RANGE]

    @classmethod
    def _is_within_range(cls, pos, voice_range):
        return (pos >= voice_range[0].abs_pos & pos <= voice_range[1].abs_pos)

    @classmethod
    def validate(cls, raw_matchings, transition_context):
        voices = None
        if len(raw_matchings) == 4:
            voices = cls.FOUR_VOICES
        elif len(raw_matchings) == 5:
            voices = cls.FIVE_VOICES
        elif len(raw_matchings) == 6:
            voices = cls.SIX_VOICES
        for matching, voice_range in zip(raw_matchings, voices):
            if not cls._is_within_range(matching.next_note.note_repr.abs_pos, voice_range):
                return False
        return True


class DominantNotesResolvingRule(AbstractRule):
    DOM_TOL = {
        3: {1},
        7: {-2, -1},
        9: {-2, -1},
        11: {0},
        13: {0, -1, -2, -3, -4}
    }
    SUS_TOL = {
        2: {1, 2},
        4: {-2, -1}
    }

    @classmethod
    def _is_within_tolerance(cls, simple_matching, tolerance_set):
        if simple_matching.cur_note.scale_pos in tolerance_set:
            if (
                (simple_matching.next_note.note_repr.abs_pos -
                 simple_matching.cur_note.note_repr.abs_pos)
                not in tolerance_set[simple_matching.cur_note.scale_pos]
            ):
                return False
        return True

    @classmethod
    def validate(cls, raw_matchings, transition_context):
        cur_chord = transition_context.cur_satb_chord
        if any(isinstance(cur_chord.chord_formula, chord_type)
               for chord_type in (DOM7Chord, DOM9Chord, DOM11Chord, DOM13Chord)):
            for simple_matching in raw_matchings:
                if not cls._is_within_tolerance(simple_matching, cls.DOM_TOL):
                    return False
        for simple_matching in raw_matchings:
            if not cls._is_within_tolerance(simple_matching, cls.SUS_TOL):
                return False
        return True


class AcceptableNoteFrequenciesRule(AbstractRule):
    @classmethod
    def validate(cls, raw_matchings, transition_context):
        pos_counter = Counter()
        for simple_matching in raw_matchings:
            pos_counter[simple_matching.next_note.scale_pos] += 1
        freq_tol = transition_context.next_satb_chord.chord_formula.get_note_freqs()
        for pos, freq_range in freq_tol.items():
            if (
                (pos_counter.get(pos, 0) < freq_range.min_freq) |
                (pos_counter.get(pos, 0) > freq_range.max_freq)
            ):
                return False
        return True
