'''
This is the skin extracellular matrix aging simulation
'''

# import the bigraph libs
#from process_bigraph import allocate_core, Composite, process
from process_bigraph import allocate_core
from process_bigraph.composite import Process, Composite
from process_bigraph.emitter import emitter_from_wires

# Simulation time and damage rates use seconds.
SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
ONE_YEAR = 365 * 24 * HOUR

# explicit registration of all processes and steps in the package
def build_core():
    our_core = allocate_core()
    our_core.register_link("GlycogenDamage", GlycogenDamage)
    return our_core

# Collagen damage from UV exposure, glycation, and MMP activity.
class GlycogenDamage(Process):
    config_schema = {
        "UV_impact": {
            "_type": "float",
            "_default": 3.0 / 1_000_000_000, # % of fragmented collagen per second per UV unit (1 UV unit = average UV in california)
        },
        "glycation_impact": {
            "_type": "float",
            "_default": 3.0 / 1_000_000_000, # % of cross linked collagen per second per glucose unit (1 glucose unit = average glucose in california)
        },
        "MMP_impact": {
            "_type": "float",
            "_default": 3.0 / 1_000_000_000, }, # % of fragmented collagen per second per MMP unit
    }
    # config already passed during creation
    # this is executed after config is set
    def initialize(self, config=None):
        print("Process config:", self.config)
        if self.config["UV_impact"] <= 0 or self.config["glycation_impact"] <=0 or self.config["MMP_impact"] <= 0:
            raise ValueError("UV, Glycation and MMP impacts must be over 0")

    # inputs as a dictionary
    def inputs(self):
        # Collagen stores are fractions (0 to 1); doses are relative levels.
        return {"IntactCollagen": "float",
                "UV_dose": "float", "glucose_dose": "float", "MMP1": "float"}

    # output as a dictionary
    def outputs(self):
        return {"IntactCollagen": "float","FragmentedCollagen": "float", "CrosslinkedCollagen": "float"}

    # this is where the process happens
    def update(self, state, interval):
        # config parameters
        UV_impact = float(self.config["UV_impact"])
        glycation_impact = float(self.config["glycation_impact"])
        MMP_impact = float(self.config["MMP_impact"])
        # stores - inputs/outputs
        IntactCollagen = float(state["IntactCollagen"])
        UV_dose = float(state["UV_dose"])
        glucose_dose = float(state["glucose_dose"])
        MMP1 = float(state["MMP1"])
        #FragmentedCollagen = float(state["FragmentedCollagen"])
        #CrosslinkedCollagen = float(state["CrosslinkedCollagen"])

        new_FragmentedCollagen_delta = IntactCollagen * (UV_impact * UV_dose + MMP_impact * MMP1) * interval
        new_CrosslinkedCollagen_delta = IntactCollagen * glycation_impact * glucose_dose * interval

        new_intactCollagen_delta = -(new_FragmentedCollagen_delta + new_CrosslinkedCollagen_delta)

        return {"IntactCollagen": new_intactCollagen_delta, "FragmentedCollagen": new_FragmentedCollagen_delta, "CrosslinkedCollagen": new_CrosslinkedCollagen_delta}

# execution
exec_core = build_core()

sim = Composite(
        {
        "state" : {
            "IntactCollagen_top": 1.0,
            "FragmentedCollagen_top": 0.0,
            "CrosslinkedCollagen_top": 0.0,

            "HealthyFibroblasts": 100,
            "SenescentFibroblasts": 0,

            "MMP1_top": 0.0,
            "IGF1_top": 1.0,

            # shared model state
            "t": 0.0,
            "UV_dose_top": 1.0,
            "glucose_dose_top": 1.0,

            # our function  for Glycation and UV & Oxidation as input
            "damage": {
                "_type": "process",
                "address": "local:GlycogenDamage", # local:<the name used in the register_link>
                "config": {
                    "UV_impact": 1.0/1_000_000_000,
                    "glycation_impact": 1.0 / 1_000_000_000,
                    "MMP_impact": 1.0 / 1_000_000_000,
                },
                "interval": ONE_YEAR, # defines the process update interval
                "inputs": {"IntactCollagen":["IntactCollagen_top"],
                           "UV_dose":["UV_dose_top"]
                           , "glucose_dose":["glucose_dose_top"],
                           "MMP1":["MMP1_top"]},
                "outputs": {"IntactCollagen":["IntactCollagen_top"],
                            "FragmentedCollagen":["FragmentedCollagen_top"],
                            "CrosslinkedCollagen":["CrosslinkedCollagen_top"],
                            },
            },

            # Emitter: record selected wires at each simulation tick
            "emitter": emitter_from_wires(
                {
                    "time": ["global_time"],
                    "IntactCollagen": ["IntactCollagen_top"],
                    "FragmentedCollagen": ["FragmentedCollagen_top"],
                    "CrosslinkedCollagen": ["CrosslinkedCollagen_top"],
                }
            )
        }
    },
    core=exec_core,
)

# inspect ports with interface
glycogen_process = GlycogenDamage(
    {
        "UV_impact": 1.0 / 1_000_000_000,
        "glycation_impact": 1.0 / 1_000_000_000,
        "MMP_impact": 1.0 / 1_000_000_000,
    },  core=exec_core)
glycogen_process_interface = glycogen_process.interface()
print("Process inputs schema:")
print(exec_core.render(glycogen_process_interface["inputs"]))

print("\nProcess outputs schema:")
print(exec_core.render(glycogen_process_interface["outputs"]))

# Run the composite for x units of composite time
sim.run(50.0 * ONE_YEAR)

# Inspect results
records = sim.state["emitter"]["instance"].query()
final_IntactCollagen = sim.state["IntactCollagen_top"]
final_FragmentedCollagen = sim.state["FragmentedCollagen_top"]
final_CrosslinkedCollagen = sim.state["CrosslinkedCollagen_top"]

print("n records:", len(records))
print("first record:", records[0])
print("last record:", records[-1])

print("Final intact collagen:", final_IntactCollagen)
print("Final fragmented collagen:", final_FragmentedCollagen)
print("Final crosslinked collagen:", final_CrosslinkedCollagen)
print("✅ Composite simulation ran")

# Visualize
import matplotlib.pyplot as plt

# Convert emitter records (list of dicts) into time series
times = [r["time"] / ONE_YEAR for r in records]
Intact_collagen_vals = [r["IntactCollagen"] for r in records]

plt.figure(figsize=(8, 4))

plt.plot(times, Intact_collagen_vals, label="Intact collagen (state)", linewidth=2)

plt.xlabel("Time (years)")
plt.ylabel("Collagen fraction")
plt.title("Intact Collagen")
plt.legend()
plt.tight_layout()
plt.show()
