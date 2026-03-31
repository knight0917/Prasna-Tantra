import math
from skyfield.api import load
ts = load.timescale()
t = ts.utc(2026, 2, 22, 4, 30, 0) # 10 AM IST

gast = t.gast
lat = 28.6139
lon = 77.2090

lst = gast + (lon / 15.0)
lst_rad = math.radians(lst * 15.0)

T = (t.tt - 2451545.0) / 36525.0
eps_deg = 23.43929111 - (46.8150 * T - 0.00059 * T**2 + 0.001813 * T**3) / 3600.0
eps_rad = math.radians(eps_deg)
lat_rad = math.radians(lat)

y = math.cos(lst_rad)
x = -(math.sin(lst_rad) * math.cos(eps_rad) + math.tan(lat_rad) * math.sin(eps_rad))
asc_rad = math.atan2(y, x)
asc_deg = (math.degrees(asc_rad) + 360) % 360

print(f"Tropical Ascendant: {asc_deg}")
# Lahiri approximation around 2026 is ~24.13
lahiri_asc = (asc_deg - 24.13) % 360
print(f"Lahiri Ascendant: {lahiri_asc}")
