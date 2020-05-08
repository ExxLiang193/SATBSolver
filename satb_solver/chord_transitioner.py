import heapq
import re
from collections import namedtuple
from copy import deepcopy
from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Set, Tuple

from termcolor import colored

from model.chord_formulas import Chord
from model.dt_def import ChordNode, NotePosPair, Transition, TransitionContext
from model.exceptions import UnableToTransitionError
from model.satb_elements import AbstractNote, Note, SATBChord, SATBSequence
from model.solver_config import get_config
from satb_solver.bf_transition_optimizer import BFTransitionOptimizer
from satb_solver.solution_interface import SolutionInterface


class ChordTransitioner:
    COST_LEAD_THRES = 100000

    def __init__(self):
        pass

    def _min_diff(self, abs_note: int, rel_note: int, full=False) -> Tuple[int, Set[int]]:
        octave, rel_abs_note = abs_note // 12, abs_note % 12
        if rel_note == rel_abs_note:
            return (0, {abs_note})
        offset = 0 if rel_note < rel_abs_note else -1
        lower_abs_note = (octave + offset) * 12 + rel_note
        upper_abs_note = (octave + offset + 1) * 12 + rel_note
        if full:
            return (-1, {lower_abs_note, upper_abs_note})
        if abs_note - lower_abs_note == 6:
            return (6, {lower_abs_note, upper_abs_note})
        elif abs_note - lower_abs_note < 6:
            return (abs_note - lower_abs_note, {lower_abs_note})
        else:
            return (upper_abs_note - abs_note, {upper_abs_note})

    def _agg_trans(self, cur_abs_note: NotePosPair, next_rel_note: NotePosPair,
                   trans_agg: Dict[int, Set[Transition]], full=False) -> None:
        min_transition_diff, min_diff_notes = (
            self._min_diff(
                cur_abs_note.note_repr.abs_pos,
                next_rel_note.note_repr.semi_pos,
                full)
        )
        for note in min_diff_notes:
            new_transition = Transition(
                min_diff=min_transition_diff,
                cur_pair=cur_abs_note,
                next_pair=NotePosPair(
                    next_rel_note.scale_pos,
                    Note(next_rel_note.note_repr, note // 12)
                )
            )
            if min_transition_diff in trans_agg:
                trans_agg[min_transition_diff].add(new_transition)
            else:
                trans_agg[min_transition_diff] = {new_transition}

    def _split_by_base(self, pairs: List[NotePosPair],
                       chord_formula: Chord) -> Tuple[NotePosPair, List[NotePosPair]]:
        formula_base = chord_formula.get_base_with_inv()
        base_pair = [pair for pair in pairs if pair.note_repr.semi_pos == formula_base.semi_pos]
        if len(base_pair) >= 2:
            base_pair = sorted(base_pair, key=lambda pair: pair.note_repr.abs_pos)
            base_pair, other_pair = base_pair[0], [base_pair[1]]
        else:
            base_pair, other_pair = base_pair[0], []
        other_pairs = [pair for pair in pairs if pair.note_repr.semi_pos != formula_base.semi_pos]
        return base_pair, other_pair + other_pairs

    def _get_checking_priority(self, cur_abs_notes: List[NotePosPair],
                               next_rel_notes: List[NotePosPair],
                               trans_context: TransitionContext) -> List:
        transition_aggregator = {}
        agg_checker_queue = []
        if get_config()['include_inv']:
            cur_base, cur_abs_notes = self._split_by_base(
                cur_abs_notes, trans_context.cur_satb_chord.chord_formula
            )
            next_base, _ = self._split_by_base(
                next_rel_notes, trans_context.next_satb_chord.chord_formula
            )
            self._agg_trans(cur_base, next_base, transition_aggregator, full=True)
        for (cur_abs_note, next_rel_note) in product(cur_abs_notes, next_rel_notes):
            self._agg_trans(cur_abs_note, next_rel_note, transition_aggregator)
        for (diff, transitions) in transition_aggregator.items():
            heapq.heappush(agg_checker_queue, (diff, transitions))
        return agg_checker_queue

    def find_optimal_transition(self, cur_satb_chord: SATBChord,
                                next_chord: SATBChord) -> Tuple[List, int]:
        transition_context = TransitionContext(cur_satb_chord, next_chord)
        prioritized_checker = self._get_checking_priority(
            cur_satb_chord.key_pos_pairs,
            next_chord.chord_formula.get_key_pos_pairs(),
            transition_context
        )
        return BFTransitionOptimizer(
            prioritized_checker, transition_context
        ).solve()

    def _get_agg_min_cost_seqs(self, next_seqs: List[SATBSequence]) -> List[SATBSequence]:
        min_overall_cost = min(next_seqs, key=lambda seq: seq.seq_cost).seq_cost
        seq_agg = {}
        queued_seqs = []
        for seq in next_seqs:
            if hash(seq) in seq_agg:
                seq_agg[hash(seq)].append(seq)
            else:
                seq_agg[hash(seq)] = [seq]
        for _, seqs in seq_agg.items():
            min_seq_cost = min(seqs, key=lambda seq: seq.seq_cost).seq_cost
            for seq in seqs:
                if seq.seq_cost > min_overall_cost + self.COST_LEAD_THRES:
                    continue
                if seq.seq_cost == min_seq_cost:
                    queued_seqs.append(seq)
        return queued_seqs

    def _get_abs_min_cost_seqs(self, final_seqs: List[SATBSequence]) -> List[SATBSequence]:
        min_overall_cost = min(final_seqs, key=lambda seq: seq.seq_cost).seq_cost
        res = []
        for seq in final_seqs:
            if seq.seq_cost == min_overall_cost:
                res.append(seq)
        return res

    def _infer_init_note_pos(self, init_notes: List[str],
                             init_model_chord: Chord) -> Set[NotePosPair]:
        result = set()
        for init_note in init_notes:
            parts = re.search(r'^([A-G])(bb|b|#|x)?(\d)$', init_note)
            abs_note = AbstractNote(parts.group(1) + (parts.group(2) or ''))
            rev_map = init_model_chord.get_itvl_note_mapping()
            scale_pos = rev_map.get(abs_note, inv=True)
            pair = NotePosPair(scale_pos, Note(abs_note, int(parts.group(3))))
            if pair in result:
                raise ValueError('Duplicate note {} in initial notes.'.format(init_note))
            else:
                result.add(NotePosPair(scale_pos, Note(abs_note, int(parts.group(3)))))
        return result

    def transition_chords(self, chord_seq: List[Chord],
                          init_notes: List[str]) -> List[SATBSequence]:
        chord_seq = list(chord_seq)
        assert len(chord_seq) >= 1, 'No chord formulas were specified in template'
        init_notes = self._infer_init_note_pos(init_notes, chord_seq[0])

        queued_seqs = [SATBSequence().add_satb_chord(
            SATBChord(chord_seq[0], init_notes), 0
        )]
        for i in range(1, len(chord_seq)):
            next_seqs = []
            for cur_seq in queued_seqs:
                results, tr_cost = self.find_optimal_transition(
                    cur_seq.most_recent_chord,
                    SATBChord(chord_seq[i], None)
                )
                results = [SATBChord(chord_seq[i], result) for result in results]
                new_seqs = [deepcopy(cur_seq).add_satb_chord(satb_chord, tr_cost)
                            for satb_chord in results]
                next_seqs.extend(new_seqs)
            if len(next_seqs) == 0:
                raise UnableToTransitionError('Unable to transition between: {} and {}'.format(
                    chord_seq[i - 1].formula_name, chord_seq[i].formula_name
                ))
            if i < len(chord_seq) - 1:
                queued_seqs = self._get_agg_min_cost_seqs(next_seqs)
            else:
                queued_seqs = self._get_abs_min_cost_seqs(next_seqs)
        return queued_seqs

    def user_transition_chords(self, chord_seq, init_notes):
        chord_seq = list(chord_seq)
        assert len(chord_seq) >= 1, 'No chord formulas were specified in template'
        init_notes = self._infer_init_note_pos(init_notes, chord_seq[0])

        seq_idx = 0
        cur_node = ChordNode(None, SATBChord(chord_seq[seq_idx], init_notes), None, 0)
        while seq_idx < len(chord_seq) - 1:
            if cur_node.next_nodes is None:
                results, tr_cost = self.find_optimal_transition(
                    cur_node.chord, SATBChord(chord_seq[seq_idx + 1], None)
                )
                results = [SATBChord(chord_seq[seq_idx + 1], result) for result in results]
                cur_node.next_nodes = [ChordNode(cur_node, chord, None, tr_cost)
                                       for chord in results]
                if len(cur_node.next_nodes) == 0:
                    raise UnableToTransitionError('Unable to transition between: {} and {}'.format(
                        chord_seq[seq_idx].formula_name, chord_seq[seq_idx + 1].formula_name
                    ))
            action, choice = SolutionInterface().report_intermed_solutions(cur_node.chord,
                                                                           cur_node.next_nodes)
            if action == 1:
                cur_node = cur_node.next_nodes[choice]
                seq_idx += 1
            elif action == -1:
                if cur_node.prev_node is None:
                    print(colored('Cannot step back in sequence any further!!!', 'red'))
                else:
                    cur_node = cur_node.prev_node
                    seq_idx -= 1
        full_seq = SATBSequence()
        while cur_node is not None:
            full_seq.add_satb_chord(cur_node.chord, cur_node.cost)
            cur_node = cur_node.prev_node
        full_seq.sequence.reverse()
        return [full_seq]
