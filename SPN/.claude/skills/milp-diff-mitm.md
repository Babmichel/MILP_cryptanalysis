---
name: milp-diff-mitm
description: >
  Expert knowledge for working on a MILP-based Differential Meet-in-the-Middle
  (Diff-MITM) key recovery attack model for symmetric ciphers (SPN, bit-oriented),
  built on Gurobi. Use this skill whenever the user asks about: modifying or
  debugging the MILP model, improving resolution time, understanding variables or
  constraints, adding new ciphers, interpreting infeasibility, tuning Gurobi
  parameters, or extending the attack model (new techniques, new objective terms).
  Also trigger for any question about the files Diff-MITM.py, Common_bricks_for_attacks.py,
  or any *_key_schedule.py or *_parameters.py file.
---

# MILP Differential MITM Key Recovery – Expert Skill

## Project Overview

This framework automatically finds the best **Differential Meet-in-the-Middle (Diff-MITM)** key recovery attack on a block cipher, given a differential distinguisher. It models the entire attack as a **MILP problem solved by Gurobi**.

### Attack structure (5 segments in order)

```
[Structure: structure_rounds] → [Upper part: upper_rounds] → [Distinguisher: distinguisher_rounds] → [Lower part: lower_rounds]
```

- **Structure**: Parallel MITM zone where upper (part=0) and lower (part=1) computations overlap to produce a "matching" at intermediate rounds.
- **Upper part** (part=0): Forward computation from structure end toward distinguisher input.
- **Distinguisher**: Fixed differential trail (given as input, not optimized).
- **Lower part** (part=1): Backward computation from distinguisher output toward structure end.

Round index mapping:
- Structure: `[0, structure_rounds-1]`
- Upper part: `[structure_rounds, structure_rounds+upper_rounds-1]`
- Distinguisher: (implicit gap, not modeled)
- Lower part: `[structure_rounds+upper_rounds+distinguisher_rounds, ..+lower_rounds]`

---

## File Map

| File | Role |
|---|---|
| `Diff-MITM.py` | Main attack model: variable init, structure/upper/lower constraints, complexities, objective |
| `Common_bricks_for_attacks.py` | `MILP_bricks` base class: propagation primitives for SR, MC, MR, SB, AK, PB (both values and differences) |
| `*_key_schedule.py` | Cipher-specific: master key vars, subkey derivation, guess counting |
| `*_parameters.py` | Cipher configuration dict: block size, operation order, matrices, sbox sizes |
| `main.py` | Entry point: loads parameters, builds model, runs attack and key schedule |

---

## Variable Encoding

### Core dimensions

All main tensors are indexed as `[part, sens, round_index, state_index, row, column, value]`:

| Dim | Name | Values | Meaning |
|---|---|---|---|
| `part` | attack side | 0=upper, 1=lower | Which MITM half owns this variable |
| `sens` | propagation direction | 0=forward, 1=backward | Direction of computation |
| `round_index` | round | `[0, total_rounds-1]` | Round number |
| `state_index` | state within round | `[0, state_number-1]` | Position between operations (0=before first op, state_number-1=after last op) |
| `row`, `column` | cell position | `[0, block_row_size-1]` × `[0, block_column_size-1]` | Nibble/bit cell |

`state_number = len(operation_order) + 1`.

### `self.values[part, sens, round, state, row, col, v]` — Information state

One-hot over `v ∈ {0, 1, 2}`:
- `v=0`: **unknown** — cannot be computed by this part/direction
- `v=1`: **computable** — can be derived from known data
- `v=2`: **fixed** — set to a concrete value (enables state test or probabilistic cancellation)

Key invariant: `values[part, 0, r, s, row, col, 2] == values[part, 1, r, s, row, col, 2]` — a cell is fixed in both propagation directions simultaneously.

### `self.differences[part, sens, round, state, row, col, d]` — Differential state

One-hot over `d ∈ {0, 1}`:
- `d=0`: **active** — non-zero difference
- `d=1`: **inactive** — zero difference

### `self.value_in_structure[part, sens, round, state, row, col, v]` — Values inside structure only

Separate tensor from `values`, restricted to `round ∈ [structure_first, structure_last]`. Tracks only `{unknown=0, computable=1}` — `v=2` is forced to 0 everywhere. Used exclusively to determine where differences can propagate through SBs in the structure (see Structure section). It is strictly more permissive than `values` (starts from all-computable, while `values` starts from only fixed cells).

### XOR auxiliary variables (MC/MR)

`self.XOR_in_mc_values[(part, sens, round, column) + xor_combination_tuple + (v,)]`

Encode possible XOR combinations through the MixColumns/MixRows operation. `xor_combination` is a binary indicator vector (tuple) over the column/row. Used to track which linear combinations can be "fixed" (v=2) or cancelled.

For differences, the same structure is used:
`self.XOR_in_mc_differences[(part, sens, round, column) + xor_combination_tuple + (d,)]`
where `d=2` (a sentinel value, not 0/1) indicates a **probabilistic cancellation** at that XOR combination.

**Note**: `XOR_in_mc_values` is shared between `values` propagation and `value_in_structure` propagation. This is safe because `value_in_structure` is always at least as computable as `values`, so its constraints on the shared XOR variables are never more restrictive.

### Key schedule variables (SKINNY example)

`self.master_key[row, col, k]` — one-hot over `k ∈ {0,1,2}`:
- `k=0`: unknown to both parts
- `k=1`: known/guessed by upper part
- `k=2`: known/guessed by lower part

`self.master_key_count_guess[row, col, part]` — INTEGER: how many times subkey bit `(row,col)` is guessed across all rounds for `part ∈ {1,2}`.

`self.upper_subkey[round, row, col]`, `self.lower_subkey[round, row, col]` — BINARY: whether the subkey nibble is guessed by upper/lower at this round.

---

## Structure — Detailed Implementation

### Purpose and two-phase design

The structure serves two goals:
1. **Message construction**: generate F_up plaintext pairs (upper side) and F_down plaintext pairs (lower side) that the respective attack parts can process.
2. **Filtering**: check consistency between the two sides at matching points, using both value-level matching (common fixes) and difference-level matching.

### Phase 1 — Value construction (fix_up / fix_down)

The upper part fixes F_up elements in the structure. Starting from these fixed elements, it can compute F_up cells at the **exit point** of the structure via forward propagation. The exit point is `(structure_last_round_index, AK+1)` — the state immediately after the last AddRoundKey of the last structure round. The propagation covers ALL operations of rounds 0..structure_rounds-2, plus ONLY the AK of round structure_rounds-1 (the `condition` flag is set to False when the last AK is hit).

```
active_start_up = block_nibbles − count(values[0, 0, last_round, AK+1, ..., v=0])
constraint: active_start_up == fix_up
```

The lower part fixes F_down elements. Starting from these fixed elements, it can compute F_down cells at the **entry point** `(structure_first_round_index, AK)` — the state immediately before the first AddRoundKey — via backward propagation. The backward propagation covers ALL operations of rounds 1..structure_rounds-1 (full), plus only AK of round 0.

```
active_start_down = block_nibbles − count(values[1, 1, first_round, AK, ..., v=0])
constraint: active_start_down == fix_down
```

The constraints `active_start_X == fix_X` enforce bijectivity: each fixed element leads to exactly one computable cell at the exit/entry point (no wasted fixes, no free computations).

**Common fixes F_common**: cells fixed by BOTH upper (forward) and lower (backward) to the SAME value. These are counted by `common_fix_count` using McCormick linearization of `values[0,0,...,2] AND values[1,1,...,2]`. For MC/MR operations, the corresponding XOR combination in the inverse direction is computed via matrix transformation (`np.bitwise_xor.reduce(xor_combination * matrixes[1])`) to correctly match the forward and backward XOR auxiliary variables.

### Phase 2 — Difference-based filtering

Two separate propagations in `self.differences` track which differences each side knows to be zero inside the structure:

| Propagation | `(part, sens)` | Start | Direction |
|---|---|---|---|
| Lower forward | `(1, 0)` | `differences[1,0, round=0, AK, ..., 1] = 1` (all inactive) | Forward through structure |
| Upper backward | `(0, 1)` | `differences[0,1, last_round, AK+1, ..., 1] = 1` (all inactive) | Backward through structure |

The other two combinations (`(0,0)` upper forward, `(1,1)` lower backward) are disabled: `differences[0,0,...,0]=1` and `differences[1,1,...,0]=1` everywhere in the structure.

**No probabilistic annulations in structure**: `XOR_in_mc_differences[..., d=2] = 0` for all structure rounds. Therefore `propagation_MC_values` (not `propagation_MC_differences`) is used for MC/MR in the structure — zero differences behave like zero values under bijective linear maps.

### `propagation_SB_differences_structure` — key constraints

Two constraints per SB cell in the structure:

**1. Monotonicity** — if input difference is active, output must be active:
```python
d[part, sens, r, output_state, ..., 0] >= d[part, sens, r, input_state, ..., 0]
```
Equivalently (via one-hot): output inactive → input inactive. Implications:
- Lower forward: `low_after=1 → low_before=1`
- Upper backward: `up_before=1 → up_after=1`

**2. Value-knowledge requirement** — output difference is inactive only if the input value is known:
```python
d[part, sens, r, output_state, ..., 1] <= value_in_structure[part, not(part), r, input_state, ..., 1]
                                        + values[part, sens, r, input_state, ..., 2]
```
The key observation: `not(attack_side_index) == sens` for structure propagation (lower→sens=0=not(1), upper→sens=1=not(0)), so `value_in_structure[part, not(part), r, input_state, ...]` correctly refers to the same-part, same-direction value knowledge. Physical meaning: to know the output difference through a bijective S-box, you must know the input value (which uniquely determines the output difference given the input difference).

### `matching_differences` — counting matched zero-differences

For each interior structure round `r ∈ [0, structure_rounds-2]`, counts cells where BOTH the upper backward AND lower forward propagations agree on an inactive (zero) difference, around the SB layer:

```python
matching_differences[r, i, row, col] = 1  iff
    differences[0, 1, r+first_round, SB+i, row, col, 1] == 1  # upper backward: zero
    AND
    differences[1, 0, r+first_round, SB+i, row, col, 1] == 1  # lower forward: zero
```
for `i ∈ {0, 1}` (before SB and after SB).

**Deduplication within a round** (`matching_differences_not_twice`): a cell known-zero both before AND after the same SB should only count once (bijective SB: zero-in ↔ zero-out, so these are the same physical constraint). The formula:
```python
not_twice[r, row, col] = min(d[0,1, r, SB, row,col, 1],   # upper backward before SB
                              d[1,0, r, SB+1, row,col, 1])  # lower forward after SB
```
This correctly equals `min(M[r,0,row,col], M[r,1,row,col])` — i.e., it is 1 exactly when both M[r,0] and M[r,1] are 1 for the same word. Proof relies on the monotonicity properties from constraint 1 of `propagation_SB_differences_structure`: `not_twice=1 ⟺ up_before=1 AND low_after=1`, and by monotonicity `up_before=1 → up_after=1` and `low_after=1 → low_before=1`, so all four conditions hold simultaneously. ✓

```python
matching_differences_count[r] = sum(M[r,0,...]) + sum(M[r,1,...]) − sum(not_twice[r,...])
```

**Deduplication across rounds** — current approach and limitation:

```python
matching_differences_quantity = max_r( matching_differences_count[r] )
```

The MAX over interior rounds is **conservative (sub-optimal)**. Differences at different rounds are deterministically related through SR and MC (bijective), so the same information appears at each round in a transformed form. However, cells at different rounds can represent DIFFERENT physical constraints on the key material, and using both could give more filtering power.

**Known limitation**: the correct approach would allow summing contributions from multiple rounds while ensuring no "information unit" (traced through SR/MC) is counted twice. This requires tracking which matched differences at round r "subsume" which matched differences at round r+1. This is a planned improvement — the current MAX is a safe lower bound.

The constraint `matching_differences_quantity >= common_fix_count` ensures the difference matching is at least as effective as the common-fix filtering.

### Constraint `common_fix_count == fix_up == fix_down` — debug only

```python
# Diff-MITM.py lines 924-925
model.addConstr(common_fix_count == fix_up)
model.addConstr(common_fix_count == fix_down)
```
**This is a temporary debug constraint** that forces all fixes to be common (F_up = F_down = F_common). It dramatically restricts the search space (eliminates asymmetric fix configurations) and causes the terms `max_fix - fix_up` and `max_fix - fix_down` in T_up/T_down to cancel. It will be removed once the full model is validated. When removing it, also remove the hardcoded `common_fix_count == 6` line below it.

---

## Probabilistic Annulations

### Physical meaning

A **probabilistic annulation** occurs during a MixColumns/MixRows operation when two or more **active** input differences (non-zero) XOR together to produce a **zero** (inactive) output difference. This is not deterministic — it happens with probability **2^(−word_size)** per cancellation. Each such event "uses up" `word_size` bits of the attack's probability budget.

Global budget constraint (in `complexities()`):
```python
word_size * probabilist_annulation_up + word_size * probabilist_annulation_down + distinguisher_probability <= block_size
```
This ensures the total probability used (distinguisher + all annulations) does not exceed the block size.

### Two annulation counters

| Variable | `(part, sens)` | Where counted |
|---|---|---|
| `probabilist_annulation_up` | `(0, 1)` — upper part, **backward** direction | Backward difference propagation of the upper part through MC/MR |
| `probabilist_annulation_down` | `(1, 0)` — lower part, **forward** direction | Forward difference propagation of the lower part through MC/MR |

Counting in code (in `upper_part()` and `lower_part()`):
```python
# probabilist_annulation_up: part=0, sens=1 (upper backward differences)
probabilist_annulation_up_count += quicksum(
    XOR_in_mc_differences[(0, 1, round, col) + vector + (2,)]
    for round in range(upper_part_first_round, lower_part_last_round+1)
    ...
)
# probabilist_annulation_down: part=1, sens=0 (lower forward differences)
probabilist_annulation_down_count += quicksum(
    XOR_in_mc_differences[(1, 0, round, col) + vector + (2,)]
    for round in range(upper_part_first_round, lower_part_last_round+1)
    ...
)
```
`d=2` in the XOR_in_mc_differences tensor is the sentinel for a cancellation event (distinct from active=0 and inactive=1).

### Cross-assignment in complexity (important)

The annulations are **cross-assigned** to complexity terms:
```python
T_up   = upper_key_guess + state_test_up   + probabilist_annulation_DOWN + max_fix - fix_up
T_down = lower_key_guess + state_test_down + probabilist_annulation_UP   + max_fix - fix_down
```

**Why the cross**: `probabilist_annulation_down` (lower forward cancellations) appears in `T_up`, and `probabilist_annulation_up` (upper backward cancellations) appears in `T_down`. The interpretation: the cost of a probabilistic event that occurs in one direction is borne by the computation that must **verify** or **exploit** it — the opposite part must account for the probabilistic filtering it receives from the other side.

---

## Complexity Model

The objective minimizes `time_complexity`, defined as the max of four terms (each also includes `log2_repetitions`):

```
time_complexity = max(T_up, T_down, T_match, T_brute)  (all in nibbles/bits log2)
```

### Formulas (exact code)

```python
T_up    = upper_key_guess + state_test_up   + probabilist_annulation_down + max_fix_up_fix_down - fix_up
T_down  = lower_key_guess + state_test_down + probabilist_annulation_up   + max_fix_up_fix_down - fix_down
T_match = T_up + T_down - matching_differences_quantity + block_nibbles - 2*common_fix_count - common_key_guess
T_brute = T_match + log2_repetitions + key_space_size - key_guess_quantity - total_advantage
```

With `filter_state_test=True`: subtract `state_test_up + state_test_down` from `T_match` and add them to `key_guess_quantity` (state test cells become filtering steps rather than online cost).

With `trunc_diff=True`: add `(distinguisher_output_quantity - distinguisher_input_quantity)` to `T_down` and `distinguisher_output_quantity` to `T_match`.

Key quantities:
- `fix_up / fix_down`: number of fixed cells in upper/lower structure (state test budget)
- `common_fix_count`: cells fixed by both — reduces matching cost
- `matching_differences_quantity`: max number of differences matched across structure rounds (reduces T_match)
- `state_test_up / state_test_down`: fixed cells in upper/lower body (state test cost)
- `common_key_guess`: key bits known to both → guessed only once in matching
- `max_fix_up_fix_down`: linearized max(fix_up, fix_down) — the dominant fix cost

### Stored time complexity variables (for display)

```python
time_complexity_up    = T_up    + log2_repetitions
time_complexity_down  = T_down  + log2_repetitions
time_complexity_match = T_match + log2_repetitions
time_complexity_brute_force = T_brute  (no extra log2, it's already in T_brute)
```

### Objective weights

```python
minimize: time_complexity + 1.2*state_test_up + 1.2*state_test_down
          + 0.0001*for_display + 0.01*data_complexity - 0.001*common_fix_count
```
The 1.2 penalty on state test terms encourages solutions that avoid expensive state tests.

---

## Brute Force Term & Repetition Mechanism

### Purpose

After the MITM filtering (at cost `T_match`), some key candidates remain. The brute force step exhaustively tests the remaining key space. If the attack reduces the key space well, `T_brute < T_match` and the brute force is not the bottleneck. Otherwise, the attack can be **repeated** multiple times to amplify the filtering advantage.

### `key_guess_quantity` — total key bits identified

```python
key_guess_quantity = upper_key_guess + lower_key_guess - common_key_guess
                   + (matching_differences_quantity - common_fix_count)
```
With `filter_state_test`: adds `state_test_up + state_test_down`.

This represents the total key material recovered across the attack, which reduces the remaining brute force search.

### `advantage_per_run` — filtering power of one attack run

```python
advantage_per_run = max(0,  key_guess_quantity - T_match - ceil(distinguisher_probability / word_size))
```

Implemented as a linearized max via a binary indicator `delta_adv`:
```python
advantage_per_run >= key_guess_quantity - T_match - ceil(dist_prob/word_size)           # lb
advantage_per_run <= key_guess_quantity - T_match - ceil(dist_prob/word_size)
                   + key_space_size * (1 - delta_adv)                                    # ub when positive
advantage_per_run <= key_space_size * delta_adv                                          # ub = 0 when negative
```

**Interpretation**: `T_match` is the cost (in log2) to run the MITM; `key_guess_quantity` is how many key bits are identified. The difference is how many extra key bits are "filtered" beyond what the matching costs. The distinguisher probability `ceil(dist_prob/word_size)` is subtracted because the distinguisher itself already provides filtering — it is not "free" advantage.

### `attack_repetition` — number of extra runs

`attack_repetition = r` means the attack is run **r+1 times total** (r=0 → single run).

Encoded as a **one-hot** over `r ∈ {0, 1, ..., 10}` via `binary_indicator_repetitions[r]`:
```python
sum(binary_indicator_repetitions[r] for r in range(11)) == 1   # exactly one value
attack_repetition == sum(r * binary_indicator_repetitions[r] for r in range(11))
```

`max_repetetions = 10` is hardcoded in `complexities()`. Changing it affects the search space for repetitions.

### `log2_repetitions` — overhead cost of repeating

Precomputed table of `ceil(log2(r+1))` for each repetition level:
```
r=0 → 0,  r=1 → 1,  r=2 → 2,  r=3 → 2,  r=4 → 3,  r=5 → 3,
r=6 → 3,  r=7 → 3,  r=8 → 4,  r=9 → 4,  r=10 → 4
```
```python
log2_costs = [0 if r == 0 else math.ceil(math.log2(r+1)) for r in range(11)]
log2_repetitions_expr = sum(log2_costs[r] * binary_indicator_repetitions[r] for r in range(11))
```
This is the additional complexity (in log2 encryptions) just for running the attack r+1 times.

### `total_advantage` — cumulative filtering across all runs

Each run independently filters out `advantage_per_run` key candidates. Over `r+1` runs:
```
total_advantage = r * advantage_per_run
```
Linearized via McCormick for each `r` (product of integer × binary):
```python
possible_advantage[r] = r * advantage_per_run  when binary_indicator_repetitions[r]=1
                       = 0                     otherwise
```
Three constraints per r:
```python
possible_advantage[r] <= r * advantage_per_run
possible_advantage[r] <= r * key_space_size * binary_indicator_repetitions[r]
possible_advantage[r] >= r * advantage_per_run - r * key_space_size * (1 - binary_indicator_repetitions[r])
```
```python
total_advantage = sum(possible_advantage[r] for r in range(11))
```

### `T_brute` — final brute force cost

```python
T_brute = T_match + log2_repetitions + key_space_size - key_guess_quantity - total_advantage
```

- `T_match + log2_repetitions`: cost of running the full MITM r+1 times
- `key_space_size - key_guess_quantity`: remaining key bits not identified by MITM
- `- total_advantage`: additional candidates eliminated by repeating the attack

When `r=0` (single run), `log2_repetitions=0` and `total_advantage=0`, so:
```
T_brute = T_match + key_space - key_guess_quantity
```
i.e. standard brute force on the remaining key space after MITM filtering.

### When is repetition useful?

Repeating is worthwhile when `advantage_per_run > log2_cost_per_extra_run`, i.e., each additional run filters more candidates than it costs. Gurobi will automatically find the optimal `r` balancing these terms.

---

## Constraint Architecture

### Structure constraints (key)

1. `active_start_up == fix_up`: every fixed cell must yield one computable cell at `(last_round, AK+1)` via upper forward propagation
2. `active_start_down == fix_down`: every fixed cell must yield one computable cell at `(first_round, AK)` via lower backward propagation
3. `fix_down + fix_up - common_fix_count <= block_nibbles`: can't fix more than the full block
4. `matching_differences_quantity >= common_fix_count`: difference matching must cover at least common-fix filtering
5. `distinguisher_probability + word_size * common_fix_count >= block_size + 1`: forces attack to be non-trivial
6. `common_fix_count == fix_up == fix_down`: **debug-only constraint** to be removed — forces all fixes to be common, eliminating asymmetric configurations. Also accompanied by a hardcoded `common_fix_count == 6` line.

### Probability budget constraint

```python
word_size * probabilist_annulation_up + word_size * probabilist_annulation_down
    + distinguisher_probability <= block_size
```
Ensures total probability consumed (annulations + distinguisher) does not exceed the block size. Annulations beyond this bound would make the attack probability better than the birthday bound, which is invalid.

### McCormick linearizations

Product of two binary variables `x*y` is linearized as auxiliary binary `z` with:
```
z <= x,  z <= y,  z >= x + y - 1
```
Used for: `common_fix`, `common_fix_in_MC`, `master_key_count_guess_match`, `possible_advantage[r]`, etc.

### Key schedule (SKINNY)

- Key bit `(row,col)` for part `p` is "known" (`master_key[row,col,p]=1`) iff it has been guessed ≥ `tweakey_number` (=3 for TK3) times across all rounds.
- Threshold logic: `count >= 3 * master_key[..., p]` and `count <= 2 + total_rounds * master_key[..., p]`
- Common key guess (`master_key_count_guess_match`): bit guessed by both parts — its cost is subtracted once in T_match.

---

## Gurobi Parameters (current)

```python
IntFeasTol  = 1e-9       # very tight: important for counting constraints
Presolve    = 2          # aggressive
Cuts        = 3          # aggressive cuts
Heuristics  = 0.30       # high (default 0.05) — helps find feasible solutions
VarBranch   = 3          # strong branching
Aggregate   = 2          # AND/OR aggregation
MIPFocus    = 1          # balanced feasibility/optimality
ConcurrentMIP = 4        # 4 parallel strategies
MIPGap      = 0.10       # 10% gap acceptable
TimeLimit   = 7200*12    # 24h max
```

---

## Performance Bottlenecks & Known Issues

### Why it's slow

1. **GenConstrOr in MC/MR propagation**: `addGenConstrOr` variables for each XOR combination × each cell × each round × 2 parts × 2 sens. For large ciphers (128-bit, 10+ rounds), this creates tens of thousands of general constraints that Gurobi handles less efficiently than pure linear constraints.

2. **Integer counting variables**: `master_key_count_guess`, `state_test_up/down`, etc. are INTEGER not BINARY. Mixed-integer + many binary variables → large branch-and-bound tree.

3. **`attack_repetition` linearization**: The McCormick for `possible_advantage[r] = r * advantage_per_run * binary_indicator[r]` adds 3×(max_repetitions+1) constraints and (max_repetitions+1) auxiliary INTEGER variables. With `max_repetetions=10`, this is 33 constraints + 11 vars just for the repetition mechanism. Reducing `max_repetetions` to 5 cuts this in half.

4. **`common_fix_count == fix_up == fix_down` constraint**: While it reduces symmetry, it also forces Gurobi to simultaneously satisfy two tight equality constraints on sums of binary variables, which is notoriously hard.

5. **Objective with 4 competing terms**: The max-of-4 formulation for `time_complexity` requires indicator variables or big-M constraints that weaken LP relaxation.

6. **`advantage_per_run` linearization**: The `delta_adv` binary + 3 constraints for `max(0, ...)` add a small but non-trivial branching variable. If annulations are never expected, fixing `advantage_per_run=0` and `attack_repetition=0` can speed things up.

7. **`matching_differences_quantity = max over rounds`**: The current MAX formulation is simple but potentially sub-optimal. A SUM formulation requiring cross-round deduplication would be more expressive but adds significant complexity.

### Known model limitations

- **Multi-round difference matching**: The MAX over interior structure rounds is conservative. Cells from different rounds carry the same information when the operations between rounds are bijective and deterministic (no annulations). However, if the cells matched at round r and round r+1 represent DIFFERENT constraints (after SR/MC transforms), summing both would improve filtering — but requires deduplication to avoid counting the same information twice.

### Infeasibility patterns

Common causes of `model_infeasible.ilp`:
- `distinguisher_probability + word_size * common_fix_count >= block_size + 1` not satisfiable given the distinguisher inputs/outputs
- `matching_differences_quantity >= common_fix_count` impossible when distinguisher has too few active S-boxes at matching points
- `word_size*(pa_up + pa_down) + distinguisher_probability <= block_size` violated when the model tries to use too many annulations on top of an already-costly distinguisher
- Key schedule conflicts: `master_key_count_guess[row, col, 1] + master_key_count_guess[row, col, 2] <= 3 + total_rounds * master_key_count_guess_match` violated when both parts guess the same bit too many times

---

## How to Add a New Cipher

1. Create `Cipher/<name>_parameters.py` with the `cipher_parameters` dict:
   - Required keys: `Cipher_name`, `block_size`, `column_size`, `row_size`, `key_size`, `key_column_size`, `key_row_size`, `operation_order`, `sbox_sizes`
   - For SPN: add `shift_rows` and `matrixes` (forward matrix only — inverse computed automatically via SageMath)
   - For bit-oriented (GIFT/PRESENT style): add `permutations` instead of `matrixes`

2. Create `Key_schedule/<name>_key_schedule.py` inheriting `MILP_bricks`:
   - Implement `keyschedule()` calling `master_key_initialisation()` and `subkey_initialisation()`
   - Set `self.upper_subkey`, `self.lower_subkey`, `self.upper_key_guess`, `self.lower_key_guess`, `self.common_key_guess`

3. Create `Attack_parameters/<name>_<N>.py` with `attack_parameters` dict specifying rounds, distinguisher, etc.

---

## Debugging Checklist

When Gurobi reports INFEASIBLE:
1. Check `model_infeasible.ilp` — identify which constraint group appears most
2. Verify `distinguisher_input` and `distinguisher_output` positions match the `operation_order` (they reference `operation_order.index('SB')`)
3. Check `structure_rounds >= 2` (needed for `matching_differences_count` which is defined for `range(structure_rounds-1)`)
4. Verify `tweakey_number` in key schedule matches actual key schedule (TK1=1, TK2=2, TK3=3)
5. Try relaxing `common_fix_count == fix_up` to `common_fix_count <= fix_up` to test feasibility
6. Check probability budget: `word_size*(pa_up + pa_down) + distinguisher_probability <= block_size` — if the distinguisher probability is already close to `block_size`, there is no room for annulations

When solving but timing out:
1. Reduce `structure_rounds` by 1 and see if the model becomes tractable
2. Add `use_upper_bound=True` with `known_upper_bound` set to best known result
3. Try `specific_solution_search=True` to find any valid solution first
4. Reduce `max_repetetions` from 10 to 5 in `complexities()` (cuts ~30 constraints)
5. Fix `attack_repetition=0` (add `model.addConstr(attack_repetition==0)`) if repetition is not expected to help — removes the entire McCormick linearization block
6. Fix `probabilist_annulation_up=0` and `probabilist_annulation_down=0` if the cipher has no MC/MR or annulations are unlikely — removes probability budget branching
