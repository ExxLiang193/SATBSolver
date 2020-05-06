import os
from typing import List

from model.exceptions import ExtensionError
from model.satb_elements import SATBSequence
from satb_solver.chord_transitioner import ChordTransitioner
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

    def report_solutions(self, template: List[str], solution_seqs: List[SATBSequence]) -> None:
        try:
            width = os.get_terminal_size()[0]
        except OSError:
            width = 50

        template = list(template)
        spaces = 4
        print((' ' * spaces).join(template))
        for i in range(len(template)):
            print('{0: <{1}}'.format(i + 1, len(template[i]) + spaces), end='')
        print('\n')

        seq_spaces = 8
        sol_num = len(solution_seqs)
        print("{} Optimal Solution{}:".format(sol_num, '' if sol_num == 1 else 's'))
        print()
        for sol in solution_seqs:
            print('-' * width)
            print('Cost: {}'.format(sol.seq_cost))
            print()
            sol_sequence = [sorted(chord.key_pos_pairs, key=lambda note: -note.note_repr.abs_pos)
                            for chord in sol.sequence]
            for line in zip(*sol_sequence):
                notes = [note.note_repr.note_name + str(note.note_repr.octave) for note in line]
                notes = ['{0: <{1}}'.format(note_name, seq_spaces) for note_name in notes]
                print(''.join(notes))
            print(''.join(['{0: <{1}}'.format(num, seq_spaces)
                           for num in range(1, len(sol_sequence) + 1)]))
        print('-' * width)

    def solve(self):
        init_cond, *template = self.read_source()
        init_notes = self.template_parser.parse_init_cond(init_cond)
        chord_sequence = self.template_parser.parse_template(template.copy())
        solutions = self.chord_transitioner.transition_chords(chord_sequence, init_notes)
        self.report_solutions(template.copy(), solutions)
