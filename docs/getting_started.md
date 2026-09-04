# Framework Overview 

One useful discovery already: the GitHub repository is actually **better documented architecturally than the Vivarium website suggests**. The current README points to a new `docs/architecture.md`, explicitly saying “start here to understand the whole system.”  The architecture document says the system is really two layers: **`bigraph-schema` defines what a model/document is**, while **`process-bigraph` defines what it does at runtime**.

The key mental model is also much simpler than the implementation initially makes it look:

1. A **document** is the structural description of a model: essentially a nested typed graph.
2. **Processes** are computational components with inputs and outputs.
3. Processes don't directly modify the global state. They return **deltas**, which the runtime merges into shared typed state.
4. A **Composite** is the runtime representation of one of these interconnected documents.
5. Processes can operate at different time scales, and Process-Bigraph provides the scheduler/orchestration that advances them.
6. `bigraph-schema` provides the graph/type/composition machinery underneath all of this.

So at a very high level I would currently draw it as:

```text
                    YOUR BIOLOGICAL MODEL
                           │
                           ▼
                 ┌──────────────────┐
                 │ Composite /      │
                 │ model document   │
                 └────────┬─────────┘
                          │
              wiring + typed shared state
                          │
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
   Process A          Process B          Process C
    ODE model         FBA model        Agent model
       │                  │                  │
       └────── return state updates / deltas ──────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ process-bigraph  │
                 │ runtime          │
                 │ scheduler        │
                 └────────┬─────────┘
                          │
                          ▼
                 typed global state
                          │
                          ▼
                    bigraph-schema
```

And an important conceptual distinction is:

**Vivarium is not primarily a biology simulator.** `process-bigraph` describes itself as a **composition protocol/runtime** for combining existing simulators and mathematical formalisms: ODE, FBA, agent-based, spatial, ML, etc.

That distinction is probably the missing piece if you're approaching Vivarium wondering, “Where is the actual biological simulation engine?”

There isn't one single biological engine. **Vivarium is the orchestration/composition engine.** The biology lives inside the Processes.

### How I suggest we learn it

Rather than reading `composite.py` from line 1 (it's roughly **148 KB**, which explains why this becomes painful quickly), I suggest we reverse-engineer Vivarium architecture-first.

I would take you through it in this order:

**1. Process**

What is the minimum contract of one simulation component?

```text
inputs()
outputs()
update(state, interval) → delta
```

**2. State + ports + wires**

How two processes actually communicate.

```text
Process A ──port──► shared store ◄──port── Process B
```

This is probably the single most important concept to understand.

**3. Composite**

How a collection of processes + stores becomes an executable simulation.

**4. Scheduler**

How Vivarium decides:

```text
which process runs
when
with what state
and how its output is merged
```

**5. Bigraph**

Only then dig into why they call it a *process bigraph*, and what the place graph / link graph abstraction buys them.

**6. A real biology example**

Take something very small, ideally an ODE model, and trace:

```text
biology
    ↓
Process subclass
    ↓
ports
    ↓
Composite
    ↓
runtime tick
    ↓
update()
    ↓
state delta
    ↓
next tick
```

That will make the more abstract bigraph machinery much easier to understand.

There is also one thing I would **not** start with: the newer template/site/investigation machinery. The architecture document spends a lot of time on “documents,” “sites,” “groundness,” `fill_sites`, higher-order DAGs, cached artifacts, etc.  Those are interesting, but they're a level above what you need to understand how a biological simulation actually works.

# Learning the framework
Yes. I’ve now traced enough of the source to give you a clean first architectural layer. The most important discovery is that **Vivarium’s core is conceptually much smaller than `composite.py` makes it appear**.

## 1. Start with the class hierarchy

The essential hierarchy is:

```text
bigraph_schema.Edge
        │
        ▼
      Open
      /  \
     /    \
 Process  Step
    │
    ▼
 Composite
```

`Composite` actually inherits from `Process`. The source describes it as a process containing a dynamic network of child Processes and Steps.

That is a major architectural idea:

> **A complete simulation can itself look like just another Process.**

So composition is recursive:

```text
Process
Process
Composite
    ├── Process
    ├── Process
    └── Composite
            ├── Process
            └── Process
```

This is how they can build multiscale simulations without the top-level engine needing to know whether a component is an equation, a cell, an organelle, or an entire sub-simulation.

---

# 2. What is a `Process`?

Ignore the framework implementation initially and look at an actual one from the repository:

```python
class IncreaseProcess(Process):
    config_schema = {
        'rate': {
            '_type': 'float',
            '_default': '0.1'}}

    def inputs(self):
        return {
            'level': 'float'}

    def outputs(self):
        return {
            'level': 'float'}

    def initial_state(self):
        return {
            'level': 4.4}

    def update(self, state, interval):
        return {
            'level': state['level'] * self.config['rate']}
```

This is real current Vivarium code.

Strip away their terminology and this is basically:

```text
Process =
    configuration
    + input interface
    + output interface
    + transition function
```

Or mathematically:

```text
Δstate = f(state, Δt, parameters)
```

That is the core abstraction.

A biological Process might therefore be:

```python
class Transcription(Process):

    def inputs(self):
        return {
            "gene": ...,
            "rna_polymerase": ...,
            "mrna": ...
        }

    def outputs(self):
        return {
            "mrna": ...
        }

    def update(self, state, interval):
        ...
        return {"mrna": delta_mrna}
```

The Process doesn't need to know where `mrna` exists in the complete cell model.

That separation is deliberate.

---

# 3. Very important: `update()` returns an **update**, not the new state

This confused me momentarily when reading their examples because this:

```python
return {
    'level': state['level'] * self.config['rate']
}
```

looks as though it replaces `level`.

Usually it doesn't.

It produces an **update/delta**. The schema determines how that delta gets applied.

For a normal numeric state:

```text
old state
   +
process update
   =
new state
```

For example, the README has:

```python
def update(self, state, interval):
    return {
        'level':
            state['level'] *
            self.config['rate'] *
            interval
    }
```

Starting with:

```text
level = 1.0
rate  = 0.5
dt    = 1
```

the Process emits:

```text
Δlevel = 0.5
```

and state becomes:

```text
1.0 + 0.5 = 1.5
```

Their example explicitly shows the trajectory `1.0 → 1.5 → ...`.

This architecture is important because the Process itself **doesn't mutate the simulation state**.

Instead:

```text
Process
   │
   │ update()
   ▼
 delta
   │
   ▼
Vivarium / bigraph-schema
   │
   │ apply delta according to type
   ▼
global state
```

So state ownership belongs to the framework, not to individual models.

---

# 4. `inputs()` and `outputs()` do NOT specify where the data comes from

This is probably the most important source-code concept to understand next.

When the Process says:

```python
def inputs(self):
    return {
        'level': 'float'
    }
```

it means:

> "I have an input port called `level`, and it expects a float."

It does **not** mean:

> "Read global variable `level`."

The mapping to actual simulation state happens elsewhere.

For example:

```python
'grow': {
    '_type': 'process',
    'address': 'local:Grow',

    'inputs': {
        'level': ['level']
    },

    'outputs': {
        'level': ['level']
    }
}
```

There are therefore two different things both unfortunately called `inputs`:

```text
PROCESS CLASS

inputs()
│
├── level : float
│
└── glucose : float

        Interface / ports
```

versus:

```text
COMPOSITE

inputs:
    level   → ['cell', 'mass']
    glucose → ['environment', 'glucose']

        Wiring
```

The repository documentation explicitly describes process inputs/outputs as **paths into shared stores**; changing the paths rewires the model.

Think of it like electronics:

```text
              Process
         ┌─────────────────┐
         │                 │
 glucose ├──► input        │
         │                 │
         │    equations    │
         │                 │
 biomass ├──► input        │
         │                 │
         └──────┬──────────┘
                │ output
                ▼
```

The Process specifies the **pins**.

The Composite specifies what the pins are **connected to**.

That is a very good architecture.

---

# 5. Processes don't communicate with each other

Suppose we have:

```text
Glycolysis
Transcription
Translation
Growth
```

Vivarium does not fundamentally wire:

```text
Glycolysis → Growth
```

Instead:

```text
                  Shared state

         glucose
             ▲
             │
             │
       ┌─────┴──────┐
       │ Glycolysis │
       └─────┬──────┘
             │
             ▼
            ATP
             ▲
             │
       ┌─────┴──────┐
       │   Growth   │
       └────────────┘
```

Both Processes interact through the state tree.

The documentation states this explicitly: processes never talk directly to one another; coupling is through shared stores.

This immediately explains why Vivarium is good at composing independently developed models.

An FBA model doesn't need to know anything about an ODE model.

They merely agree on:

```text
ATP
glucose
biomass
etc.
```

and their types.

---

# 6. Then what is a `Step`?

This distinction is quite elegant.

A **Process is time driven**.

A **Step is dependency/event driven**.

The type definitions make the distinction unusually clear:

```python
class ProcessLink(Link):
    interval: Float = ...
```

while:

```python
class StepLink(Link):
    priority: Float = ...
    _triggers: dict = ...
```

So think:

```text
Process
────────
run every Δt

update(state, interval)
```

versus:

```text
Step
────
run when its dependency changes / becomes available

update(state)
```

The repository's `OperatorStep` is a nice simple example:

```python
class OperatorStep(Step):

    def inputs(self):
        return {
            'a': 'float',
            'b': 'float'}

    def outputs(self):
        return {
            'c': 'float'}

    def update(self, inputs):
        a = inputs['a']
        b = inputs['b']

        if self.config['operator'] == '+':
            c = a + b

        return {'c': c}
```

No biological time integration is implied here.

It's closer to a node in a dataflow graph.

---

# 7. There are therefore **two execution models inside Composite**

This is something the documentation could explain much better.

### Temporal network

```text
                 simulation clock

      t=0        t=1        t=2        t=3
       │          │          │          │

Process A ●────────●──────────●──────────●
 interval=1

Process B ●───────────────────●
 interval=2

Process C ●────●────●────●────●────●────●
 interval=0.5
```

These are `Process` objects.

Each has its own `interval`.

Vivarium finds the next simulation time and executes whichever Processes are due.

The tick-lifecycle documentation confirms that `Composite.run()` walks its `process_paths`, extracts the state view for each Process, invokes it, and later applies the resulting update.

### Dependency network

Separately you have Steps:

```text
simulation result
       │
       ▼
   Analysis
       │
       ▼
    Figure
       │
       ▼
    Report
```

These form a dependency graph.

`scheduling.py` literally builds this graph from the Steps' input/output wire paths and determines which steps fire and in which layered order.

So conceptually:

```text
                    COMPOSITE
                        │
             ┌──────────┴───────────┐
             │                      │
             ▼                      ▼

      TEMPORAL ENGINE          DEPENDENCY ENGINE

        Processes                   Steps

       interval Δt             triggered by data
             │                      │
             ▼                      ▼

     biological dynamics      workflow / analysis
```

This is much clearer than thinking of Process and Step as minor variants of the same class.

---

# 8. Now we can understand `Composite`

This is the piece that brings everything together.

A Composite contains:

```text
State tree
+
Processes
+
Steps
+
Wiring
+
Scheduler
```

Simplified:

```text
                       Composite
                           │
             ┌─────────────┼──────────────┐
             │             │              │
             ▼             ▼              ▼
          STATE        PROCESSES        STEPS
             │             │              │
             │          temporal       dependency
             │          scheduler       scheduler
             │             │              │
             └─────────────┴──────────────┘
                           │
                           ▼
                     update state
```

And because:

```python
class Composite(Process):
```

that entire box can itself be embedded in another Composite.

That's how you get something like:

```text
Organism Composite
│
├── Liver Composite
│   ├── hepatocyte 1 Composite
│   ├── hepatocyte 2 Composite
│   └── ...
│
├── Blood Process
│
└── Kidney Composite
```

without changing the orchestration abstraction.

---

# 9. The five objects I would keep in your head

For now, forget "bigraph", "sites", "groundness", "investigation", etc.

Keep only this:

| Concept       | Think of it as                      |
| ------------- | ----------------------------------- |
| **Store**     | State variable / state tree         |
| **Port**      | Typed interface of a computation    |
| **Wire**      | Mapping port → state path           |
| **Process**   | `Δstate = f(state, Δt)`             |
| **Composite** | Runtime assembling all of the above |

And put `Step` on the side as:

> a dependency-driven computation rather than a time-driven Process.

That is enough to understand perhaps **70% of what matters for building biological models**.

---

# 10. Where I would navigate in the repo

Don't read the repository alphabetically.

Use this route:

```text
process_bigraph/
│
├── processes/examples.py      ← READ FIRST
│       │
│       └── actual Process/Step examples
│
├── composite.py
│       │
│       ├── Open
│       ├── Process             ← read class only
│       ├── Step                ← read class only
│       └── Composite           ← later
│
├── scheduling.py              ← understand after Process/Step
│
├── types/process.py
│       │
│       ├── ProcessLink
│       └── StepLink
│
└── emitter.py                 ← later
```

I would **not yet read**:

```text
templates.py
artifacts.py
bundle.py
composite_generator.py
distributed protocols
Ray
sites
investigations
```

They're secondary architecture.

### Next: the most important part

The natural next step is to take a **tiny two-Process model** and trace one iteration through the source:

```text
Composite.run()
      ↓
scheduler chooses Process
      ↓
extract input state through wires
      ↓
Process.invoke()
      ↓
Process.update(state, dt)
      ↓
delta
      ↓
project delta back through output wires
      ↓
bigraph-schema apply()
      ↓
new global state
```

That's where things like **stores, views, ports, wires, projection, `front`, and `apply_updates()`** will suddenly make sense.

I suggest we do exactly that next, rather than reading more classes in isolation.

Use the notebooks (tutorials) under /notebooks
