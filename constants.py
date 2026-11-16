from models import BusCompany

BUS_COMPANIES = {
    "SolRuta": BusCompany(
        name="SolRuta", 
        bus_code="SOL",
        price_per_km=0.050, 
        speed_multiplier=1.10, 
        co2_g_per_km=32,
        departure_window=("06:00", "14:00"),
        direct_route=False, 
        coastal_focus=False, 
        new_fleet=False,
        budget_company=True
    ),
    "CaminoExpress": BusCompany(
        name="CaminoExpress", 
        bus_code="CAE",
        price_per_km=0.075, 
        speed_multiplier=0.90, 
        co2_g_per_km=26,
        departure_window=("11:00", "20:00"),
        direct_route=True, 
        coastal_focus=False, 
        new_fleet=True,
        budget_company=False
    ),
    "CostaLink": BusCompany(
        name="CostaLink", 
        bus_code="COL",
        price_per_km=0.062, 
        speed_multiplier=1.05, 
        co2_g_per_km=28,
        departure_window=("16:00", "20:00"),
        direct_route=False, 
        coastal_focus=True, 
        new_fleet=False,
        budget_company=False
    ),
    "VerdeBus": BusCompany(
        name="VerdeBus", bus_code="VDB",
        price_per_km=0.071, 
        speed_multiplier=1.00,
        co2_g_per_km=18,
        departure_window=("16:30", "23:00"),
        direct_route=False, 
        coastal_focus=False, 
        new_fleet=True,
        budget_company=False
    ),
    "NocheVia": BusCompany(
        name="NocheVia", 
        bus_code="NOV",
        price_per_km=0.059, 
        speed_multiplier=1.05, 
        co2_g_per_km=29,
        departure_window=("15:30", "23:59"),
        direct_route=False, 
        coastal_focus=False, 
        new_fleet=False,
        budget_company=False
    ),
}
