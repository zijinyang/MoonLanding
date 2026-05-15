import numpy as np
import matplotlib.pyplot as plt

#===================== Estimates ====================
total_cost_per_rocket = 5e9
operational_cost_per_flight_per_rocket = 50e6
total_pollution_per_flight_per_rocket = [1000, 2000, 3000, 4000, 5000] #depending on launch site
total_number_of_flights_per_year_per_launch_site = 1000
total_mass_per_flight_per_rocket = 100

#===================== Constants ====================
total_mass = 100e6
start_year = 2050


#max time, no consideration for cost or pollution
def rocket_only_deterministic_model():
    years = []
    mass_delivered = []
    cumulative_cost = []
    
    year = start_year
    delivered = 0
    cost = 0
    launch_sites = [ {'pollution_per_flight': pollution, 'flights_per_year': total_number_of_flights_per_year_per_launch_site} for pollution in total_pollution_per_flight_per_rocket]
    
    while delivered < total_mass:
        years.append(year)
        for site in launch_sites:
            if delivered < total_mass:
                flights = min(site['flights_per_year'], (total_mass - delivered) / total_mass_per_flight_per_rocket)
                delivered += flights * total_mass_per_flight_per_rocket
                cost += flights * operational_cost_per_flight_per_rocket
        cumulative_cost.append(cost + total_cost_per_rocket * len(launch_sites))
        year += 1
        mass_delivered.append(delivered)
    return years, mass_delivered, cumulative_cost

if __name__ == "__main__":
    years, mass_delivered, cumulative_cost = rocket_only_deterministic_model()
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(years, mass_delivered, label='Mass Delivered (kg)')
    plt.xlabel('Year')
    plt.ylabel('Mass Delivered (kg)')
    plt.title('Rocket-Only Deterministic Model: Mass Delivered Over Time')
    plt.grid()
    plt.legend()
    
    plt.subplot(2, 1, 2)
    plt.plot(years, cumulative_cost, label='Cumulative Cost ($)', color='orange')
    plt.xlabel('Year')
    plt.ylabel('Cumulative Cost ($)')
    plt.title('Rocket-Only Deterministic Model: Cumulative Cost Over Time')
    plt.grid()
    plt.legend()
    
    plt.tight_layout()
    plt.show()