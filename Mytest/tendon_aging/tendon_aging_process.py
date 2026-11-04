'''
This is the Tendon extracellular matrix aging simulation
'''

# import the bigraph libs
#from process_bigraph import allocate_core, Composite, process
from process_bigraph import allocate_core
from process_bigraph.composite import Process, Composite, Step
from process_bigraph.emitter import emitter_from_wires
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint, solve_ivp


# Simulation time and damage rates use seconds.
SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
ONE_YEAR = 365 * 24 * HOUR

# explicit registration of all processes and steps in the package
def build_core():
    our_core = allocate_core()
    our_core.register_link("CollagenDamage", CollagenDamage)
    our_core.register_link("FibroblastActivity", FibroblastActivity)
    our_core.register_link("SenescentFibroblastAccumulation", SenescentFibroblastAccumulation)
    our_core.register_link("HealthyFibroblast", HealthyFibroblast)
    our_core.register_link("FibroblastEpigeneticImpairment", FibroblastEpigeneticImpairment)
    return our_core

'''
Collagen damage from UV exposure, glycation, and MMP activity.
The UV and MMP break the collagen fibrils (fragment) while the glycation create non enzymatic cross-linking
'''
class CollagenDamage(Process):
    # dD/dt = kd * (1-D)
    # D(t): fraction of teh tendon collagen that is compromised
    # * kd is the rate of matrix damage accumulation.
    config_schema = {
        "damage_accumulation_rate": {
            "_type": "float",
            "_default": 3.0 / 1_000_000_000, # % of fragmented collagen per second per UV unit (1 UV unit = average UV in california)
        },
        "glycation_impact": {
            "_type": "float",
            "_default": 3.0 / 1_000_000_000, # % of cross linked collagen per second per glucose unit (1 glucose unit = average glucose in california)
        },
    }
    # config already passed during creation
    # this is executed after config is set
    def initialize(self, config=None):
        print("Process config:", self.config)
        if self.config["damage_accumulation_rate"] <= 0 or self.config["glycation_impact"] <=0 :
            raise ValueError("damage, Glycation must be over 0")

    # inputs as a dictionary
    def inputs(self):
        # Collagen stores are fractions (0 to 1); doses are relative levels.
        return {"IntactCollagen": "float", "glucose_dose": "float"}

    # output as a dictionary
    def outputs(self):
        return {"IntactCollagen": "float","FragmentedCollagen": "float", "CrosslinkedCollagen": "float"}

    # this is where the process happens
    def update(self, state, interval):
        # config parameters
        damage_impact = float(self.config["damage_accumulation_rate"])
        glycation_impact = float(self.config["glycation_impact"])
        # stores - inputs/outputs
        IntactCollagen = float(state["IntactCollagen"])
        glucose_dose = float(state["glucose_dose"])

        new_FragmentedCollagen_delta = IntactCollagen * damage_impact * interval
        new_CrosslinkedCollagen_delta = IntactCollagen * glycation_impact * glucose_dose * interval

        new_intactCollagen_delta = -(new_FragmentedCollagen_delta + new_CrosslinkedCollagen_delta)

        return {"IntactCollagen": new_intactCollagen_delta, "FragmentedCollagen": new_FragmentedCollagen_delta, "CrosslinkedCollagen": new_CrosslinkedCollagen_delta}

'''
    Fibroblast activity related to collagen 
    The fibroblasts regenerate the collagen: they reduce fragmented collagen and crosslinked collagen
    When the mechanical tension is low however they regenerate less and also increase MMP creation
'''
class FibroblastActivity(Process):
    # C = C0 (1 - a.S)
    # C(t): Effective maintenance capacity of resident tendon cells
    # a represents the loss of maintenance effectiveness associated with senescence.
    # Hypothesis: a = 1
    #  - kr * C * f(L) * D
    # * kr is the maximum effective matrix repair rate.
    # * f(L) describes how appropriate mechanical loading stimulates maintenance.

    config_schema = {
        "regeneration_rate": {
            "_type": "float",
            "_default": 1.0 / ONE_YEAR, # % of fragmented collagen and crosslinked collagen regenerated
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
        if self.config["regeneration_rate"] <= 0 :
            raise ValueError("impacts rates must be over 0")

    # inputs as a dictionary
    def inputs(self):
        # Collagen stores are fractions (0 to 1); doses are relative levels.
        return {"IntactCollagen": "float", "FragmentedCollagen": "float", "CrosslinkedCollagen": "float",
                "healthy_fibroblasts": "float", "fibroblasts_efficiency": "float", "mechanical_loading" : "float"}

    # output as a dictionary
    def outputs(self):
        return {"IntactCollagen": "float","FragmentedCollagen": "float", "CrosslinkedCollagen": "float"}

    # this is where the process happens
    def update(self, state, interval):
        # config parameters
        regeneration_rate = float(self.config["regeneration_rate"])
        max_regen = float(self.config["MAX_REGENERATION"])

        # stores - inputs/outputs
        FragmentedCollagen = float(state["FragmentedCollagen"])
        CrosslinkedCollagen = float(state["CrosslinkedCollagen"])
        healthy_fibroblasts = float(state["healthy_fibroblasts"])
        fibroblasts_efficiency = float(state["fibroblasts_efficiency"])
        mechanical_loading = float(state["mechanical_loading"])

        mechanical_loading_effect = mechanical_loading/ (mechanical_loading + 0.5)
        #print("Mechanical tension:", Mechanical_tension)
        total_regeneration_rate = regeneration_rate * healthy_fibroblasts * fibroblasts_efficiency * mechanical_loading_effect
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
        new_intactCollagen_delta = -(new_FragmentedCollagen_delta + new_CrosslinkedCollagen_delta)

        return {"IntactCollagen": new_intactCollagen_delta,
                "FragmentedCollagen": new_FragmentedCollagen_delta,
                "CrosslinkedCollagen": new_CrosslinkedCollagen_delta}

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
        "clearance_rate": {
            "_type": "float",
            "_default": 3.0 / 1_000_000_000,  # error rate per million
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
        #dS/dt = accumulation_rate * (1-S) - clearance_rate * S
        # * accumulation_rate is the rate of entry into senescence
        # * clearance_rate is the clearance rate of senescent cells.

        ### System Parameters
        # config parameters
        accumulation_rate = float(self.config["accumulation_rate"])
        clearance_rate = float(self.config["clearance_rate"])
        # stores - inputs/outputs
        senescent_fibroblasts = float(state["senescent_fibroblasts"])
        # time span
        t0 = 0.0
        t1 = float(interval)

        t_span = (t0, t1)  # Time range for solve_ivp (Start, End)
        t_points = np.linspace(t_span[0], t_span[1], 50)  # Time points for plotting/odeint

        # --- Solve Using odeint (Legacy) ---
        # Note: odeint expects the state variable (S) BEFORE time (t)
        def model_odeint(S, t, acc, clr):
            dSdt = acc * (1 - S) - clr * S
            return dSdt
        S0 = senescent_fibroblasts

        solution_odeint: np.ndarray = odeint(
            model_odeint,
            y0=S0,
            t=t_points,
            args=(accumulation_rate, clearance_rate)
        )

        new_senescent_fibroblasts = solution_odeint[-1,0]
        delta = new_senescent_fibroblasts - senescent_fibroblasts

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

'''
Fibroblast methylation due to age
The activity of fibroblasts is impaired due to the DNA methylation / age related epigentic due to age
(some protein producing DNA needed for the fibroblast activity is impaired or disabled)
'''
class FibroblastEpigeneticImpairment(Process):

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
        return {"fibroblasts_efficency": "float"}

    # output as a dictionary
    def outputs(self):
        return {"fibroblasts_efficiency": "float"}

    # this is where the process happens
    def update(self, state, interval):
        # config parameters
        accumulation_rate = float(self.config["accumulation_rate"])
        # stores - inputs/outputs
        fibroblasts_efficiency = float(state["fibroblasts_efficiency"])

        # accumulation rate every generation
        new_fibroblasts_efficiency = fibroblasts_efficiency * (1-accumulation_rate)
        delta = new_fibroblasts_efficiency - fibroblasts_efficiency

        return {"fibroblasts_efficiency": delta}

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

def tendon_aging_process_execute( exec_core, # execution core
                                sim_time , # duration of simulation in YEARS
                                senescence_accumulation_rate = 5 / 1_000_000_000, # per seconds
                                clearance_rate = 3 / 1_000_000_000,# per seconds
                                epigenetic_aging_rate = 0.0001,
                               ):
    sim = Composite(
            {
            "state" : {
                "IntactCollagen_top": 1.0,
                "FragmentedCollagen_top": 0.0,
                "CrosslinkedCollagen_top": 0.0,

                "healthy_fibroblasts_top": 1,
                "senescent_fibroblasts_top": 0,
                "fibroblasts_efficiency_top": 1.0,

                # shared model state
                "t": 0.0,
                "glucose_dose_top": 1.0,
                "mechanical_loading_top": 2.0,

                # our function  for Glycation and UV & Oxidation as input
                "damage": {
                    "_type": "process",
                    "address": "local:CollagenDamage", # local:<the name used in the register_link>
                    "config": {
                        "damage_impact": 1.0/1_000_000_000,
                        "glycation_impact": 1.2 / 1_000_000_000,
                    },
                    "interval": ONE_YEAR / 12, # defines the process update interval
                    "inputs": {"IntactCollagen":["IntactCollagen_top"],
                               "glucose_dose":["glucose_dose_top"]},
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
                        "MAX_REGENERATION" : 0.25
                    },
                    "interval": ONE_YEAR / 12,
                    "inputs": {"IntactCollagen":["IntactCollagen_top"],
                               "FragmentedCollagen":["FragmentedCollagen_top"],
                               "CrosslinkedCollagen":["CrosslinkedCollagen_top"],
                               "healthy_fibroblasts": ["healthy_fibroblasts_top"],
                               "fibroblasts_efficiency": ["fibroblasts_efficiency_top"],
                               "mechanical_loading": ["mechanical_loading_top"],},
                    "outputs": {"IntactCollagen":["IntactCollagen_top"],
                                "FragmentedCollagen":["FragmentedCollagen_top"],
                                "CrosslinkedCollagen":["CrosslinkedCollagen_top"]
                                },
                },

                # senescence process
                "senescence": {
                    "_type": "process",
                    "address": "local:SenescentFibroblastAccumulation",
                    "config": {
                        "accumulation_rate": senescence_accumulation_rate,
                        "clearance_rate": clearance_rate,
                    },
                    "interval": ONE_YEAR / 12,
                    "inputs": {"senescent_fibroblasts": ["senescent_fibroblasts_top"], },
                    "outputs": {"senescent_fibroblasts": ["senescent_fibroblasts_top"], },
                },

                # epigenetic aging process
                "epigenetic aging": {
                    "_type": "process",
                    "address": "local:FibroblastEpigeneticImpairment",
                    "config": {
                        "accumulation_rate": epigenetic_aging_rate,
                    },
                    "interval": ONE_YEAR / 12,
                    "inputs": {"fibroblasts_efficiency": ["fibroblasts_efficiency_top"], },
                    "outputs": {"fibroblasts_efficiency": ["fibroblasts_efficiency_top"], },
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
                        "fibroblasts_efficiency": ["fibroblasts_efficiency_top"],
                    }
                )
            }
        },
        core=exec_core,
    )
    # Run the composite for x units of composite time
    sim.run(sim_time)
    return sim

def inspect_processes(exec_core):
    # inspect ports with interface
    collagen_damage = CollagenDamage(
        {
            "UV_impact": 1.0 / 1_000_000_000,
            "glycation_impact": 1.0 / 1_000_000_000,
        },  core=exec_core)
    collagen_damage_interface = collagen_damage.interface()
    print("Process inputs schema:")
    print(exec_core.render(collagen_damage_interface["inputs"]))

    print("\nProcess outputs schema:")
    print(exec_core.render(collagen_damage_interface["outputs"]))

def tendon_aging_inspect_and_visualize(sim):

    # Inspect results
    records = sim.state["emitter"]["instance"].query()
    final_IntactCollagen = sim.state["IntactCollagen_top"]
    final_FragmentedCollagen = sim.state["FragmentedCollagen_top"]
    final_CrosslinkedCollagen = sim.state["CrosslinkedCollagen_top"]
    final_HealthyFibroblasts = sim.state["healthy_fibroblasts_top"]
    final_SenescentFibroblasts = sim.state["senescent_fibroblasts_top"]
    final_Fibroblasts_efficiency = sim.state["fibroblasts_efficiency_top"]

    print("n records:", len(records))
    print("first record:", records[0])
    print("last record:", records[-1])

    print("Final intact collagen:", final_IntactCollagen)
    print("Final fragmented collagen:", final_FragmentedCollagen)
    print("Final crosslinked collagen:", final_CrosslinkedCollagen)
    print("Final healthy fibroblasts:", final_HealthyFibroblasts)
    print("Final senescent fibroblasts:", final_SenescentFibroblasts)
    print("Final Fibroblasts efficiency:", final_Fibroblasts_efficiency)
    print("✅ Composite simulation ran")

    # Visualize
    import matplotlib.pyplot as plt

    # Convert emitter records (list of dicts) into time series
    times = [r["time"] / ONE_YEAR for r in records]
    Intact_collagen_vals = [r["IntactCollagen"] for r in records]
    fragmented_collagen_vals = [r["FragmentedCollagen"] for r in records]
    crosslinked_collagen_vals = [r["CrosslinkedCollagen"] for r in records]
    senescent_fibroblasts_vals = [r["senescent_fibroblasts"] for r in records]
    fibroblasts_efficiency_vals = [r["fibroblasts_efficiency"] for r in records]

    plt.figure(figsize=(8, 4))

    plt.plot(times, Intact_collagen_vals, label="Intact collagen (state)", linewidth=2)
    plt.plot(times, fragmented_collagen_vals, label="Fragmented collagen (state)", linewidth=2)
    plt.plot(times, crosslinked_collagen_vals, label="Crosslinked collagen (state)", linewidth=2)
    plt.plot(times, fibroblasts_efficiency_vals, label="Fibroblasts_efficiency (state)", linewidth=2)
    plt.plot(times,senescent_fibroblasts_vals, label="Senescent fibroblasts (state)", linewidth=2 )

    plt.xlabel("Time (years)")
    plt.ylabel("Collagen fraction")
    plt.title("Intact Collagen")
    plt.legend()
    plt.tight_layout()
    plt.show()