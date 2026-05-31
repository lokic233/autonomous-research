### T-TAX FINAL
- Vote: GREEN
- Is it MORE than A*+C* restated? yes - E-T adds measured end-to-end high-fanout decode: SW never crashes through B=1124 and scales 280->800 tok/s, while HW is <=136 tok/s, crashes for every B>=128, and has 0 win regimes.
- Strongest remaining attack: single layer / single GPU / single driver, with HW crash point variable at 9-393 branches under fork+CoW+attention, so the exact collapse branch is confounded by allocator/context state.
- Does the negative result clear a real venue, and which? yes: MLSys or ATC; OSDI/EuroSys would need broader hardware/driver/model coverage.
- Honesty check: GREEN on measured evidence, not hope: A* gives K≈523,404, C* gives 240x fork slowdown and 0/12 VMM wins, and E-T shows 2.74x-10.62x SW wins with HW collapse.
===EXIT_0===
