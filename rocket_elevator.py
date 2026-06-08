import math
import matplotlib.pyplot as plt
from requirements import verify_requirements

# ==================== Estimates ====================

ELEVATOR_BUILD_COST_USD      = 10e9
ELEVATOR_OPEX_USD_PER_YEAR   = 10e7
NUM_ELEVATORS                = 3
ANNUAL_CAPACITY_PER_ELEVATOR = 179_000

ROCKET_PAYLOAD_TONS    = 125
ROCKET_LAUNCH_COST_USD = 150_000_000
ERF_BASE_MW_M2         = 0.3

TOTAL_MASS  = 100e6 
START_YEAR  = 2050

# ==================== Launch Sites ====================
LAUNCH_SITES = {
    'Florida (Kennedy)':       {'max_launches_per_month': 20},
    'California (Vandenberg)': {'max_launches_per_month': 20},
    'Texas (Boca Chica)':      {'max_launches_per_month': 20},
    'Virginia (Wallops)':      {'max_launches_per_month': 20},
    'Alaska':                  {'max_launches_per_month': 20},
    'Kazakhstan (Baikonur)':   {'max_launches_per_month': 20},
    'French Guiana (Kourou)':  {'max_launches_per_month': 20},
    'India (Satish Dhawan)':   {'max_launches_per_month': 20},
    'China (Taiyuan)':         {'max_launches_per_month': 20},
    'New Zealand (Mahia)':     {'max_launches_per_month': 20},
}

ERF_SEASONAL_MULTIPLIER = {
    'Florida (Kennedy)':       [1.0, 1.0, 1.5, 2.0, 2.8, 3.5, 4.0, 3.5, 2.5, 1.8, 1.2, 1.0],
    'California (Vandenberg)': [1.0, 1.0, 1.5, 2.0, 2.8, 3.5, 4.0, 3.5, 2.5, 1.8, 1.2, 1.0],
    'Texas (Boca Chica)':      [1.0, 1.0, 1.5, 2.0, 2.8, 3.5, 4.0, 3.5, 2.5, 1.8, 1.2, 1.0],
    'Virginia (Wallops)':      [1.0, 1.0, 1.5, 2.0, 2.8, 3.5, 4.0, 3.5, 2.5, 1.8, 1.2, 1.0],
    'Alaska':                  [0.8, 0.8, 1.2, 2.2, 3.2, 4.2, 4.8, 4.2, 2.8, 1.5, 0.9, 0.8],
    'Kazakhstan (Baikonur)':   [0.9, 0.9, 1.4, 2.0, 3.0, 3.8, 4.2, 3.8, 2.6, 1.7, 1.1, 0.9],
    'French Guiana (Kourou)':  [2.0, 2.0, 2.0, 2.1, 2.2, 2.3, 2.3, 2.2, 2.1, 2.0, 2.0, 2.0],
    'India (Satish Dhawan)':   [1.5, 1.5, 2.0, 2.5, 3.0, 3.5, 3.8, 3.5, 3.0, 2.2, 1.8, 1.5],
    'China (Taiyuan)':         [1.0, 1.0, 1.5, 2.0, 2.8, 3.5, 4.0, 3.5, 2.5, 1.8, 1.2, 1.0],
    'New Zealand (Mahia)':     [5.4, 5.4, 4.7, 3.4, 2.4, 1.4, 1.4, 1.6, 2.4, 3.8, 4.7, 5.4],
}


# ==================== Helpers ====================

def _month_from_step(step: int, delta_time: float) -> int:
    """Calendar month (0=Jan … 11=Dec) for a given simulation step."""
    year = START_YEAR + step * delta_time
    return int(round((year % 1) * 12)) % 12


def get_launch_cost() -> float:
    return ROCKET_LAUNCH_COST_USD


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
        for site_name in LAUNCH_SITES:
            all_slots.append((ROCKET_LAUNCH_COST_USD, step, site_name))
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

    elevator_finish = START_YEAR + math.ceil(TOTAL_MASS / (ANNUAL_CAPACITY_PER_ELEVATOR * NUM_ELEVATORS))
    max_year    = max(max(requirements.keys()), elevator_finish) + 10
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
                cost      += n * get_launch_cost()
                pollution += n * ERF_BASE_MW_M2 * ERF_SEASONAL_MULTIPLIER[site_name][month]
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
        'cumulative_erf':   pollution_log,
        'launches_per_site':       launches_per_site,
        'total_launches':          total_launches,
        'completion_year':         completion_year,
        'final_cost':              cost_log[-1]      if cost_log      else 0,
        'final_erf':               pollution_log[-1] if pollution_log else 0,
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
    ax.plot(results['years'], results['cumulative_erf'], color='firebrick')
    ax.set_xlabel('Year')
    ax.set_ylabel('Cumulative ERF (mW/m²)')
    ax.set_title('Cumulative Rocket ERF')

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
    print(f"Total rocket ERF:      {results['final_erf']:.3f} mW/m2")
    print()
    print("Launches by site (greedy cheapest-first):")
    for site, n in sorted(results['launches_per_site'].items(), key=lambda x: -x[1]):
        if n > 0:
            print(f"  {site:<30} {n:>7,} launches")
    print("=" * 65)


# ==================== Requirement Sweep ====================

def sweep_deadline(deadline_years: list[int],
                   fraction: float = 1.0,
                   delta_time: float = 1 / 12) -> list[dict]:
    """
    Run simulate() for each deadline year and collect outcomes.

    For each year in deadline_years, builds requirements {year: fraction}
    and records completion_year, final_erf, total_launches, and final_cost.
    This shows how aggressiveness of the deadline drives rocket use and pollution.
    """
    results = []
    for year in deadline_years:
        r = simulate({year: fraction}, delta_time)
        results.append({
            'deadline_year':   year,
            'completion_year': r['completion_year'],
            'final_erf':       r['final_erf'],
            'total_launches':  r['total_launches'],
            'final_cost':      r['final_cost'],
        })
    return results


def plot_sweep(sweep_results: list[dict],
               title: str = "Pollution vs Deadline",
               show: bool = True):
    deadlines = [r['deadline_year']  for r in sweep_results]
    erfs      = [r['final_erf']      for r in sweep_results]
    launches  = [r['total_launches'] for r in sweep_results]
    costs     = [r['final_cost'] / 1e9 for r in sweep_results]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle(title)

    ax = axes[0]
    ax.plot(deadlines, erfs, color='firebrick', marker='o', markersize=3)
    ax.set_xlabel('Deadline Year')
    ax.set_ylabel('Total ERF (mW/m²)')
    ax.set_title('Pollution vs Deadline')

    ax = axes[1]
    ax.plot(deadlines, launches, color='orange', marker='o', markersize=3)
    ax.set_xlabel('Deadline Year')
    ax.set_ylabel('Total Rocket Launches')
    ax.set_title('Launches vs Deadline')

    ax = axes[2]
    ax.plot(deadlines, costs, color='steelblue', marker='o', markersize=3)
    ax.set_xlabel('Deadline Year')
    ax.set_ylabel('Total Cost (USD billions)')
    ax.set_title('Cost vs Deadline')

    plt.tight_layout()
    if show:
        plt.show()


def print_sweep_summary(sweep_results: list[dict]):
    min_result = min(
        (r for r in sweep_results if r['completion_year'] is not None),
        key=lambda r: r['completion_year']
    )
    print("\n" + "=" * 65)
    print("DEADLINE SWEEP SUMMARY")
    print("=" * 65)
    print(f"Deadline range:        {sweep_results[0]['deadline_year']} – {sweep_results[-1]['deadline_year']}")
    print(f"Minimum completion:    {min_result['completion_year']:.2f}  "
          f"(deadline {min_result['deadline_year']}, "
          f"{min_result['total_launches']:,} launches, "
          f"ERF {min_result['final_erf']:.1f} mW/m2)")
    no_rocket = [r for r in sweep_results if r['total_launches'] == 0]
    if no_rocket:
        print(f"Elevator-only from:    deadline >= {no_rocket[0]['deadline_year']}")
    print("=" * 65)


# ==================== Entry point ====================

def _achievable_range() -> tuple[int, int]:
    rocket_per_month = sum(
        info['max_launches_per_month'] for info in LAUNCH_SITES.values()
    ) * ROCKET_PAYLOAD_TONS
    elev_per_month = ANNUAL_CAPACITY_PER_ELEVATOR * NUM_ELEVATORS / 12
    min_year = START_YEAR + math.ceil(
        math.ceil(TOTAL_MASS / (rocket_per_month + elev_per_month)) / 12
    )
    max_year = START_YEAR + math.ceil(
        math.ceil(TOTAL_MASS / elev_per_month) / 12
    )
    return min_year, max_year


if __name__ == "__main__":
    from requirements import req_ex

    # for req in req_ex:
    #     results = simulate(req)
    #     print_summary(results)
    #     plot_results(results, title=f"Rocket + Elevator  |  Requirements: {req}", show=True)

    lo, hi = _achievable_range()
    print(f"Achievable deadline range: {lo} – {hi}")
    deadlines = list(range(lo-10, hi + 10))
    sweep = sweep_deadline(deadlines, fraction=1.0)
    print_sweep_summary(sweep)
    plot_sweep(sweep, title="ERF and Completion Time vs Deadline Year", show=True)
