"""Astronomy helpers: Julian days, Delta-T, apparent solar longitude,
solar-term (节气) instants and the equation of time.

Solar longitude uses Meeus' "Astronomical Algorithms" ch.25 with nutation
and aberration (accuracy ~0.01 deg, i.e. solar terms within a few minutes).
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

J2000 = 2451545.0


def julian_day(dt: datetime) -> float:
    """Julian day of a UTC datetime (naive datetimes are treated as UTC)."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    y, m = dt.year, dt.month
    d = dt.day + (dt.hour + (dt.minute + (dt.second + dt.microsecond / 1e6) / 60) / 60) / 24
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def from_julian_day(jd: float) -> datetime:
    """UTC naive datetime from a Julian day."""
    return datetime(2000, 1, 1, 12) + timedelta(days=jd - J2000)


def delta_t(year: float) -> float:
    """TT - UT in seconds (Espenak & Meeus polynomials, 1900-2150)."""
    y = year
    if y < 1900:
        u = (y - 1820) / 100
        return -20 + 32 * u * u
    if y < 1920:
        t = y - 1900
        return -2.79 + 1.494119 * t - 0.0598939 * t**2 + 0.0061966 * t**3 - 0.000197 * t**4
    if y < 1941:
        t = y - 1920
        return 21.20 + 0.84493 * t - 0.076100 * t**2 + 0.0020936 * t**3
    if y < 1961:
        t = y - 1950
        return 29.07 + 0.407 * t - t**2 / 233 + t**3 / 2547
    if y < 1986:
        t = y - 1975
        return 45.45 + 1.067 * t - t**2 / 260 - t**3 / 718
    if y < 2005:
        t = y - 2000
        return 63.86 + 0.3345 * t - 0.060374 * t**2 + 0.0017275 * t**3 + 0.000651814 * t**4 + 0.00002373599 * t**5
    if y < 2050:
        t = y - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t**2
    if y < 2150:
        return -20 + 32 * ((y - 1820) / 100) ** 2 - 0.5628 * (2150 - y)
    u = (y - 1820) / 100
    return -20 + 32 * u * u


def _jde(jd_ut: float) -> float:
    year = 2000 + (jd_ut - J2000) / 365.25
    return jd_ut + delta_t(year) / 86400


def sun_longitude(jd_ut: float) -> float:
    """Apparent geocentric ecliptic longitude of the Sun, degrees [0,360)."""
    t = (_jde(jd_ut) - J2000) / 36525
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = math.radians(357.52911 + 35999.05029 * t - 0.0001537 * t * t)
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m)
         + (0.019993 - 0.000101 * t) * math.sin(2 * m)
         + 0.000289 * math.sin(3 * m))
    omega = math.radians(125.04 - 1934.136 * t)
    lam = l0 + c - 0.00569 - 0.00478 * math.sin(omega)
    return lam % 360


def solar_term_jd(year: int, longitude: float) -> float:
    """JD (UT) at which the Sun reaches `longitude` within Gregorian `year`."""
    # Sun is at 280 deg ~ Jan 1; ~0.9856 deg/day.
    guess = julian_day(datetime(year, 1, 1)) + ((longitude - 280.5) % 360) / 0.98565
    jd = guess
    for _ in range(20):
        diff = (longitude - sun_longitude(jd) + 180) % 360 - 180
        jd += diff / 0.98565
        if abs(diff) < 1e-7:
            break
    return jd


def equation_of_time_minutes(jd_ut: float) -> float:
    """Apparent minus mean solar time, minutes (NOAA/Meeus approximation)."""
    t = (_jde(jd_ut) - J2000) / 36525
    eps = math.radians(23.439291 - 0.0130042 * t)
    l0 = math.radians((280.46646 + 36000.76983 * t) % 360)
    e = 0.016708634 - 0.000042037 * t
    m = math.radians(357.52911 + 35999.05029 * t)
    y = math.tan(eps / 2) ** 2
    eot = (y * math.sin(2 * l0) - 2 * e * math.sin(m) + 4 * e * y * math.sin(m) * math.cos(2 * l0)
           - 0.5 * y * y * math.sin(4 * l0) - 1.25 * e * e * math.sin(2 * m))
    return math.degrees(eot) * 4
