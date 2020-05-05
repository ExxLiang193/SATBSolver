from collections import namedtuple

# Keep alphabetically listed
FormulaParts = namedtuple('FormulaParts', ['main_note', 'main_accid', 'triad', 'compound_accid',
                                           'compound_itvl', 'has_sus', 'sus_itvl', 'modif', 'inv'])
FreqRange = namedtuple('FreqRange', ['min_freq', 'max_freq'])
MatchConfig = namedtuple('MatchConfig', ['matchings'])  # Config -> MatchConfig
NotePosPair = namedtuple('NotePosPair', ['scale_pos', 'note_repr'])  # KeyPosPair -> NotePosPair
# SimpleMatching = namedtuple('SimpMatching', ['cur_pair', 'next_pair'])
Transition = namedtuple('Transition', ['min_diff', 'cur_pair', 'next_pair'])
TransitionContext = namedtuple('TransitionContext', ['cur_satb_chord', 'next_satb_chord'])
