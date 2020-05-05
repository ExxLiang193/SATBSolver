from abc import ABC, abstractmethod
from collections import Counter
from itertools import combinations
from typing import List

from model.chord_formulas import DOM7Chord, DOM9Chord, DOM11Chord, DOM13Chord
from model.dt_def import Transition, TransitionContext
from model.satb_elements import AbstractNote, Note


class AbstractRule(ABC):
    @classmethod
    @abstractmethod
    def validate(cls, *args, **kwargs):
        raise NotImplementedError


class AllNotesMatchedRule(AbstractRule):
    NOTE_COUNT = 4

    @classmethod
    def validate(cls, matchings: List[Transition], transition_context: TransitionContext):
        return len(matchings) == cls.NOTE_COUNT


class ValidParallelIntervalRule(AbstractRule):
    VALID_PARALLEL_INTERVALS = {3, 4, 8, 9}

    @classmethod
    def validate(cls, matchings: List[Transition], transition_context: TransitionContext):
        for trans_pair in combinations(matchings, 2):
            lower_trans, upper_trans = trans_pair[0], trans_pair[1]
            if (
                (
                    (upper_trans.next_abs_pos - lower_trans.next_abs_pos) % 12 ==
                    (upper_trans.cur_abs_pos - lower_trans.cur_abs_pos) % 12
                ) &
                (
                    (upper_trans.next_abs_pos - lower_trans.next_abs_pos)
                    not in cls.VALID_PARALLEL_INTERVALS
                ) & lower_trans.abs_pos_changed
            ):
                return False
        return True


class VoicesNotExceedingOctaveNorCrossingRule(AbstractRule):
    @classmethod
    def validate(cls, matchings: List[Transition], transition_context: TransitionContext):
        for i in range(2, len(matchings)):
            lower_trans = matchings[i - 1]
            upper_trans = matchings[i]
            # There should not any perfect unisons nor intervals exceeding an octave
            if (
                (upper_trans.next_abs_pos - lower_trans.next_abs_pos <= 0) |
                (upper_trans.next_abs_pos - lower_trans.next_abs_pos > 12)
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
    def validate(cls, matchings: List[Transition], transition_context: TransitionContext):
        voices = None
        if len(matchings) == 4:
            voices = cls.FOUR_VOICES
        elif len(matchings) == 5:
            voices = cls.FIVE_VOICES
        elif len(matchings) == 6:
            voices = cls.SIX_VOICES
        for trans, voice_range in zip(matchings, voices):
            if not cls._is_within_range(trans.next_abs_pos, voice_range):
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
    def _is_within_tolerance(cls, trans, tolerance_set):
        if trans.cur_scale_pos in tolerance_set:
            if (
                (trans.next_abs_pos - trans.cur_abs_pos)
                not in tolerance_set[trans.cur_scale_pos]
            ):
                return False
        return True

    @classmethod
    def validate(cls, matchings: List[Transition], transition_context: TransitionContext):
        cur_chord = transition_context.cur_satb_chord
        if any(isinstance(cur_chord.chord_formula, chord_type)
               for chord_type in (DOM7Chord, DOM9Chord, DOM11Chord, DOM13Chord)):
            for trans in matchings:
                if not cls._is_within_tolerance(trans, cls.DOM_TOL):
                    return False
        for trans in matchings:
            if not cls._is_within_tolerance(trans, cls.SUS_TOL):
                return False
        return True


class AcceptableNoteFrequenciesRule(AbstractRule):
    @classmethod
    def validate(cls, matchings: List[Transition], transition_context: TransitionContext):
        pos_counter = Counter()
        for trans in matchings:
            pos_counter[trans.next_scale_pos] += 1
        freq_tol = transition_context.next_satb_chord.chord_formula.get_note_freqs()
        for pos, freq_range in freq_tol.items():
            if (
                (pos_counter.get(pos, 0) < freq_range.min_freq) |
                (pos_counter.get(pos, 0) > freq_range.max_freq)
            ):
                return False
        return True
