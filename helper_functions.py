


def calculate_env_score(company,destination):
    """
    This functions helps in calculating the environment score of the bus company to a particular destination.
    """

    # here we calculate total co2 release during a ride to particular destination in kg
    total_emission_kg = (company.co2_g_per_km * destination.distance_km)

    # Base emission penalty: lower emissions per km result in a higher base score.
    # Assuming standard bus emissions range roughly from 20g/km (ultra-green/electric) to 50g/km (older diesel).
    # We map this inversely to a 0-100 scale.
    max_expected_co2_per_km = 55.0
    min_expected_co2_per_km = 20.0


    # 
    clamped_co2 = max(min_expected_co2_per_km, min(company.co2_g_per_km, max_expected_co2_per_km))

    # lower co2 = higher score(0 to 100)
    base_score = ((max_expected_co2_per_km - clamped_co2) / (max_expected_co2_per_km - min_expected_co2_per_km)) * 100.0

    # if company uses new/modern fleet, will have bonus
    modern_fleet_bonus = 10.0 if company.new_fleet else 0.0

    #final score
    final_score = base_score + modern_fleet_bonus
    if(company.name == "VerdeBus"):
     print(final_score)
    return int(max(0.0,min(100.0,final_score)))

