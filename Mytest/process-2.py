'''
This is the skin extracellular matrix aging simulation
'''

# import the bigraph libs
#from process_bigraph import allocate_core, Composite, process
from process_bigraph import allocate_core
from process_bigraph.composite import Process, Composite, Step
from process_bigraph.emitter import emitter_from_wires

# Simulation time and damage rates use seconds.
SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
ONE_YEAR = 365 * 24 * HOUR

# explicit registration of all processes and steps in the package
def build_core():
    our_core = allocate_core()
    our_core.register_link("GlycogenDamage", CollagenDamage)
    our_core.register_link("FibroblastActivity", FibroblastActivity)
    our_core.register_link("SenescentFibroblastAccumulation", SenescentFibroblastAccumulation)
    our_core.register_link("HealthyFibroblast", HealthyFibroblast)
    return our_core

'''
Collagen damage from UV exposure, glycation, and MMP activity.
The UV and MMP break the collagen fibrils (fragment) while the glycation create non enzymatic cross-linking
'''
class CollagenDamage(Process):
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

        new_FragmentedCollagen_delta = IntactCollagen * (UV_impact * UV_dose + MMP_impact * MMP1) * interval
        new_CrosslinkedCollagen_delta = IntactCollagen * glycation_impact * glucose_dose * interval

        new_intactCollagen_delta = -(new_FragmentedCollagen_delta + new_CrosslinkedCollagen_delta)

        return {"IntactCollagen": new_intactCollagen_delta, "FragmentedCollagen": new_FragmentedCollagen_delta, "CrosslinkedCollagen": new_CrosslinkedCollagen_delta}

'''
    Fibroblast activity related to collagen 
    The fibroblasts regenerate the collagen: they reduce fragmented collagen and crosslinked collagen
    When the mechanical tension is low however they regenerate less and also increase MMP creation
'''
class FibroblastActivity(Process):
    config_schema = {
        "regeneration_rate": {
            "_type": "float",
            "_default": 1.0 / ONE_YEAR, # % of fragmented collagen and crosslinked collagen regenerated
        },
        "mechanical_tension_regeneration_impact": {
            "_type": "float",
            "_default": 1.0, # % of regeneration decrease per point of mechanical tension
             },
        "mechanical_tension_MMP1_impact": {
            "_type": "float",
            "_default": 3.0 / 1_000_000_000, # MMP1 increase per unit of tension loss per year
        },
        "MMP1_MAX": {
            "_type": "float",
            "_default": 1.0,  # MAX MMP1 - this is an abstract value (no unit)
        },
        "MAX_REGENERATION": {
            "_type": "float",
            "_default": 0.1,  # Maximum total collagen fraction repaired per year (0.1 = 10%).
        },

    }

     # config already passed during creation
    # this is executed after config is set
    def initialize(self, config=None):
        print("Process config:", self.config)
        if self.config["regeneration_rate"] <= 0 or self.config["mechanical_tension_regeneration_impact"] <=0 or self.config["mechanical_tension_MMP1_impact"] <= 0:
            raise ValueError("impacts rates must be over 0")

    # inputs as a dictionary
    def inputs(self):
        # Collagen stores are fractions (0 to 1); doses are relative levels.
        return {"IntactCollagen": "float", "FragmentedCollagen": "float", "CrosslinkedCollagen": "float",
                "healthy_fibroblasts": "float"}

    # output as a dictionary
    def outputs(self):
        return {"IntactCollagen": "float","FragmentedCollagen": "float", "CrosslinkedCollagen": "float", "MMP1": "float"}

    # this is where the process happens
    def update(self, state, interval):
        # config parameters
        regeneration_rate = float(self.config["regeneration_rate"])
        mechanical_tension_regeneration_impact = float(self.config["mechanical_tension_regeneration_impact"])
        mechanical_tension_MMP1_impact = float(self.config["mechanical_tension_MMP1_impact"])
        mmp1_max = float(self.config["MMP1_MAX"])
        max_regen = float(self.config["MAX_REGENERATION"])

        # stores - inputs/outputs
        FragmentedCollagen = float(state["FragmentedCollagen"])
        CrosslinkedCollagen = float(state["CrosslinkedCollagen"])
        healthy_fibroblasts = float(state["healthy_fibroblasts"])

        Mechanical_tension = FragmentedCollagen + CrosslinkedCollagen
        #print("Mechanical tension:", Mechanical_tension)
        total_regeneration_rate = regeneration_rate * (1- (mechanical_tension_regeneration_impact * Mechanical_tension)) \
                                  * healthy_fibroblasts
        #print("total_regeneration_rate:", total_regeneration_rate)


        # Share one repair capacity across both damaged collagen pools.
        total_damage = FragmentedCollagen + CrosslinkedCollagen
        repair_fraction = max(0.0, min(1.0, total_regeneration_rate * interval))
        repair_capacity = max_regen * interval / ONE_YEAR
        total_repair = min(total_damage * repair_fraction, repair_capacity)

        if total_damage > 0:
            new_FragmentedCollagen_delta = -total_repair * FragmentedCollagen / total_damage
            new_CrosslinkedCollagen_delta = -total_repair * CrosslinkedCollagen / total_damage
        else:
            new_FragmentedCollagen_delta = 0.0
            new_CrosslinkedCollagen_delta = 0.0

        #print("FragmentedCollagen:", FragmentedCollagen)
        #print("new_FragmentedCollagen_delta:", new_FragmentedCollagen_delta)
        new_MMP1_delta = (
            mechanical_tension_MMP1_impact * Mechanical_tension * mmp1_max
            * interval / ONE_YEAR
        )

        new_intactCollagen_delta = -(new_FragmentedCollagen_delta + new_CrosslinkedCollagen_delta)

        return {"IntactCollagen": new_intactCollagen_delta,
                "FragmentedCollagen": new_FragmentedCollagen_delta,
                "CrosslinkedCollagen": new_CrosslinkedCollagen_delta,
                "MMP1": new_MMP1_delta}

'''
    Fibroblast become senescent and are less effective. 
    This is independent from the collagen matrix aging.
'''
class SenescentFibroblastAccumulation(Process):

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
        return {"senescent_fibroblasts": "float"}

    # output as a dictionary
    def outputs(self):
        return {"senescent_fibroblasts": "float"}

    # this is where the process happens
    def update(self, state, interval):
        # config parameters
        accumulation_rate = float(self.config["accumulation_rate"])
        # stores - inputs/outputs
        senescent_fibroblasts = float(state["senescent_fibroblasts"])

        # accumulation rate every generation
        good_fibroblasts = (1-senescent_fibroblasts)
        new_good_fibroblasts = good_fibroblasts * (1-accumulation_rate)
        new_senescent_fibroblasts = 1-new_good_fibroblasts
        delta = new_good_fibroblasts - new_senescent_fibroblasts

        return {"senescent_fibroblasts": delta}

# Step to give the healthy fibroblast ratio
class HealthyFibroblast(Step):
    def inputs(self):
        return {
            "senescent_fibroblasts": "float"
        }

    def outputs(self):
        return {
            "healthy_fibroblasts": "overwrite[float]"
        }

    def update(self, state, interval=None):
        count = state["senescent_fibroblasts"]

        return {
            "healthy_fibroblasts": 1-count
        }


# execution
exec_core = build_core()

sim = Composite(
        {
        "state" : {
            "IntactCollagen_top": 1.0,
            "FragmentedCollagen_top": 0.0,
            "CrosslinkedCollagen_top": 0.0,

            "healthy_fibroblasts_top": 1,
            "senescent_fibroblasts_top": 0,

            "MMP1_top": 0.0,

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
                    "glycation_impact": 1.2 / 1_000_000_000,
                    "MMP_impact": 1.0 / 1_000_000_000,
                },
                "interval": ONE_YEAR / 12, # defines the process update interval
                "inputs": {"IntactCollagen":["IntactCollagen_top"],
                           "UV_dose":["UV_dose_top"]
                           , "glucose_dose":["glucose_dose_top"],
                           "MMP1":["MMP1_top"]},
                "outputs": {"IntactCollagen":["IntactCollagen_top"],
                            "FragmentedCollagen":["FragmentedCollagen_top"],
                            "CrosslinkedCollagen":["CrosslinkedCollagen_top"],
                            },
            },

            "repair":{
              "_type" : "process",
                "address": "local:FibroblastActivity",
                "config": {
                    "regeneration_rate" : 1.0 / ONE_YEAR,
                    "mechanical_tension_regeneration_impact" : 1.0,
                    "mechanical_tension_MMP1_impact" : 0.5,
                    "MMP1_MAX" : 1.0,
                    "MAX_REGENERATION" : 0.10
                },
                "interval": ONE_YEAR / 12,
                "inputs": {"IntactCollagen":["IntactCollagen_top"],
                           "FragmentedCollagen":["FragmentedCollagen_top"],
                           "CrosslinkedCollagen":["CrosslinkedCollagen_top"],
                           "healthy_fibroblasts": ["healthy_fibroblasts_top"],},
                "outputs": {"IntactCollagen":["IntactCollagen_top"],
                            "FragmentedCollagen":["FragmentedCollagen_top"],
                            "CrosslinkedCollagen":["CrosslinkedCollagen_top"],
                            "MMP1":["MMP1_top"]},
            },

            "senescence": {
                "_type": "process",
                "address": "local:SenescentFibroblastAccumulation",
                "config": {
                    "accumulation_rate": 0.005 /12,
                },
                "interval": ONE_YEAR / 12,
                "inputs": {"senescent_fibroblasts":["senescent_fibroblasts_top"],},
                "outputs": {"senescent_fibroblasts":["senescent_fibroblasts_top"],},
            },

            # Step: to give the healthy fibroblast ratio
            "healthy_fibroblast_step": {
                "_type": "step",
                "address": "local:HealthyFibroblast",
                "inputs": {
                    "senescent_fibroblasts":["senescent_fibroblasts_top"],
                },
                "outputs": {
                    "healthy_fibroblasts": ["healthy_fibroblasts_top"]
                }
            },

            # Emitter: record selected wires at each simulation tick
            "emitter": emitter_from_wires(
                {
                    "time": ["global_time"],
                    "IntactCollagen": ["IntactCollagen_top"],
                    "FragmentedCollagen": ["FragmentedCollagen_top"],
                    "CrosslinkedCollagen": ["CrosslinkedCollagen_top"],
                    "senescent_fibroblasts": ["senescent_fibroblasts_top"],
                    "healthy_fibroblasts": ["healthy_fibroblasts_top"],
                }
            )
        }
    },
    core=exec_core,
)

# inspect ports with interface
glycogen_process = CollagenDamage(
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
sim.run(70.0 * ONE_YEAR)

# Inspect results
records = sim.state["emitter"]["instance"].query()
final_IntactCollagen = sim.state["IntactCollagen_top"]
final_FragmentedCollagen = sim.state["FragmentedCollagen_top"]
final_CrosslinkedCollagen = sim.state["CrosslinkedCollagen_top"]
final_HealthyFibroblasts = sim.state["healthy_fibroblasts_top"]
final_SenescentFibroblasts = sim.state["senescent_fibroblasts_top"]

print("n records:", len(records))
print("first record:", records[0])
print("last record:", records[-1])

print("Final intact collagen:", final_IntactCollagen)
print("Final fragmented collagen:", final_FragmentedCollagen)
print("Final crosslinked collagen:", final_CrosslinkedCollagen)
print("Final healthy fibroblasts:", final_HealthyFibroblasts)
print("Final senescent fibroblasts:", final_SenescentFibroblasts)
print("✅ Composite simulation ran")

# Visualize
import matplotlib.pyplot as plt

# Convert emitter records (list of dicts) into time series
times = [r["time"] / ONE_YEAR for r in records]
Intact_collagen_vals = [r["IntactCollagen"] for r in records]
fragmented_collagen_vals = [r["FragmentedCollagen"] for r in records]
crosslinked_collagen_vals = [r["CrosslinkedCollagen"] for r in records]

plt.figure(figsize=(8, 4))

plt.plot(times, Intact_collagen_vals, label="Intact collagen (state)", linewidth=2)
plt.plot(times, fragmented_collagen_vals, label="Fragmented collagen (state)", linewidth=2)
plt.plot(times, crosslinked_collagen_vals, label="Crosslinked collagen (state)", linewidth=2)

plt.xlabel("Time (years)")
plt.ylabel("Collagen fraction")
plt.title("Intact Collagen")
plt.legend()
plt.tight_layout()
plt.show()
