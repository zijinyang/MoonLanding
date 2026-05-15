req_ex = [
    {
        2100 : 0.5,
        2500 : 1 
    }
]

def verify_requirements(req_dict):
    current_req = 0
    current_year = 2050
    for year, req in req_dict.items():
        if req < 0 or req > 1:
            raise ValueError(f"Requirement for year {year} must be between 0 and 1. Found: {req}")
        if req < current_req:
            raise ValueError(f"Requirement for year {year} must be greater than or equal to the previous requirement. Found: {req} < {current_req}")
        current_req = req
        if year < 2050:
            raise ValueError(f"Year {year} must be greater than or equal to the start year {current_year}. Found: {year}")
        if year < current_year:
            raise ValueError(f"Year {year} must be greater than or equal to the previous year. Found: {year} < {current_year}")
        current_year = year
    print("All requirements are valid.")

if __name__ == "__main__":
    for req in req_ex:
        verify_requirements(req)