# Theoretical Foundations of Bigraphs & Simulation Orchestration
### A curriculum for researchers with a numerical/Python background, aiming to understand frameworks like `process-bigraph`

This curriculum moves in the order the theory itself was built: **motivation → formalism → dynamics → algebraic rigor**. Each phase lists what to read/watch, roughly how long it takes, and *why* it matters for reading bigraph-based simulation frameworks.

---

## Phase 0 — Orientation (a few hours)

Before the theory, see the target system once so the abstractions have something to attach to.

- **process-bigraph architecture doc** — the framework's own "start here" doc.
  `docs/architecture.md` in https://github.com/vivarium-collective/process-bigraph
- **Milner's own short motivating paper** (much shorter than the book, same ideas):
  Milner, R. — *"Bigraphs and their algebra"* (survey talk slides/notes exist online) or *"Pure Bigraphs: Structure and Dynamics"*, Information and Computation, 2006 — search the title, freely available as a PDF from Cambridge's Computer Laboratory.

**Goal:** recognize the vocabulary (place graph, link graph, controls, reaction rules) before it's formally defined.

---

## Phase 1 — Process Calculi & Concurrency Theory (2–4 weeks)

This is the "why" layer — the field bigraphs unify and generalize. If your background is numerical/scientific computing, this is likely your biggest gap, so don't skip it even though it looks like pure CS theory.

### Core concepts to learn
- Processes as first-class, composable units
- Communication via synchronization (CCS) vs. name-passing/mobility (π-calculus)
- Bisimulation and behavioral equivalence — what it means for two systems to "act the same"
- Structural congruence — rewriting a system's syntax without changing its behavior

### References
- **Glynn Winskel, *Topics in Concurrency* (Cambridge lecture notes, free PDF)** — the best free on-ramp; covers CCS, bisimulation, and Petri nets in one coherent set of notes written for a course.
  https://www.cl.cam.ac.uk/teaching/1617/TopConc/TopicsConc-1617.pdf
- **Robin Milner, *"The Polyadic π-calculus: A Tutorial"* (1993)** — Milner's own short, readable introduction to the π-calculus, written as a tutorial rather than a monograph. Search the title; widely mirrored as a free PDF.
- **Simon Heinzel, *"The Foundations of the π-Calculus"* (seminar paper)** — a gentle, example-driven walkthrough (satellites tracking an airplane) if Milner's own tutorial feels too dense at first.
  https://depend.cs.uni-saarland.de/fileadmin/user_upload/depend/neuhaeusser/concurrency_seminar_2011/Heinzel-Foundations_of_Pi.pdf
- **Video:** search "process calculus" / "pi-calculus lecture" on YouTube — university concurrency-theory courses (e.g. Saarland, MPI-SWS "Concurrency Theory" course pages linked below) periodically post recorded lectures; there isn't one single canonical video series the way there is for category theory, so lecture notes are the more reliable primary resource here.
  Course page with slide/notes archive: https://dzufferey.github.io/concurrency_theory_2017/

**Goal:** by the end, "a process is a unit of composition that communicates via typed channels" should feel intuitive — this is the exact mental model behind `process-bigraph`'s ports.

---

## Phase 2 — Petri Nets (1 week, can run parallel to Phase 1)

A much simpler formalism for concurrent/discrete dynamics. Petri nets are the "training wheels" version of bigraphical reactive systems' reaction rules, and they show up constantly in computational biology (metabolic networks, gene regulatory networks) so this phase pays for itself twice.

### References
- **Javier Esparza, *"Decidability and Complexity of Petri Net Problems — An Introduction"*** — a standard, approachable intro, referenced in most concurrency-theory course reading lists (see the Concurrency Theory 2017 course page above for the link).
- Any short "Petri nets for systems biology" tutorial — search that exact phrase; several free ones exist aimed specifically at your domain, since Petri nets are already a known modeling tool in metabolic/regulatory network research.

**Goal:** understand *token-based rewriting* — this is the direct ancestor of bigraph reaction rules.

---

## Phase 3 — Graph Theory Refresher (a few days, only if rusty)

Skip if you're already comfortable with graphs; otherwise, focus narrowly:

- Rooted trees/forests (→ place graphs: nesting/containment)
- Hypergraphs (→ link graphs: connectivity independent of nesting)

Any standard discrete math or graph theory reference chapter on trees and hypergraphs is sufficient — this part is genuinely the least novel piece of the theory.

---

## Phase 4 — Bigraphs Themselves (3–5 weeks)

Now the main event.

### Primary text
- **Robin Milner, *The Space and Motion of Communicating Agents* (Cambridge University Press, 2009).**
  This is *the* bigraphs book, written by the inventor. It is explicitly designed to be learned from — self-contained, with exercises and solutions. Table of contents runs: idea of bigraphs → defining bigraphs → algebra for bigraphs → sorting → reactions and transitions → bigraphical reactive systems → behavioral theory.
  ISBN 9780521738330 (paperback) / 9780521490306 (hardback).

### Companion/lighter reading
- **Blair Archibald, *"Practical Modelling with Bigraphs"*** — a much more recent, practically-oriented paper aimed at people who want to *use* bigraphs for modeling rather than derive the theory from scratch. Good to read alongside Milner's book as a "here's what this looks like in practice" anchor.
  https://arxiv.org/pdf/2405.20745
- **Review of Milner's book** (short, gives a bird's-eye map of the book's structure before you commit to reading it cover to cover):
  http://www.cs.umd.edu/~gasarch/BLOGPAPERS/milner.pdf

### Hands-on tooling (to make it concrete)
- **BigraphER** — command-line tool + OCaml library for defining and simulating bigraphical reactive systems, with export to the PRISM model checker. Working through its tutorial examples alongside the book is the single best way to make the formalism stop feeling abstract.
  https://www.dcs.gla.ac.uk/~michele/bigrapher.html
- **Bigraph Framework (Java)** — an alternative, more application/software-engineering-oriented implementation, useful if you want to see bigraphs embedded in a "real" object-oriented framework rather than an OCaml research tool.
  https://bigraphs.org/

**Goal:** be able to read a bigraph diagram (nesting = place graph, connecting curves = link graph) and a reaction rule, and understand what composition of two bigraphs means formally.

---

## Phase 5 — Category Theory (the algebraic backbone) (4–8 weeks, can be ongoing/background)

This explains *why* composition is well-behaved — the guarantee that composing valid bigraphs (composites of composites) always yields a valid bigraph. You don't need deep category theory, just enough to understand monoidal categories and composition as a first-class operation.

### References
- **Bartosz Milewski, *Category Theory for Programmers* — video lecture series (YouTube).**
  The best free, CS/programming-oriented (not pure-math-oriented) route in. Built from a programmer's intuition outward, not from set-theoretic foundations inward.
  Playlist: https://www.youtube.com/playlist?list=PLbgaMIhjbmEnaH_LTkxLI7FMa2HsnawM_
- **Companion free book/PDF** (transcribed from the same lectures, same author, CC-BY-SA licensed):
  https://github.com/hmemcpy/milewski-ctfp-pdf
- Focus specifically on: categories, functors, **monoidal categories**, and composition — you can treat topics like Kleisli categories, monads, and advanced functional-programming applications as optional/skippable for your purposes; they're aimed at Haskell/functional programmers and not essential for reading the bigraphs literature.

**Goal:** understand composition-as-an-operation well enough that "bigraphs form a precategory and composition is categorical composition" reads as a specific instance of a general pattern, not a new bespoke rule.

---

## Phase 6 — Closing the Loop: Bigraphical Reactive Systems & Multiscale Orchestration (2–3 weeks)

Return to `process-bigraph` itself with the full toolkit now in hand.

- Re-read `docs/architecture.md` and `docs/tick_lifecycle.md` in the process-bigraph repo — this time the design choices (typed deltas instead of mutation, composites-within-composites, multi-timestep scheduling) should read as direct engineering consequences of the theory rather than arbitrary API decisions.
- **Co-simulation standards, for the multiscale/multi-timestep orchestration problem specifically** (this is somewhat separate from bigraph theory but essential for *why* multiscale biological simulation is hard): look into the **FMI (Functional Mock-up Interface)** standard, the most mature general treatment of orchestrating heterogeneous solvers with different time semantics — useful even though it comes from engineering/systems co-simulation rather than biology.
- **Reference implementation to study end-to-end:** `spatio-flux`, a full multiscale model built on process-bigraph, composing spatial fields, particle dynamics, and metabolic processes.
  https://github.com/vivarium-collective/spatio-flux

---

## Suggested pacing

| Phase | Focus | Time |
|---|---|---|
| 0 | Orientation | Few hours |
| 1 | Process calculi (CCS, π-calculus, bisimulation) | 2–4 weeks |
| 2 | Petri nets | 1 week (parallel with 1) |
| 3 | Graph theory refresher | Few days, optional |
| 4 | Bigraphs proper (Milner's book + BigraphER) | 3–5 weeks |
| 5 | Category theory (Milewski) | 4–8 weeks, can run in background |
| 6 | Return to process-bigraph, co-simulation | 2–3 weeks |

Total: roughly **3–4 months** at a steady part-time pace, though Phase 5 (category theory) can keep running in the background well past that — it's the piece with the longest tail and the least urgency for merely *using* the framework productively.

---

## If you only have two weeks

Read, in order: the process-bigraph architecture doc → Heinzel's π-calculus paper (for intuition) → Archibald's "Practical Modelling with Bigraphs" paper → Milner's book chapters 1–3 (idea of bigraphs, defining bigraphs, algebra for bigraphs) → work through 2–3 BigraphER tutorial examples. Treat category theory as optional background reading rather than a prerequisite.
