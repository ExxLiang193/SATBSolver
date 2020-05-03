import argparse
from time import time

from satb_solver.satb import SATBSolver


def parse_args():
    parser = argparse.ArgumentParser(description='Solve SATB harmony')
    parser.add_argument('filepath', type=str, nargs=1,
                        help='Absolute path to file with template harmonies')
    args = parser.parse_args()
    return args.filepath[0]


if __name__ == '__main__':
    source_filepath = parse_args()
    solver = SATBSolver(source_filepath)
    t0 = time()
    solver.solve()
    print()
    print('Solutions generated in: {} sec'.format(round(time() - t0, 5)))
