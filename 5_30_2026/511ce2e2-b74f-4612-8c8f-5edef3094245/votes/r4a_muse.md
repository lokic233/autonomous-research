67 skills discovered
### A* FINAL
- Vote: GREEN
- Are CC4.8's two objections resolved? (obj1 mechanism: yes; obj2 AMD absence: yes)
- Strongest remaining attack: The AMD “absence” is only demonstrated up to 50,000,000 mappings (191 GiB VA) where the host thrashed and the node went offline; the thesis claims “ABSENT in all reachable VA” but reachable VA is bounded by host memory for page tables, not GPU VA limits, so a reviewer could argue the cliff is quantitative (96×) not qualitative (present vs absent), and the pattern-sensitive NVIDIA ceiling (5,637 vs 523,404) weakens the simple K≈520K model.
- Is the NVIDIA-specific portability-cliff claim GREEN-worthy EVEN IF AMD's exact ceiling stays unmeasured? (yes/no + why — this is the crux) yes because the NVIDIA wall is independently reproduced at 523,404 (±0.6%) across four prefix sizes and forensically located at cuMemSetAccess with 1 GiB HBM live, while AMD sustains 50,000,000 mappings (96×) with zero driver failure; a VMM-based design scaling to even 5M branches on AMD will reliably hit the NVIDIA wall at ~0.5M, establishing a practical vendor-specific cliff without needing AMD’s asymptotic ceiling.
- Venue you'd bet on: OSDI
- One-line: what (if anything) is still needed for unconditional GREEN: A measured AMD hipMemSetAccess failure point (or a vendor-confirmed statement that ROCm imposes no fixed descriptor limit) to convert “no ceiling found up to 50M” into a definitive “absent”.
### A* FINAL
- Vote: GREEN
- Are CC4.8's two objections resolved? (obj1 mechanism: yes; obj2 AMD absence: yes)
- Strongest remaining attack: The AMD “absence” is only demonstrated up to 50,000,000 mappings (191 GiB VA) where the host thrashed and the node went offline; the thesis claims “ABSENT in all reachable VA” but reachable VA is bounded by host memory for page tables, not GPU VA limits, so a reviewer could argue the cliff is quantitative (96×) not qualitative (present vs absent), and the pattern-sensitive NVIDIA ceiling (5,637 vs 523,404) weakens the simple K≈520K model.
- Is the NVIDIA-specific portability-cliff claim GREEN-worthy EVEN IF AMD's exact ceiling stays unmeasured? (yes/no + why — this is the crux) yes because the NVIDIA wall is independently reproduced at 523,404 (±0.6%) across four prefix sizes and forensically located at cuMemSetAccess with 1 GiB HBM live, while AMD sustains 50,000,000 mappings (96×) with zero driver failure; a VMM-based design scaling to even 5M branches on AMD will reliably hit the NVIDIA wall at ~0.5M, establishing a practical vendor-specific cliff without needing AMD’s asymptotic ceiling.
- Venue you'd bet on: OSDI
- One-line: what (if anything) is still needed for unconditional GREEN: A measured AMD hipMemSetAccess failure point (or a vendor-confirmed statement that ROCm imposes no fixed descriptor limit) to convert “no ceiling found up to 50M” into a definitive “absent”.
===EXIT_0===
