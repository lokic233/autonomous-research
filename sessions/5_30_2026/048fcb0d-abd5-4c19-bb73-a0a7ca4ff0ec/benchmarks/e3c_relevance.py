"""
E3c — NT1 relevance: does the K ceiling actually BITE at deployment-realistic agent fanout?
(pure model from the measured K; no GPU stress). For real agent workloads (long shared context,
many parallel branches), compute the max concurrent branches and whether the wall is hit BEFORE
HBM is exhausted — i.e. is mapping-metadata the BINDING constraint, not memory?
"""
import json
K = 519936  # measured median K on H100 (Metric 4b), driver 580.82
PAGE_MiB = 2
HBM_GiB = 97
KV_per_token_KiB = 128  # 7B-class GQA fp16 (matches WRITEUP)
toks_per_page = (PAGE_MiB*1024)//KV_per_token_KiB  # tokens per 2MiB page

scenarios = [
 ("short chat prefix", 2_000),
 ("RAG / 6k agent ctx", 8_000),
 ("long coding-agent ctx", 32_000),
 ("128k long-context", 128_000),
]
rows=[]
for name, ctx_tokens in scenarios:
    prefix_pages = -(-ctx_tokens // toks_per_page)  # ceil
    max_branches_mapping = K // prefix_pages              # the NT1 ceiling
    # memory ceiling if you DIDN'T share (full clone): each branch needs ctx KV bytes
    kv_per_branch_GiB = ctx_tokens*KV_per_token_KiB/1024/1024
    max_branches_mem_noshare = int(HBM_GiB / max(kv_per_branch_GiB,1e-9))
    # with CoW sharing, HBM for prefix is paid ONCE; so memory allows ~unbounded branches,
    # and the BINDING limit becomes the mapping ceiling:
    binding = "mapping-metadata (NT1 wall)" if max_branches_mapping < 100000 else "none-practical"
    rows.append({"scenario":name,"ctx_tokens":ctx_tokens,"prefix_pages":prefix_pages,
                 "max_branches_NT1_mapping_ceiling":max_branches_mapping,
                 "max_branches_if_fullclone_HBM":max_branches_mem_noshare,
                 "binding_constraint_under_CoW_sharing":binding})
R={"experiment":"E3c_relevance_deployment_envelope","K":K,"toks_per_page":toks_per_page,"rows":rows}
R["verdict"]="NT1 ceiling BITES whenever shared-prefix CoW is used at scale: with sharing, HBM is no longer the limit, so the ~520K mapping budget becomes the binding cap on concurrent branches."
print(json.dumps(R,indent=2)); json.dump(R,open("e3c_result.json","w"),indent=2)
