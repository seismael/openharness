# Front Taxonomy: The Complete Exploration Surface

The loop does not chase a single axis. It explores a project across **fronts** — the
distinct kinds of work that can move a target forward or protect it. Coverage of every
front is mandatory; the *order* is decided by the [dispatch policy](dispatch-policy.md),
not hard-coded. This is what makes the loop generic, agnostic, and unrestricted: it
considers every direction the evidence supports and refuses to silently drop one.

A **front** is a stable category. A **sub-axis** is a concrete question inside a front
(the project profile names them). Each front declares: what it answers, the evidence
artifact a completed examination produces, the gate it must pass, and its exit
condition.

## The twelve fronts

| Front | Answers | Terminal evidence | Exit condition |
| :--- | :--- | :--- | :--- |
| `orient` | Where are we? What is the true baseline and current state? | reproduced baseline metric + clean/pushed state | baseline reproduced once; refreshed on drift |
| `discover` | What can this project *do* that we have not used? | updated `capabilities.md` | every declared surface inventoried; gaps explicit |
| `audit` | Where does the project diverge from its stated contracts, targets, or risks? | findings with source evidence | all findings decided or deferred with a trigger |
| `diagnose` | Why is the target metric where it is? What is the dominant drag/opportunity? | bounded diagnostic artifact (gap/funnel/profile) | the dominant component per cell is localized |
| `research` | What do we not yet know that blocks a decision? | a bounded synthesis with citations | open questions answered or marked UNKNOWN |
| `debug` | What is incorrect, unsafe, or inconsistent? | a fixed defect + regression test, or counter-evidence | each sub-axis VERIFIED-SOUND or defect resolved |
| `improve` | What bounded change raises the target metric without regression? | a dual-gated adoption (commit + push) | candidates tried until the frontier is exhausted |
| `harden` | Are risk, safety, limits, and integrity enforced? | enforced gate + test | every limit has a verified test |
| `performance` | Are latency/throughput/resources within target? | measured profile vs target | target met or honestly bounded |
| `pipeline` | Are data, artifacts, reproducibility, and CI sound? | integrity/reproducibility check | no unresolved integrity gap |
| `knowledge` | Is what we learned recorded so it compounds? | updated wiki leaves + validator VALID | every finding/decision/defect/capability recorded |
| `plan` | Is the target decomposed into measurable sub-targets and ranked moves? | current `target` + ranked `next_moves` | decomposition exists and is current |

## Rules

- **Coverage is a guarantee, not a preference.** Every front reaches a terminal status in
  the [coverage ledger](coverage-ledger.md); `UNEXPLORED` blocks completion unless
  explicitly bounded out by the profile.
- **Depth over breadth when the evidence points there.** A front may be revisited many
  times; the ledger records the strongest status reached, not the visit count.
- **Fronts are project-neutral.** A `diagnose` front is a diagnosis in any domain; the
  profile supplies the concrete commands and metrics. Never encode one project's
  specifics here.
- **A defect discovered in any front is a `debug` obligation first.** Fixing what is
  incorrect outranks further improvement in every domain.
