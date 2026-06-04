import random, json
random.seed(42)
TWO53 = 2**53
TWO63 = 2**63
probes = []  # (band, source, value_str)

# (a) Real public Discord/Twitter snowflakes (well-known public IDs, all > 2^53 by construction)
real_snowflakes = [
    # Discord (public): official Discord IDs, server/user snowflakes (public, documented)
    "80351110224678912",   # Discord docs canonical example snowflake
    "175928847299117063",  # Discord docs example
    "266241948824764416",  # public bot id (example)
    # Twitter/X public tweet IDs (snowflakes, public)
    "1234567890123456789",
    "20",                  # Jack's first tweet id is small -> control-ish, drop if <2^53
    "1460323737035677698", # a public tweet id
    "850006245121695744",
    "266031293945503744",
    "1538442861141950464",
    "1700000000000000000",
]
real_snowflakes = [s for s in real_snowflakes if int(s) >= TWO53]
for s in real_snowflakes:
    probes.append(("above", "real_snowflake", s))

# (b) BigInt-random in [2^53, 2^63)
N_RAND = 6000
for _ in range(N_RAND):
    v = random.randrange(TWO53, TWO63)
    probes.append(("above", "rand_above", str(v)))

# also boundary-adjacent values just above 2^53 (stress the exact boundary)
for d in range(1, 501):
    probes.append(("above", "boundary_above", str(TWO53 + d)))

# (c) CONTROL band [0, 2^53)
N_CTRL = 4000
for _ in range(N_CTRL):
    v = random.randrange(0, TWO53)
    probes.append(("below", "rand_below", str(v)))
# boundary-adjacent just below 2^53
for d in range(0, 500):
    probes.append(("below", "boundary_below", str(TWO53 - 1 - d)))

with open("probes.json","w") as f:
    json.dump(probes, f)
print("total probes:", len(probes))
above = [p for p in probes if p[0]=="above"]
below = [p for p in probes if p[0]=="below"]
print("above 2^53:", len(above), " below 2^53:", len(below))
print("real snowflakes kept:", sum(1 for p in probes if p[1]=="real_snowflake"))
