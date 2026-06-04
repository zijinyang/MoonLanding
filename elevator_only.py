import numpy as np
import matplotlib.pyplot as plt

#===================== Estimates ====================
total_cost_per_elevator = 10e9
operational_cost_per_year_per_elevator = 100e6

#===================== Constants ====================
total_mass = 100e6
num_elevators = 3
annual_capacity_per_elevator = 179_000
start_year = 2050

def elevator_only_deterministic_model():
    years = []
    mass_delivered = []
    cumulative_cost = []
    
    year = start_year
    delivered = 0
    cost = total_cost_per_elevator * num_elevators 
    
    
    while delivered < total_mass:
        years.append(year)
        delivered = min(delivered + annual_capacity_per_elevator * num_elevators, total_mass)
        mass_delivered.append(delivered)
        cost += operational_cost_per_year_per_elevator * num_elevators
        cumulative_cost.append(cost)
        year += 1
    
    return {
        'years': years,
        'mass_delivered': mass_delivered,
        'cumulative_cost': cumulative_cost,
    }

def elevator_only_stochastic_model(num_simulations=1000, mean_capacity=annual_capacity_per_elevator * num_elevators, 
                                   std_dev=1000000, delta_time=1.0):
    """
    Simulates the elevator-only model with stochastic delivery amounts per time step.
    
    Parameters:
    - num_simulations: Number of simulation runs to perform.
    - mean_capacity: Average delivery capacity per time step (default is annual capacity).
    - std_dev: Standard deviation for the delivery capacity to introduce variability.
    - delta_time: Time step in years (e.g., 1.0 for yearly, 0.25 for quarterly, 1/12 for monthly, 1/52 for weekly). 
    
    Outputs:
    - A dictionary containing:
        - 'years': List of years corresponding to the time steps.
        - 'mass_delivered': Average mass delivered to space at each time step across simulations.
        - 'cumulative_cost': Average cumulative cost at each time step across simulations.
        - 'completion_timesteps': List of time steps taken to complete delivery in each simulation.
        - 'completion_years': List of years taken to complete delivery in each simulation.
        - 'final_costs': List of final cumulative costs at completion for each simulation.
        - 'mean_completion_timestep': Average time steps to completion across simulations.
        - 'std_completion_timestep': Standard deviation of time steps to completion across simulations.
        - 'mean_completion_year': Average years to completion across simulations.
        - 'std_completion_year': Standard deviation of years to completion across simulations.
        - 'mean_final_cost': Average final cumulative cost at completion across simulations.
        - 'std_final_cost': Standard deviation of final cumulative cost at completion across simulations.
    """
    timestep_capacity = mean_capacity * delta_time
    timestep_std_dev = std_dev * delta_time
    timestep_operational_cost = operational_cost_per_year_per_elevator * num_elevators * delta_time
    
    completion_timesteps = []
    final_costs = []
    timestep_deliveries = []
    
    for sim in range(num_simulations):
        timestep = 0
        delivered = 0
        cost = total_cost_per_elevator * num_elevators
        timestep_data = []
        
        while delivered < total_mass:
            timestep_delivery = max(0, np.random.normal(timestep_capacity, timestep_std_dev))
            delivered += timestep_delivery
            delivered = min(delivered, total_mass)
            cost += timestep_operational_cost
            timestep_data.append({'timestep': timestep, 'delivered': delivered, 'cost': cost})
            timestep += 1
        
        completion_timesteps.append(timestep)
        final_costs.append(cost)
        timestep_deliveries.append(timestep_data)
        
    individual_simulations = []
    for timestep_data in timestep_deliveries:
        sim_years = [start_year + data['timestep'] * delta_time for data in timestep_data]
        sim_delivered = [data['delivered'] for data in timestep_data]
        individual_simulations.append({
            'years': sim_years,
            'delivered': sim_delivered,
        })
    
    years_list = []
    mass_delivered_per_year = []
    cost_per_year = []
    
    max_timesteps = max(len(data) for data in timestep_deliveries)
    timesteps_per_year = 1.0 / delta_time
    
    for year_idx in range(0, max_timesteps, int(timesteps_per_year)):
        masses = []
        costs = []
        
        for timestep_data in timestep_deliveries:
            if year_idx < len(timestep_data):
                masses.append(timestep_data[year_idx]['delivered'])
                costs.append(timestep_data[year_idx]['cost'])
        
        if masses:
            years_list.append(start_year + year_idx * delta_time)
            mass_delivered_per_year.append(np.mean(masses))
            cost_per_year.append(np.mean(costs))
    
    if len(timestep_deliveries) > 0:
        last_idx = len(timestep_deliveries[0]) - 1
        if last_idx % int(timesteps_per_year) != 0:  
            masses = [data[-1]['delivered'] for data in timestep_deliveries]
            costs = [data[-1]['cost'] for data in timestep_deliveries]
            if masses:
                final_year = start_year + last_idx * delta_time
                if len(years_list) == 0 or abs(years_list[-1] - final_year) > 0.01: 
                    years_list.append(final_year)
                    mass_delivered_per_year.append(np.mean(masses))
                    cost_per_year.append(np.mean(costs))
    
    completion_years = [t * delta_time for t in completion_timesteps] 
    
    return {
        'years': years_list,
        'mass_delivered': mass_delivered_per_year,
        'cumulative_cost': cost_per_year,
        'individual_simulations': individual_simulations,
        'completion_timesteps': completion_timesteps,
        'completion_years': completion_years,
        'final_costs': final_costs,
        'mean_completion_timestep': np.mean(completion_timesteps),
        'std_completion_timestep': np.std(completion_timesteps),
        'mean_completion_year': np.mean(completion_years),
        'std_completion_year': np.std(completion_years),
        'mean_final_cost': np.mean(final_costs),
        'std_final_cost': np.std(final_costs),
        'delta_time': delta_time,
    }


    
def plot_results(results, title="Please input a title", show=False):
    plt.figure(figsize=(12, 6))
    plt.suptitle(title)
    
    plt.subplot(1, 2, 1)
    
    for sim in results['individual_simulations']:
        plt.plot(sim['years'], sim['delivered'], alpha=0.05, color='blue', linewidth=0.5)
    
    plt.plot(results['years'], results['mass_delivered'], marker='o', color='red', linewidth=2.5, label='Mean', zorder=10)
    
    plt.title('Mass Delivered to Space Over Time')
    plt.xlabel('Year')
    plt.ylabel('Mass Delivered (metric tons)')
    if 'individual_simulations' in results:
        plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(results['years'], results['cumulative_cost'], marker='o', color='orange')
    plt.title('Cumulative Cost Over Time')
    plt.xlabel('Year')
    plt.ylabel('Cumulative Cost (USD)')
    
    plt.tight_layout()
    if show:
        plt.show()

if __name__ == "__main__":
    stoch_results_monthly = elevator_only_stochastic_model(num_simulations=1000, delta_time=1/12)
    plot_results(stoch_results_monthly, title="Elevator-Only Stochastic Model - Monthly (1000 Simulations)", show=True)
    
    print("\n" + "=" * 70)
    print("STOCHASTIC MODEL - MONTHLY TIME STEPS (delta_time=1/12):")
    print("=" * 70)
    print(f"Mean Completion Time: {stoch_results_monthly['mean_completion_year']:.2f} ± {stoch_results_monthly['std_completion_year']:.2f} years")
    print(f"Mean Final Cost: ${stoch_results_monthly['mean_final_cost']:,.2f} ± ${stoch_results_monthly['std_final_cost']:,.2f}")
    print(f"Range: {min(stoch_results_monthly['completion_years']):.3f} - {max(stoch_results_monthly['completion_years']):.3f} years") 