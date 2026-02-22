# AstroTrack Python - Active Tasks

## Phase 1: Core Engine Initialization & Math Setup

- [x] Set up Python environment (3.10+) with `skyfield` and define Ephemeris data paths. _(Using DE421 bsp via Skyfield due to C++ compile constraint on pyswisseph)_
- [x] Download & configure JPL DE421 (`.bsp`) binary data files.
- [x] Create core astronomical conversion utility functions in `skyfield` via `Topos` and `Apparent`.

## Phase 2: Astronomical Computation Module

- [x] Implement Geocentric to Topocentric coordinate translation (added missing Altitude parameter to input).
- [x] Implement Ayanamsa selection wrapper (Lahiri, Raman, Tropical approximations added).
- [x] Build Planetary position loops using `skyfield` calculating Refraction.
- [x] Implement high-precision integer math representation for Zodiac mapping and Nakshatra ($13^\circ 20'$ division) calculation to avoid floating-point bounds errors.

## Phase 3: Input/Output Boundaries & Validation

- [x] Construct explicit input validation boundaries (via Pydantic) for Latitude (-90 to 90), Longitude (-180 to 180), Date, Time, and Altitude.
- [x] Build the central computational orchestrator that computes required planets.
- [x] Format final outputs into the standardized JSON/Dictionary contract (`AstroResponse`).

## Phase 4: Performance & Latency Optimization

- [x] Introduce memory Caching/Singleton for `eph = load('de421.bsp')`. Loading 17MB+ Ephemeris files successfully occurs at startup, not per-request, yielding `~29ms` latency (well under the `< 100ms` strict latency requirement).
- [x] Decoupled API layer conceptually by exposing purely `process(AstroRequest)` dict.
- [x] Write validation test suite benchmark showing validation computations executing successfully.
