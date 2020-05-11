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
See `example_input.txt` in project directory for example input format. Write your input into `test_harmonies.txt`.
* First line of input is the initial state to start the solving process.
  * Write in 4 notes (see [here](#satbsolver-global-settings) for details). For reference, middle C is `C4`, and the nearest `B` is `B3`.
  * Keep all initial notes on one line.
* The following lines are chord formulae. These follow conventional formula formats. See the property `formula_matcher` in [satb_solver/template_parser.py](satb_solver/template_parser.py) for the specific syntax or see below for a simpler explanation.

### Formula Format
The chord formula is composed of the following parts **in order**:

| Component | Syntax | Example Usage | Description | Inclusion Symbol | Required |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Natural base note | `A`-`G` | `Fmaj` | Base natural note for chord formula (may not be base note for SATB chord after inversion is applied). | None | Yes |
| Base note accidental | `b` or `#` | `C#min` | Accidental for base formula note. Note that `bb` and `x` cannot be given. | None | No |
| Base triad | one of `min`, `maj`, `aug`, `dim` | `A#aug` | Basic third and fifth interval composition of chord. | None | Yes |
| Compound note accidental | `b` or `#` | `Dmin#11` | Modifies the compound chord note by either raising it or dropping it by a semitone. Note that `D#9` is ambiguous and will be interpreted as a 9th chord with base `D#`. Use single-note modification if the other case is intended. | None | No |
| Compound note | one of `7`, `9`, `11`, `13` | `C#7` | Specifies compound chord. Can be combined with base triads. No inclusion of `min`, `maj`, or `dim` implies dominant chord. | None | No |
| Sustained note | one of `sus`, `sus2`, `sus4` | `Amin-sus4` | Replaces third interval with either a major second or a perfect fourth. No number implies perfect fourth suspension. | `-` | No |
| Added note | `add` + `1`-`13` | `E7-add2` | _Not implemented yet._ | `-` | No |
| Single-note modification | `b` or `#` + `<chord position>` | `F9-#5` | Only either single- or multi-note modification can be done. Modifies any note already in chord by raising/lowering it by a semitone. | `-` | No |
| Multi-note modification | (`<single note mod>`, ...) | `D11-(b5,b9)` | Only either single- or multi-note modification can be done. Modifies several notes already in chord by raising/lowering it by a semitone. | `-` | No |
| Inversion | one of `6`, `64`, `65`, `43`, `42` | `Cmaj_6`, `Dmin7_43` | Specifies inversion of chord. No specification implies root inversion. | `_` (underscore) | No |

_See [Results](#results) for some examples._

### SATBSolver Global Settings
In [solver_config.yaml](solver_config.yaml), the following modifiable settings are offered:
* `voice_count`: Number of voices in input. **[4-6]**
* `include_inv`: When True, the solver will ensure that the base note of each chord matches the inversion of each chord formula. Otherwise, solver simply chooses the optimal base note. **[True/False]**
* `user_intermed`: When True, allows user to choose transition for each chord, when given options by solver. Otherwise, generates all optimal solutions. See [Results](#results) section for both cases. **[True/False]**

To run your input, call:
```bash
python3 solve_satb.py test_harmonies.txt
```

## Results
The result from the `example_input.txt` file is the following **without user intervention**. Each solution is an optimal solution that transitions between chords using the fewest number of semitone differences.
```
Cmaj    Fmaj_64    Dmin7_42    Ebmaj7_43    Bb7    Baug    Abmin7-b5_42    Dmin_6    Ebdim7    Abmaj7-#3_43    Gmaj-sus    G13    Cmaj
1       2          3           4            5      6       7               8         9         10              11          12     13      

1 Optimal Solution:

-------------------------------------------------------------------------------------------------------------------------------------------
Cost: 93

C5      C5      D5      Eb5     F5      Fx5     Ab5     A5      Gb5     C#5     C5      B4      C5      
E4      F4      F4      G4      Ab4     Fx4     Cb4     A4      Bbb4    G4      G4      F4      E4      
G3      A3      A3      D4      D4      D#4     Ebb4    D4      Dbb4    Ab3     D4      E4      C4      
C3      C3      C3      Bb3     Bb3     B3      Gb3     F3      Eb3     Eb3     G3      G3      C3      
1       2       3       4       5       6       7       8       9       10      11      12      13      
-------------------------------------------------------------------------------------------------------------------------------------------

Solutions generated in: 0.08413 sec
```

With the global setting `user_intermed` set to `True`, the following is an example of an intermediate step that requires user intervention:
```
3 Optimal Options: Ab7_65 -> Bbmin_6
--------------------------------------------------------

Eb5             ⎡       Db5     Bb4     Bb4      ⎤      
Gb4             ⎢       F4      F4      F4       ⎥      
Ab3      -->    ⎢       Bb3     F3      Bb3      ⎥      
Eb3             ⎢       Bb2     Db3     Db3      ⎥      
Ab2             ⎢       F2      Bb2     F2       ⎥      
C2              ⎣       Db2     Db2     Db2      ⎦      
                        1       2       3       
--------------------------------------------------------
Choose transition (type "back" or number of choice): 
```

To see other examples with more voices, check out the [examples](examples/) directory.

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
- [x] Allow user to choose intermediate chord configurations to reduce the number of final optimal solutions.
- [ ] Use library/software to display solutions on staves rather than in terminal.
- [x] Fully implement support for all chord modifications (*except* add-on notes).
- [x] Fully implement support for 5- and 6-part harmony (infrastructure already exists for it).
- [x] Fix base note of chords so they aren't manipulated during transition optimization.
