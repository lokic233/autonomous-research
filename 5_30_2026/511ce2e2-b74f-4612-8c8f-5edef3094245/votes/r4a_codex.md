### A* FINAL
- Vote: GREEN
- Are CC4.8's two objections resolved? (obj1 mechanism: yes/no; obj2 AMD absence: yes/no)
  obj1 mechanism: yes; obj2 AMD absence: yes, within reachable VA, not as an exact AMD K_ceiling.
- Strongest remaining attack:
  AMD still lacks a measured failure point; 50,000,000 mappings at 191 GiB and zero driver failure is a bounded absence result, not proof of no ceiling.
- Is the NVIDIA-specific portability-cliff claim GREEN-worthy EVEN IF AMD's exact ceiling stays unmeasured? (yes/no + why — this is the crux)
  yes — NVIDIA reproducibly fails at ~520K mappings while AMD reached 50M mappings with zero driver failure, a 96× gap in the tested regime.
- Venue you'd bet on:
  ATC
- One-line: what (if anything) is still needed for unconditional GREEN.
  A controlled AMD run that ends at a predeclared non-driver resource limit, or reaches a hipMemSetAccess failure, with host telemetry preserved.
===EXIT_0===
