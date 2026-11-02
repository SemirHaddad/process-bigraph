from skin_aging_process import build_core, inspect_processes, skin_aging_process_execute, ONE_YEAR, \
    skin_aging_inspect_and_visualize

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
    print("Welcome to the skin aging simulation test!")
    print("=" * 60)
    print("Mode: 1 - default   2 - interactive")
    print("=" * 60)
    mode = input("Select mode: ").strip()

    if mode == "2":
        sim_time = int(input("Number of years: ").strip()) * ONE_YEAR
        senescence_accumulation_rate = float(input("Senescence accumulation rate: ").strip())
        epigenetic_aging_rate = float(input("Epigenetic aging rate: ").strip())
    elif mode == "1":
        sim_time = 70*ONE_YEAR
        senescence_accumulation_rate = 0.0001
        epigenetic_aging_rate = 0.00001

    else:
        print("Invalid choice")
        exit()

    # execution
    exec_core = build_core()
    inspect_processes(exec_core)

    sim = skin_aging_process_execute(exec_core, sim_time, senescence_accumulation_rate, epigenetic_aging_rate)
    skin_aging_inspect_and_visualize(sim)
