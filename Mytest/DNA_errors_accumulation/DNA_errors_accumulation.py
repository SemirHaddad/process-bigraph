import sys
import inspect
import numpy as np

# import the bigraph libs
#from process_bigraph import allocate_core, Composite, process
from process_bigraph import allocate_core
from process_bigraph.composite import Process, Step, Composite, as_process, as_step
from process_bigraph.emitter import emitter_from_wires

# GENERATION_TIME = time between divisions of an individual cell.
# every generation_time, the cells double (Mitosis)
SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
GENERATION_TIME = 20 * MINUTE

# explicit registration of all processes and steps in the package
def build_core():
    our_core = allocate_core()
    our_core.register_link("ErrorAccumulation", ErrorAccumulation)
    our_core.register_link("GoodDNA", GoodDNA)
    return our_core

# Error accumulation in DNA reproduction
class ErrorAccumulation(Process):
    # Schema = a data model as a dictionary
    # when the process is instantiated, an actual configuration dictionary is supplied:
    # The base Process/Edge initialization validates/fills that dictionary using config_schema and
    # stores the resulting configuration on the instance as: self.config
    config_schema = {
        "accumulation_rate": {
            "_type": "float",
            "_default": 3.0 / 1_000_000_000, # error rate per million
        },
    }
    # config already passed during creation
    # this si executed after config is set
    def initialize(self, config=None):
        print("Process config:", self.config)
        if self.config["accumulation_rate"] < 0 or self.config["accumulation_rate"] > 1:
            raise ValueError("Error Accumulation requires rate between 0 and 1")

    # inputs as a dictionary
    def inputs(self):
        # defective dna proportion in percent
        return {"defective_dna": "float", "number_of_cells": "integer"}

    # output as a dictionary
    def outputs(self):
        return {"defective_dna": "float","number_of_cells": "integer"}

    # this is where the process happens
    def update(self, state, interval):
        # config parameters
        accumulation_rate = float(self.config["accumulation_rate"])
        # stores - inputs/outputs
        defective_dna = float(state["defective_dna"])
        number_of_cells = int(state["number_of_cells"])

        # accumulation rate every generation
        good_dna = (1-defective_dna)
        new_good_dna = good_dna * (1-accumulation_rate)
        new_defective_dna = 1-new_good_dna
        delta = new_defective_dna - defective_dna

        # double number of cell every generation
        new_cells =  number_of_cells

        return {"defective_dna": delta, "number_of_cells": new_cells}

# Step to give the good DNA
class GoodDNA(Step):
    def inputs(self):
        return {
            "defective_DNA": "float"
        }

    def outputs(self):
        return {
            "good_DNA": "overwrite[float]"
        }

    def update(self, state, interval=None):
        count = state["defective_DNA"]

        return {
            "good_DNA": 1-count
        }

# execution
exec_core = build_core()

sim = Composite(
    {
        "state": {
            # shared model state
            "t": 0.0,
            "Defective DNA Top": 0.0,
            "cell_population": 1,
            "Good DNA Top": 0.0,

            # our function for error accumulation
            "error": {
                "_type": "process",
                "address": "local:ErrorAccumulation", # local:<the name used in the register_link>
                "config": {
                    "accumulation_rate": 1.0/1_000_000_000,
                },
                "interval": GENERATION_TIME, # defines the process update interval
                "inputs": {"defective_dna":["Defective DNA Top"],
                           "number_of_cells":["cell_population"]},
                "outputs": {"defective_dna":["Defective DNA Top"],
                            "number_of_cells": ["cell_population"]},
            },

            # Step: to give the good DNA ratio
            "good_DNA_step": {
                "_type": "step",
                "address": "local:GoodDNA",
                "inputs": {
                    "defective_DNA": ["Defective DNA Top"]
                },
                "outputs": {
                    "good_DNA": ["Good DNA Top"]
                }
            },

            # Emitter: record selected wires at each simulation tick
            "emitter": emitter_from_wires(
                {
                    "time": ["global_time"],
                    "error": ["Defective DNA Top"],
                    "good_DNA": ["Good DNA Top"],
                    "number_of_cells": ["cell_population"],
                }
            )
        }
    },
    core=exec_core,
)

# inspect ports with interface
error_process = ErrorAccumulation({"accumulation_rate": 1.0e-9},  core=exec_core)
ErrorAccumulation_interface = error_process.interface()
print("Process inputs schema:")
print(exec_core.render(ErrorAccumulation_interface["inputs"]))

print("\nProcess outputs schema:")
print(exec_core.render(ErrorAccumulation_interface["outputs"]))

# Run the composite for 10.0 units of composite time
sim.run(50.0 * GENERATION_TIME)

# Inspect results
records = sim.state["emitter"]["instance"].query()
final_DNA = sim.state["Defective DNA Top"]
final_GoodDNA = sim.state["Good DNA Top"]
final_cell_population = sim.state["cell_population"]
print("n records:", len(records))
print("first record:", records[0])
print("last record:", records[-1])

print("Final Defective DNA Top:", final_DNA)
print("Final Good DNA Top:", final_GoodDNA)
print("Final number of cells:", final_cell_population)
print("✅ Composite simulation ran")

# Visualize
import matplotlib.pyplot as plt

# Convert emitter records (list of dicts) into time series
times = [r["time"] for r in records]
error_vals = [r["error"] for r in records]

plt.figure(figsize=(8, 4))

plt.plot(times, error_vals, label="DNA Error rate (state)", linewidth=2)

plt.xlabel("time")
plt.ylabel("value")
plt.title("DNA Error accumulation")
plt.legend()
plt.tight_layout()
plt.show()