import math
import matplotlib.pyplot as plt
from requirements import verify_requirements

# ==================== Estimates ====================

ELEVATOR_BUILD_COST_USD      = 10e9
ELEVATOR_OPEX_USD_PER_YEAR   = 100e6
NUM_ELEVATORS                = 3
ANNUAL_CAPACITY_PER_ELEVATOR = 179_000

ROCKET_PAYLOAD_TONS          = 125 
ROCKET_CO2_KG_PER_LAUNCH     = 400_000

TOTAL_MASS  = 100e6 
START_YEAR  = 2050

# ==================== Launch Sites ====================
LAUNCH_SITES = {
    'Florida (Kennedy)': {
        'base_cost': 150_000_000,
        'monthly_multipliers': [1.05, 1.00, 0.98, 0.95, 0.92, 0.98,
                                 1.10, 1.15, 1.20, 1.10, 1.05, 1.08],
        'max_launches_per_month': 4,
        'co2_multiplier': 1.00,
    },
    'California (Vandenberg)': {
        'base_cost': 160_000_000,
        'monthly_multipliers': [1.00, 1.00, 0.98, 0.95, 0.92, 0.90,
                                 0.92, 0.95, 1.00, 1.02, 1.05, 1.02],
        'max_launches_per_month': 3,
        'co2_multiplier': 1.00,
    },
    'Texas (Boca Chica)': {
        'base_cost': 145_000_000,
        'monthly_multipliers': [1.00, 1.00, 1.02, 1.05, 1.10, 1.15,
                                 1.20, 1.18, 1.10, 1.00, 0.98, 0.95], 
        'max_launches_per_month': 5,
        'co2_multiplier': 1.00,
    },
    'Virginia (Wallops)': {
        'base_cost': 165_000_000,
        'monthly_multipliers': [1.10, 1.05, 1.00, 0.95, 0.90, 0.92,
                                 0.95, 1.00, 1.05, 1.05, 1.08, 1.12],
        'max_launches_per_month': 2,
        'co2_multiplier': 1.00,
    },
    'Alaska': {
        'base_cost': 140_000_000,
        'monthly_multipliers': [1.40, 1.35, 1.20, 1.05, 0.90, 0.85,
                                 0.85, 0.88, 1.00, 1.15, 1.30, 1.40],
        'max_launches_per_month': 2,
        'co2_multiplier': 1.05,
    },
    'Kazakhstan (Baikonur)': {
        'base_cost': 120_000_000,
        'monthly_multipliers': [1.30, 1.25, 1.10, 0.95, 0.90, 0.88,
                                 0.90, 0.92, 1.00, 1.10, 1.20, 1.30],
        'max_launches_per_month': 4,
        'co2_multiplier': 1.10,
    },
    'French Guiana (Kourou)': {
        'base_cost': 155_000_000,
        'monthly_multipliers': [0.95, 0.98, 1.00, 1.05, 1.10, 1.15,
                                 1.10, 1.05, 1.00, 0.95, 0.92, 0.93],
        'max_launches_per_month': 3,
        'co2_multiplier': 1.00,
    },
    'India (Satish Dhawan)': {
        'base_cost': 110_000_000,
        'monthly_multipliers': [0.90, 0.88, 0.90, 1.00, 1.10, 1.30,
                                 1.40, 1.35, 1.20, 0.95, 0.88, 0.88],
        'max_launches_per_month': 3,
        'co2_multiplier': 1.05,
    },
    'China (Taiyuan)': {
        'base_cost': 115_000_000,
        'monthly_multipliers': [1.10, 1.05, 0.98, 0.92, 0.90, 1.00,
                                 1.15, 1.10, 0.98, 0.95, 1.00, 1.05],
        'max_launches_per_month': 4,
        'co2_multiplier': 1.08,
    },
    'New Zealand (Mahia)': {
        'base_cost': 130_000_000,
        'monthly_multipliers': [0.90, 0.92, 0.98, 1.05, 1.10, 1.15,
                                 1.12, 1.08, 1.00, 0.95, 0.92, 0.88], 
        'max_launches_per_month': 3,
        'co2_multiplier': 1.00,
    },
}


# ==================== Helpers ====================

def _month_from_step(step: int, delta_time: float) -> int:
    """Calendar month (0=Jan … 11=Dec) for a given simulation step."""
    year = START_YEAR + step * delta_time
    return int(round((year % 1) * 12)) % 12


def get_launch_cost(site_name: str, month: int) -> float:
    """Effective USD cost per launch for a site in a given month (0=Jan, 11=Dec)."""
    s = LAUNCH_SITES[site_name]
    return s['base_cost'] * s['monthly_multipliers'][month]


# ==================== Planning ====================

def plan_launches(requirements: dict, delta_time: float = 1 / 12) -> dict:
    """
    Pre-compute the cost-minimal rocket launch schedule.

    Returns {(step, site_name): num_launches} covering all deadlines.
    """
    step_elevator = ANNUAL_CAPACITY_PER_ELEVATOR * NUM_ELEVATORS * delta_time

    deadline_targets: list[tuple[int, int]] = []   # (d_step, cumulative_launches_needed)
    for deadline_year, fraction in sorted(requirements.items()):
        d_step = round((deadline_year - START_YEAR) / delta_time)
        elevator_total = step_elevator * (d_step + 1)
        target_mass    = fraction * TOTAL_MASS
        launches = max(0, math.ceil((target_mass - elevator_total) / ROCKET_PAYLOAD_TONS))
        deadline_targets.append((d_step, launches))

    last_needed_step = max(
        (d_step for d_step, n in deadline_targets if n > 0),
        default=0
    )
    if last_needed_step == 0 and all(n == 0 for _, n in deadline_targets):
        return {}  

    all_slots: list[tuple[float, int, str]] = []   # (cost, step, site_name)
    for step in range(last_needed_step + 1):
        month = _month_from_step(step, delta_time)
        for site_name, info in LAUNCH_SITES.items():
            cost = info['base_cost'] * info['monthly_multipliers'][month]
            all_slots.append((cost, step, site_name))
    all_slots.sort() 

    remaining_cap: dict[tuple[int, str], int] = {
        (step, site): LAUNCH_SITES[site]['max_launches_per_month']
        for _, step, site in all_slots
    }

    schedule: dict[tuple[int, str], int] = {}
    committed = 0  

    for d_step, total_needed in deadline_targets:
        to_assign = total_needed - committed
        if to_assign <= 0:
            continue
        for _, step, site_name in all_slots:
            if to_assign <= 0:
                break
            if step > d_step:
                continue
            key   = (step, site_name)
            avail = remaining_cap[key]
            if avail == 0:
                continue
            n = min(avail, to_assign)
            schedule[key]    = schedule.get(key, 0) + n
            remaining_cap[key] -= n
            committed  += n
            to_assign  -= n

    return schedule


# ==================== Simulation ====================

def simulate(requirements: dict, delta_time: float = 1 / 12) -> dict:
    """
    requirements : dict {year: fraction_of_total}, verified by verify_requirements().
    delta_time   : simulation timestep in years (default 1/12 = monthly).
    """
    verify_requirements(requirements)

    schedule       = plan_launches(requirements, delta_time)
    step_elevator  = ANNUAL_CAPACITY_PER_ELEVATOR * NUM_ELEVATORS * delta_time

    cost      = ELEVATOR_BUILD_COST_USD * NUM_ELEVATORS
    pollution = 0.0
    delivered = 0.0
    completion_year = None

    launches_per_site = {site: 0 for site in LAUNCH_SITES}
    years_log, delivered_log, cost_log, pollution_log = [], [], [], []

    max_year    = max(requirements.keys()) + 10
    total_steps = int((max_year - START_YEAR) / delta_time) + 1

    for step in range(total_steps):
        year  = START_YEAR + step * delta_time
        month = _month_from_step(step, delta_time)

        # Elevator delivery
        delivered += min(step_elevator, TOTAL_MASS - delivered)
        cost      += ELEVATOR_OPEX_USD_PER_YEAR * NUM_ELEVATORS * delta_time

        # Scheduled rocket launches for this step
        for site_name in LAUNCH_SITES:
            n = schedule.get((step, site_name), 0)
            if n:
                launches_per_site[site_name] += n
                cost      += n * get_launch_cost(site_name, month)
                pollution += n * ROCKET_CO2_KG_PER_LAUNCH * LAUNCH_SITES[site_name]['co2_multiplier']
                delivered += n * ROCKET_PAYLOAD_TONS

        years_log.append(year)
        delivered_log.append(min(delivered, TOTAL_MASS))
        cost_log.append(cost)
        pollution_log.append(pollution)

        if delivered >= TOTAL_MASS:
            completion_year = year
            break

    total_launches = sum(launches_per_site.values())

    return {
        'years':                   years_log,
        'mass_delivered':          delivered_log,
        'cumulative_cost':         cost_log,
        'cumulative_pollution_kg': pollution_log,
        'launches_per_site':       launches_per_site,
        'total_launches':          total_launches,
        'completion_year':         completion_year,
        'final_cost':              cost_log[-1]      if cost_log      else 0,
        'final_pollution_kg':      pollution_log[-1] if pollution_log else 0,
        'final_year':              years_log[-1]     if years_log     else START_YEAR,
    }


# ==================== Output ====================

def plot_results(results: dict, title: str = "Rocket + Elevator Model", show: bool = True):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(title)

    ax = axes[0]
    ax.plot(results['years'], [m / 1e6 for m in results['mass_delivered']], color='steelblue')
    ax.set_xlabel('Year')
    ax.set_ylabel('Mass Delivered (million metric tons)')
    ax.set_title('Cumulative Mass Delivered')

    ax = axes[1]
    ax.plot(results['years'], [c / 1e9 for c in results['cumulative_cost']], color='orange')
    ax.set_xlabel('Year')
    ax.set_ylabel('Cumulative Cost (USD billions)')
    ax.set_title('Cumulative Cost')

    ax = axes[2]
    ax.plot(results['years'],
            [p / 1e9 for p in results['cumulative_pollution_kg']],
            color='firebrick')
    ax.set_xlabel('Year')
    ax.set_ylabel('CO₂ Emissions (million metric tons)')
    ax.set_title('Cumulative Rocket CO₂ Emissions')

    plt.tight_layout()
    if show:
        plt.show()


def print_summary(results: dict):
    print("\n" + "=" * 65)
    print("ROCKET + ELEVATOR SIMULATION SUMMARY")
    print("=" * 65)
    if results['completion_year']:
        print(f"100% delivery year:    {results['completion_year']:.2f}")
    print(f"Simulation end year:   {results['final_year']:.2f}")
    print(f"Total rocket launches: {results['total_launches']:,}")
    print(f"Final cumulative cost: ${results['final_cost'] / 1e9:.2f}B")
    co2_mt = results['final_pollution_kg'] / 1e9   # kg → million metric tons
    print(f"Total rocket CO₂:      {co2_mt:.3f} million metric tons")
    print()
    print("Launches by site (greedy cheapest-first):")
    for site, n in sorted(results['launches_per_site'].items(), key=lambda x: -x[1]):
        if n > 0:
            print(f"  {site:<30} {n:>7,} launches")
    print("=" * 65)


# ==================== Entry point ====================

if __name__ == "__main__":
    from requirements import req_ex

    for req in req_ex:
        results = simulate(req)
        print_summary(results)
        plot_results(results, title=f"Rocket + Elevator  |  Requirements: {req}", show=True)
