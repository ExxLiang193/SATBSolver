import heapq
from collections import namedtuple

from model.transition_rules import (AllNotesMatchedRule,
                                    ValidParallelIntervalRule,
                                    VoicesNotExceedingOctaveNorCrossingRule,
                                    DominantNotesResolvingRule,
                                    VoicesWithinRangeRule,
                                    AcceptableNoteFrequenciesRule)


class BFTransitionOptimizer:
    KeyPosPair = namedtuple('KeyPosPair', ['scale_pos', 'note_repr'])
    Config = namedtuple('Config', ['matchings'])
    SimpleMatching = namedtuple('SimpMatching', ['cur_note', 'next_note'])

    def __init__(self, prioritized_checker, transition_context):
        self.prioritized_checker = prioritized_checker
        self.transition_context = transition_context
        self.cur_depth_configs = []
        self.next_depth_configs = []
        self.checked = set()

    def _get_hashable_matchings(self, config_matchings):
        return tuple(sorted(config_matchings.values(),
                            key=lambda match: match.cur_note.note_repr.abs_pos))

    def _add_to_next_depth(self, new_config):
        hashable_config_matching = self._get_hashable_matchings(new_config.matchings)
        if hashable_config_matching not in self.checked:
            self.checked.add(hashable_config_matching)
            self.next_depth_configs.append(new_config)

    def _is_valid_config(self, config):
        if not AllNotesMatchedRule.validate(config.matchings, self.transition_context):
            return False
        simplified_matchings = sorted([self.SimpleMatching(cur_note=trans.cur_note,
                                                           next_note=trans.next_note)
                                       for trans in config.matchings.values()],
                                      key=lambda pair: pair.cur_note.note_repr.abs_pos)
        for validator in [
            ValidParallelIntervalRule,
            VoicesNotExceedingOctaveNorCrossingRule,
            VoicesWithinRangeRule,
            DominantNotesResolvingRule,
            AcceptableNoteFrequenciesRule
        ]:
            if not validator.validate(simplified_matchings, self.transition_context):
                return False
        return True

    def _get_min_cost_config(self, configs):
        def simplify_config(config):
            return {tr.next_note for tr in config.matchings.values()}
        min_cost = 999999
        res = []
        for config in configs:
            cost = sum(match.min_dist for match in config.matchings.values())
            if cost < min_cost:
                min_cost = cost
                res.clear()
                res.append(simplify_config(config))
            elif cost == min_cost:
                res.append(simplify_config(config))
        return res, min_cost

    def solve(self):
        for _ in range(len(self.prioritized_checker)):
            diff, transitions = heapq.heappop(self.prioritized_checker)
            for test_trans in transitions:
                self.next_depth_configs = []
                if len(self.cur_depth_configs) == 0:
                    self._add_to_next_depth(
                        self.Config(matchings={test_trans.cur_note.note_repr.abs_pos: test_trans})
                    )
                else:
                    for cur_depth_config in self.cur_depth_configs:
                        if test_trans.cur_note.note_repr.abs_pos in cur_depth_config.matchings:
                            self.next_depth_configs.append(cur_depth_config)
                        cur_depth_config_matchings = cur_depth_config.matchings.copy()
                        cur_depth_config_matchings[
                            test_trans.cur_note.note_repr.abs_pos
                        ] = test_trans
                        self._add_to_next_depth(
                            self.Config(matchings=cur_depth_config_matchings)
                        )
                self.cur_depth_configs = self.next_depth_configs.copy()
            valids = list(filter(self._is_valid_config, self.cur_depth_configs))
            if len(valids) > 0:
                return self._get_min_cost_config(valids)
        return [], 0
