### A* FINAL
- Vote: GREEN
- Are CC4.8's two objections resolved? (obj1 mechanism: yes; obj2 AMD absence: yes)
- Strongest remaining attack: The absolute claim "absent on AMD in all reachable VA" is empirically bounded by the host failure at 191 GiB (50,000,000 mappings); an unmeasured theoretical driver ceiling might still exist beyond that host-kill threshold.
- Is the NVIDIA-specific portability-cliff claim GREEN-worthy EVEN IF AMD's exact ceiling stays unmeasured? yes, because a 96x proven divergence (520K NVIDIA vs >50M AMD) definitively establishes the practical portability cliff for any application operating in that regime.
- Venue you'd bet on: USENIX ATC
- One-line: Explicitly bound the AMD claim to the tested 191 GiB (50M mappings) host-failure threshold rather than claiming absolute infinity.
===EXIT_0===
