import heapq
import math
from collections import namedtuple
from typing import Any, Dict, List, Tuple

from model.dt_def import MatchConfig, NotePosPair, Transition
from model.transition_rules import (AcceptableNoteFrequenciesRule,
                                    AllNotesMatchedRule,
                                    DominantNotesResolvingRule,
                                    ValidParallelIntervalRule,
                                    VoicesNotExceedingOctaveNorCrossingRule,
                                    VoicesWithinRangeRule)


class BFTransitionOptimizer:
    def __init__(self, prioritized_checker, transition_context):
        self.prioritized_checker = prioritized_checker
        self.transition_context = transition_context
        self.cur_depth_configs = []
        self.next_depth_configs = []
        self.checked = set()

    def _get_hashable_matchings(self, transitions: List[Transition]) -> int:
        return sum(math.sin(trans.cur_abs_pos * trans.next_abs_pos) for trans in transitions)

    def _add_to_next_depth(self, new_config: MatchConfig) -> None:
        hashable_config_matching = self._get_hashable_matchings(new_config.matchings.values())
        if hashable_config_matching not in self.checked:
            self.checked.add(hashable_config_matching)
            self.next_depth_configs.append(new_config)

    def _is_valid_config(self, config: MatchConfig) -> Any:
        ordered_matchings = sorted(
            [trans for trans in config.matchings.values()],
            key=lambda trans: trans.cur_abs_pos
        )
        # The order is important, doing common failures first.
        for validator in [
            AcceptableNoteFrequenciesRule,
            ValidParallelIntervalRule,
            VoicesNotExceedingOctaveNorCrossingRule,
            AllNotesMatchedRule,
            DominantNotesResolvingRule,
            VoicesWithinRangeRule
        ]:
            if not validator.validate(ordered_matchings, self.transition_context):
                return False
        return True

    def _get_min_cost_config(
        self, configs: List[MatchConfig]
    ) -> Tuple[List[NotePosPair], int]:
        def simplify_config(config):
            return {tr.next_pair for tr in config.matchings.values()}
        min_cost = 999999
        res = []
        for config in configs:
            cost = sum(match.min_diff if match.min_diff != -1 else match.abs_pos_diff
                       for match in config.matchings.values())
            if cost < min_cost:
                min_cost = cost
                res.clear()
                res.append(simplify_config(config))
            elif cost == min_cost:
                res.append(simplify_config(config))
        return res, min_cost

    def solve(self) -> Tuple[List[NotePosPair], int]:
        for _ in range(len(self.prioritized_checker)):
            diff, transitions = heapq.heappop(self.prioritized_checker)
            for test_trans in transitions:
                self.next_depth_configs = []
                # If there are no configurations present, make initial configuration
                if len(self.cur_depth_configs) == 0:
                    self._add_to_next_depth(
                        MatchConfig(matchings={test_trans.cur_abs_pos: test_trans})
                    )
                else:
                    for cur_depth_config in self.cur_depth_configs:
                        # Diff of -1 is sentinel value used to denote base note,
                        #  taking highest priority
                        if diff == -1:
                            self.next_depth_configs.append(cur_depth_config)
                            self._add_to_next_depth(
                                MatchConfig(matchings={test_trans.cur_abs_pos: test_trans})
                            )
                            continue
                        # If transition target is already matched, split off and
                        #  duplicate configuration
                        if test_trans.cur_abs_pos in cur_depth_config.matchings:
                            self.next_depth_configs.append(cur_depth_config)
                        cur_depth_config_matchings = cur_depth_config.matchings.copy()
                        cur_depth_config_matchings[test_trans.cur_abs_pos] = test_trans
                        self._add_to_next_depth(
                            MatchConfig(matchings=cur_depth_config_matchings)
                        )
                self.cur_depth_configs = self.next_depth_configs
            # If there are valid configurations, SUCCESS, otherwise, continue on
            #  with all invalid configurations.
            valids = list(filter(self._is_valid_config, self.cur_depth_configs))
            if len(valids) > 0:
                return self._get_min_cost_config(valids)
        # If no valid configurations could be found, indicate so
        return [], 0
