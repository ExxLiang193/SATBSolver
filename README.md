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
```
Cmaj    Fmaj_64    Dmin7_42    Ebmaj7_43    Bb7    Baug    Amin7-b5    Dmin_6    Ebdim7    Abmaj7-#3_43    D9    Gmin_6    Cmaj
1       2          3           4            5      6       7           8         9         10              11    12        13      

2 Optimal Solutions:

-----------------------------------------------------------------------------------------------------------------------------------
Cost: 100

C5      C5      D5      Eb5     F5      D#5     Eb5     D5      Eb5     G5      E5      D5      C5      
E4      F4      F4      G4      Ab4     Fx4     G4      F4      Gb4     Ab4     C5      Bb4     G4      
G3      A3      A3      D4      D4      D#4     C4      D4      Dbb4    C#4     F#4     G4      E4      
C3      C3      C3      Bb3     Bb3     B3      A3      F3      Eb3     Eb3     D4      Bb3     C4      
1       2       3       4       5       6       7       8       9       10      11      12      13      
-----------------------------------------------------------------------------------------------------------------------------------
Cost: 100

C5      C5      D5      Eb5     F5      D#5     C5      D5      Eb5     G5      E5      D5      C5      
E4      F4      F4      G4      Ab4     Fx4     G4      F4      Gb4     Ab4     C5      Bb4     G4      
G3      A3      A3      D4      D4      D#4     Eb4     D4      Dbb4    C#4     F#4     G4      E4      
C3      C3      C3      Bb3     Bb3     B3      A3      F3      Eb3     Eb3     D4      Bb3     C4      
1       2       3       4       5       6       7       8       9       10      11      12      13      
-----------------------------------------------------------------------------------------------------------------------------------

Solutions generated in: 0.17556 sec
```

## Implementation
The SATBSolver attempts to generate all solutions in the form of sequences that minimize the semitone change difference between chords in the initial chord formula template. Here is the process which it undergoes:
1. **Input Reading**
   * Reading in initial condition and chord formulae template.
2. **Formula Model Generation**
   * Matches each chord formula with its formula model, which specifies the chord composition which includes its intervals and note names (ex. A#).
   * Includes 7th, 9th, 11th, and 13th chords, suspended notes, altered notes, and added notes (though not all is supported yet).
3. **Model Sync**
   * Initial condition is matched with first chord model.
4. **Prioritized Breadth-first Search**
   * For each transition between chord formulae, the transitions that have the smallest amount of semitone changes are checked first. Compared to brute-force checking of all configurations, this approach is 5 - 10 times more efficient as it only checks a subset. All optimal transitions which are valid according to validation rules in `model/transition_rules.py` are found.
5. **Sequence Generation and DP-based Aggregation**
   * Each optimal transition branches off into a new sequence. Since sequences that arrive at the same chord configuration can have a differing number of total semitone changes, the sequence with lower changes is perpetuated.
6. **Report Optimal Sequences**
   * The globally optimal sequence solutions are found and outputted to the terminal as seen in the [Results](#results) section.

## TODO
* Allow user to choose intermediate chord configurations to reduce the number of final optimal solutions.
* Use library/software to display solutions on staves rather than in terminal.
* Fully implement support for all chord modifications (infrastructure already exists for it).
* Fully implement support for 5- and 6-part harmony (infrastructure already exists for it).
* Fix base note of chords so they aren't manipulated during transition optimization.

## Support
Currently only works for 4-part harmony. Infrastructure exists to execute 5- or 6-part harmony but there are hardcoded restrictions that will raise an error.

Currently only a subset of chord modifications will properly work. The amount of code changes to make this work is small, but I'll get to it when I have the time.
