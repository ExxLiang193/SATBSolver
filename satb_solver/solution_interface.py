import os
from typing import List

from termcolor import colored

from model.dt_def import ChordNode
from model.satb_elements import SATBChord, SATBSequence


class SolutionInterface:

    def __init__(self, templ_padding: int = 4, seq_padding: int = 8):
        self.templ_padding = templ_padding
        self.seq_padding = seq_padding
        self.trans_padding = 6

    def _get_divider_len(self):
        try:
            width = os.get_terminal_size()[0]
        except OSError:
            width = 50
        return width

    def _order_chord_trans(self, chord):
        return sorted(chord.key_pos_pairs, key=lambda note: -note.note_repr.abs_pos)

    def _format_note(self, note):
        return note.note_repr.note_name + str(note.note_repr.octave)

    def report_intermed_solutions(self, cur_chord: SATBChord, next_nodes: List[ChordNode]):
        # Print transition info
        width = self._get_divider_len()
        sol_num = len(next_nodes)
        print(colored('{} Optimal Option{}: {} -> {}'.format(
            sol_num,
            '' if sol_num == 1 else 's',
            cur_chord.chord_formula.formula_name,
            next_nodes[0].chord.chord_formula.formula_name), 'green'))
        print('-' * width)
        print()

        # Print transition options
        cur_ordered_chord = self._order_chord_trans(cur_chord)
        ordered_chord_choices = [self._order_chord_trans(node.chord) for node in next_nodes]
        for i, line in enumerate(zip(*ordered_chord_choices)):
            notes = [self._format_note(note) for note in line]
            if i == 0:
                pre, post = '⎡', ' ⎤'
            elif i == len(cur_chord.key_pos_pairs) - 1:
                pre, post = '⎣', ' ⎦'
            else:
                pre, post = '⎢', ' ⎥'
            prev_info = self._format_note(cur_ordered_chord[i])
            trans_sym = '{:^{space}s}'.format(
                '-->' if i == (len(cur_chord.key_pos_pairs) - 1) // 2 else '',
                space=self.trans_padding
            )
            notes = [prev_info] + [trans_sym] + [pre] + notes + [post]
            notes = ['{0: <{1}}'.format(note_name, self.seq_padding)
                     for note_name in notes]
            print(''.join(notes))
        print(''.join(['{0: <{1}}'.format(num if num >= 1 else '', self.seq_padding)
                       for num in range(-2, len(ordered_chord_choices) + 1)]))
        print('-' * width)

        # Get user choice of transition or step back
        while True:
            choice = input('Choose transition (type "back" or number of choice): ')
            if choice == 'back':
                return -1, None
            try:
                choice = int(choice)
            except ValueError:
                pass
            if choice in range(1, len(ordered_chord_choices) + 1):
                return 1, int(choice) - 1
            else:
                print(colored('Invalid choice. Try again.', 'red'))

    def report_final_solutions(self, template: List[str], solution_seqs: List[SATBSequence]):
        # Print entire chord formula template
        print((' ' * self.templ_padding).join(template))
        for i in range(len(template)):
            print('{0: <{1}}'.format(i + 1, len(template[i]) + self.templ_padding), end='')
        print('\n')

        # Print full sequence solutions
        width = self._get_divider_len()
        sol_num = len(solution_seqs)
        print(colored('{} Optimal Solution{}:'.format(sol_num, '' if sol_num == 1 else 's'),
                      'green'))
        print()
        for satb_seq in solution_seqs:
            print('-' * width)
            print('Cost: {}'.format(satb_seq.seq_cost))
            print()
            ordered_chord_seq = [self._order_chord_trans(chord) for chord in satb_seq.sequence]
            for line in zip(*ordered_chord_seq):
                notes = [self._format_note(note) for note in line]
                notes = ['{0: <{1}}'.format(note_name, self.seq_padding)
                         for note_name in notes]
                print(''.join(notes))
            print(''.join(['{0: <{1}}'.format(num, self.seq_padding)
                           for num in range(1, len(ordered_chord_seq) + 1)]))
        print('-' * width)
