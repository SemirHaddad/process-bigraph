from tendon_aging_process import build_core, inspect_processes, tendon_aging_process_execute, ONE_YEAR, \
    tendon_aging_inspect_and_visualize

# TODO: MAYBE add interactive visualization and parameters
# TODO: MAYBE investigate why crosslink collagen does not grow

# ---------------- Logging ----------------
import logging
logging.basicConfig(
    level=logging.CRITICAL,  # change to CRITICAL in prod
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("predictions")
logger.info("logger initialized")
logging.getLogger("urllib3").setLevel(logging.WARNING)
# end top level code

if __name__ == "__main__":
    print("=" * 60)
    print("Welcome to the tendon aging simulation test!")
    print("=" * 60)
    print("Mode: 1 - default   2 - interactive")
    print("=" * 60)
    mode = input("Select mode: ").strip()

    if mode == "2":
        sim_time = int(input("Number of years: ").strip()) * ONE_YEAR
        senescence_accumulation_rate = float(input("Senescence accumulation rate: ").strip())
        clearance_rate = float(input("Clearance rate: ").strip())
        epigenetic_aging_rate = float(input("Epigenetic aging rate: ").strip())
    elif mode == "1":
        sim_time = 70*ONE_YEAR
        senescence_accumulation_rate = 3 / 1_000_000_000  # per seconds
        clearance_rate = 1 / 1_000_000_000  # per seconds
        epigenetic_aging_rate = 0.001

    else:
        print("Invalid choice")
        exit()

    # execution
    exec_core = build_core()
    inspect_processes(exec_core)

    sim = tendon_aging_process_execute(exec_core, sim_time, senescence_accumulation_rate, clearance_rate, epigenetic_aging_rate)
    tendon_aging_inspect_and_visualize(sim)
