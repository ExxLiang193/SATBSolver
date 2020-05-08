import os
from typing import List

from model.exceptions import ExtensionError
from model.satb_elements import SATBSequence
from model.solver_config import get_config
from satb_solver.chord_transitioner import ChordTransitioner
from satb_solver.solution_interface import SolutionInterface
from satb_solver.template_parser import TemplateParser


class SATBSolver:
    def __init__(self, source_filepath):
        self.source_filepath = source_filepath
        self.template_parser = TemplateParser()
        self.chord_transitioner = ChordTransitioner()

    def read_source(self):
        if not self.source_filepath.endswith('.txt'):
            raise ExtensionError('Source file specified has incorrect extension. Required: .txt')
        path_to_file = os.path.abspath(self.source_filepath)
        if not os.path.exists(path_to_file):
            raise FileNotFoundError('Source file specified cannot be found')

        with open(path_to_file, 'r') as sf:
            sf_it = iter(sf)
            yield next(sf)
            for value in sf_it:
                yield value.strip()

    def solve(self):
        init_cond, *template = self.read_source()
        init_notes = self.template_parser.parse_init_cond(init_cond)
        chord_sequence = self.template_parser.parse_template(template.copy())
        if get_config()['user_intermed']:
            solutions = self.chord_transitioner.user_transition_chords(chord_sequence, init_notes)
        else:
            solutions = self.chord_transitioner.transition_chords(chord_sequence, init_notes)
        SolutionInterface().report_final_solutions(template.copy(), solutions)
