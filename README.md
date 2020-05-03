# SATBSolver
Given a sequence of chord formulae and an initial condition, finds optimal transition sequences.

## Environment
Developed on MacOS. Commands are executed in terminal.

## Setup
1. Create a virtual environment for Python3 and activate it.
```bash
pip install virtualenv
virtualenv -p python3 venv3
source venv3/bin/activate
```
2. Install requirements for project (may deprecate this need later on).
```bash
pip install -r requirements.txt
```

## Running the SATBSolver
See `example_input.txt` in project directory for input format. Write your input into `test_harmonies.txt`.
* First line of input is the initial state to start the solving process.
  * Write in 4 notes (may change in the future). For reference, middle C is `C4`, and the nearest `B` is `B3`.
  * Keep all initial notes on one line.
* The following lines are chord formulae. These follow conventional formula formats. See the property `formula_matcher` in `satb_solver/template_parser.py` for the specific syntax.
  * The first chord formula MUST match the initial condition. Validation has not been implemented for it yet.

To run your input, call:
```bash
python3 solve_satb.py test_harmonies.txt
```

## Results
The result from the `example_input.txt` file is the following. Each solution is an optimal solution that transitions between chords using the fewest number of semitone differences.
```bash
Cmaj    Fmaj7    Dmin7    Fdim    G7    Amin    Gmin7    Ebaug    Abmaj
1       2        3        4       5     6       7        8        9        

4 Optimal Solutions:

----------------------------------------------------------------------------
Cost: 44

C5      C5      C5      Cb4     D5      C5      D5      B4      Ab4     
E4      E4      D4      F4      F4      E4      F4      Eb4     Eb4     
G3      F3      F3      Ab3     G3      A3      G3      G3      Ab3     
C3      A2      A2      Cb2     B2      C3      Bb2     B2      C3      
1       2       3       4       5       6       7       8       9       
----------------------------------------------------------------------------
Cost: 44

C5      A4      A4      Cb4     D5      C5      D5      B4      Ab4     
E4      E4      D4      F4      F4      E4      F4      Eb4     Eb4     
G3      F3      F3      Ab3     G3      A3      G3      G3      Ab3     
C3      C3      C3      Cb2     B2      C3      Bb2     B2      C3      
1       2       3       4       5       6       7       8       9       
----------------------------------------------------------------------------
Cost: 44

C5      C5      C5      Cb4     B4      C5      D5      B4      Ab4     
E4      E4      D4      F4      F4      E4      F4      Eb4     Eb4     
G3      F3      F3      Ab3     G3      A3      G3      G3      Ab3     
C3      A2      A2      Cb2     D3      C3      Bb2     B2      C3      
1       2       3       4       5       6       7       8       9       
----------------------------------------------------------------------------
Cost: 44

C5      A4      A4      Cb4     B4      C5      D5      B4      Ab4     
E4      E4      D4      F4      F4      E4      F4      Eb4     Eb4     
G3      F3      F3      Ab3     G3      A3      G3      G3      Ab3     
C3      C3      C3      Cb2     D3      C3      Bb2     B2      C3      
1       2       3       4       5       6       7       8       9       
----------------------------------------------------------------------------

Solutions generated in: 0.11228 sec
```

## Implementation
TODO

## Support
Currently only works for 4-part harmony. Infrastructure exists to execute 5- or 6-part harmony but there are hardcoded restrictions that will raise an error.
