#!/usr/bin/env python3
"""EXP-0060 L1 dense-encoder harness (CLAIM-0052 #4 resolution).
Real dense encoders (BGE-base, e5-base) over realistic-NL MCP-style registry with harness-owned
coverage knob c. GT harness-held. Reachable-recall + coverage-gap discriminator + TOST.
Honest pipeline. GPU mem capped; os._exit at end.
"""
import os, sys, json, time, math, random, gc
# httpx/no_proxy fix not needed (offline); but sanitize anyway
for k in ("no_proxy","NO_PROXY"):
    if k in os.environ:
        os.environ[k]=",".join(p for p in os.environ[k].split(",") if "[" not in p and "::" not in p)
os.environ["HF_HUB_OFFLINE"]="1"; os.environ["TRANSFORMERS_OFFLINE"]="1"
os.environ.setdefault("CUDA_VISIBLE_DEVICES","3")
import numpy as np
import torch
torch.set_grad_enabled(False)

# ---------------- DOMAIN BANK (grounded in 398 real MCP editorial descriptions) ----------------
# Each domain: a boilerplate sentence (server theme) + a pool of DISTINCTIVE capability phrases
# (tool-level), each with a paraphrase used as the QUERY. capability != query paraphrase verbatim.
DOMAINS = {
 "web_scraping": {
   "boiler":"An MCP server for web scraping, crawling, and turning online content into clean LLM-ready text.",
   "tools":[
     ("convert a web page URL into clean LLM-ready markdown","turn this link into tidy markdown I can feed an LLM"),
     ("discover and map all reachable URLs on a website","crawl a site and list every page it links to"),
     ("extract the main article text and strip navigation and ads","pull just the readable body of a news article"),
     ("take a full-page screenshot of a rendered web page","capture an image of how a webpage looks"),
     ("search the web and return ranked result snippets","run a Google-style web query and get top hits"),
     ("submit and fill an HTML form on a page","automatically complete a web form's fields"),
     ("download and parse a sitemap.xml file","read a site's sitemap to enumerate its content"),
     ("monitor a page and detect when its content changes","watch a webpage and alert me if it updates"),
     ("render JavaScript-heavy pages in a headless browser","load a dynamic SPA so its JS content appears"),
     ("respect and read a site's robots.txt rules","check what a crawler is allowed to fetch on a domain"),
   ]},
 "sql_database": {
   "boiler":"An MCP server providing structured access to SQL databases and tabular data stores.",
   "tools":[
     ("run a parameterized read-only SQL SELECT query","execute a safe SELECT against the database"),
     ("list all tables and their column schemas","show me the database's tables and columns"),
     ("explain the query plan and estimated cost","get the EXPLAIN output for a slow query"),
     ("create a new table from a CSV upload","import a CSV file as a fresh database table"),
     ("compute aggregate statistics over a column","get the mean, min, and max of a numeric field"),
     ("export query results to a downloadable file","save the rows from a query as a CSV"),
     ("manage and apply schema migrations","run a database migration to alter the schema"),
     ("create an index to speed up a slow lookup","add an index on a column for faster reads"),
     ("perform a full-text search over text columns","do a keyword search inside text fields"),
     ("back up a table to object storage","snapshot a table and store it in a bucket"),
   ]},
 "git_code": {
   "boiler":"An MCP server for source code repositories, version control, and code search.",
   "tools":[
     ("search C and C++ symbols across a build index","find a function definition in a C++ codebase"),
     ("show the diff between two git commits","display what changed between two revisions"),
     ("blame a file to find who last edited each line","see git blame authorship for a source file"),
     ("open a pull request from a feature branch","create a PR for my branch against main"),
     ("run a semantic grep over the whole repository","search the codebase by meaning, not exact text"),
     ("list recent commits touching a given file","show the commit history of one file"),
     ("resolve a merge conflict between branches","help me merge two diverging branches"),
     ("generate a changelog from commit messages","summarize recent commits into release notes"),
     ("find all references to a symbol project-wide","locate every call site of this function"),
     ("check out a specific tag or release","switch the working tree to a tagged version"),
   ]},
 "calendar": {
   "boiler":"An MCP server that manages calendars, events, and scheduling.",
   "tools":[
     ("create a calendar event with attendees and a location","schedule a meeting and invite people"),
     ("find a free time slot across several calendars","figure out when everyone is available"),
     ("set a reminder ahead of an event","add an alert before an appointment"),
     ("list all events on a given day","show me what's on my schedule today"),
     ("reschedule an existing event to a new time","move a meeting to a different slot"),
     ("cancel an event and notify attendees","delete a meeting and tell the guests"),
     ("convert an event's time across time zones","show this meeting in another time zone"),
     ("create a recurring weekly event","set up a meeting that repeats every week"),
     ("accept or decline a meeting invitation","RSVP to an event invite"),
     ("attach a video conference link to an event","add a Zoom link to a calendar invite"),
   ]},
 "image_gen": {
   "boiler":"An MCP server for image generation, editing, and visual content creation.",
   "tools":[
     ("generate an image from a text prompt","make a picture from a written description"),
     ("remove the background from a photo","cut out the subject and erase the backdrop"),
     ("upscale a low-resolution image","increase the resolution of a small image"),
     ("inpaint and fill a masked region of an image","fill in an erased area of a photo"),
     ("apply an artistic style transfer to a photo","restyle a picture to look like a painting"),
     ("create variations of an existing image","produce alternate versions of a given image"),
     ("caption an image with a text description","write alt-text describing what's in a photo"),
     ("detect and crop faces in a photo","find and tightly crop the faces in an image"),
     ("convert an image to a different file format","change a PNG into a JPEG"),
     ("generate a thumbnail at a target size","make a small preview of a large image"),
   ]},
 "kubernetes": {
   "boiler":"An MCP server for Kubernetes cluster operations and container orchestration.",
   "tools":[
     ("scale a deployment to a target replica count","set the number of pods for a deployment"),
     ("stream the logs of a running pod","tail the logs from a container"),
     ("apply a YAML manifest to the cluster","deploy resources from a kubernetes manifest"),
     ("describe the status of a failing pod","explain why a pod is crash-looping"),
     ("roll back a deployment to a previous revision","undo the last deploy and restore the old version"),
     ("exec a command inside a container","run a shell command in a running pod"),
     ("list nodes and their resource usage","show cluster node CPU and memory pressure"),
     ("create a port-forward to a service","tunnel a local port to a cluster service"),
     ("drain a node for maintenance","cordon and evict pods off a node"),
     ("set resource requests and limits on a container","configure CPU and memory limits for a pod"),
   ]},
 "email": {
   "boiler":"An MCP server for email: reading, composing, and managing messages.",
   "tools":[
     ("send an email with attachments","compose and send a message with files attached"),
     ("search the inbox by sender and date","find emails from a person within a date range"),
     ("summarize a long email thread","give me the gist of this email conversation"),
     ("draft a reply to an incoming message","write a response to this email for me"),
     ("label and file a message into a folder","sort this email into a folder with a tag"),
     ("mark messages as read or unread","flag these emails as read"),
     ("extract action items from an email","list the to-dos mentioned in this message"),
     ("set up an out-of-office auto-reply","turn on a vacation responder"),
     ("unsubscribe from a mailing list","stop getting newsletters from this sender"),
     ("forward a message to another recipient","send this email along to someone else"),
   ]},
 "finance": {
   "boiler":"An MCP server providing financial market data and portfolio analytics.",
   "tools":[
     ("fetch the latest stock price for a ticker","get the current share price of a company"),
     ("retrieve historical daily OHLC price bars","download a stock's past daily prices"),
     ("compute portfolio risk and volatility","measure how risky my holdings are"),
     ("get a company's latest earnings report","pull the most recent quarterly earnings"),
     ("convert an amount between two currencies","exchange dollars into euros at today's rate"),
     ("screen stocks by financial criteria","filter equities by P/E and market cap"),
     ("calculate compound interest over time","project savings growth with compounding"),
     ("retrieve a crypto asset's market depth","get the order book for a cryptocurrency"),
     ("compute the moving average of a price series","smooth a price chart with a rolling mean"),
     ("get dividend history for a holding","show past dividend payments for a stock"),
   ]},
}
DOMAIN_KEYS=list(DOMAINS.keys())

def build_registry(S, T, c, rng):
    """Return servers list. Each server: domain, boiler, tools[(cap,query)], editorial_desc(str),
    pooled_member(str), tool_schemas[str], covered[bool per tool]. GT = (server_idx, tool_idx)."""
    servers=[]
    for si in range(S):
        dom=DOMAIN_KEYS[si % len(DOMAIN_KEYS)]
        d=DOMAINS[dom]; boiler=d["boiler"]; pool=d["tools"]
        idxs=rng.sample(range(len(pool)), T)  # T<=10
        caps=[pool[i] for i in idxs]
        covered=[rng.random()<c for _ in range(T)]
        # editorial desc: boilerplate + included distinctive capabilities (covered ones)
        inc=[caps[t][0] for t in range(T) if covered[t]]
        ed = boiler + (" It can: " + "; ".join(inc) + "." if inc else "")
        # tool schema = distinctive capability + boilerplate (stage-2 observable)
        schemas=[caps[t][0] + ". " + boiler for t in range(T)]
        # pooled-member-schema rep = concat of all member tool schemas (ecological baseline)
        pooled = boiler + " Tools: " + "; ".join(caps[t][0] for t in range(T)) + "."
        queries=[caps[t][1] for t in range(T)]
        servers.append(dict(dom=dom, boiler=boiler, caps=caps, covered=covered,
                            ed=ed, schemas=schemas, pooled=pooled, queries=queries))
    return servers
print("harness module (build_registry) loaded; domains:", len(DOMAINS))

# ---------------- ENCODERS ----------------
from sentence_transformers import SentenceTransformer
_ENC_CACHE={}
def get_encoder(name):
    if name not in _ENC_CACHE:
        dev="cuda" if torch.cuda.is_available() else "cpu"
        m=SentenceTransformer(name, device=dev)
        _ENC_CACHE[name]=m
    return _ENC_CACHE[name]

def encode(name, texts, kind):
    """kind in {'query','passage'} for e5 prefixing / bge instruction."""
    m=get_encoder(name)
    if "e5" in name:
        pref = "query: " if kind=="query" else "passage: "
        texts=[pref+t for t in texts]
    elif "bge" in name:
        if kind=="query":
            texts=["Represent this sentence for searching relevant passages: "+t for t in texts]
    emb=m.encode(texts, batch_size=256, convert_to_numpy=True, normalize_embeddings=True,
                 show_progress_bar=False)
    return emb.astype(np.float32)

# ---------------- LEXICAL (L0-style TF cosine) ----------------
import re
_tok=re.compile(r"[a-z0-9]+")
def tf_vec(text, vocab):
    v=np.zeros(len(vocab),dtype=np.float32)
    for w in _tok.findall(text.lower()):
        j=vocab.get(w)
        if j is not None: v[j]+=1.0
    n=np.linalg.norm(v)
    return v/n if n>0 else v
def lexical_scores(queries, docs):
    vocab={}
    for txt in list(queries)+list(docs):
        for w in _tok.findall(txt.lower()):
            if w not in vocab: vocab[w]=len(vocab)
    Q=np.stack([tf_vec(q,vocab) for q in queries])
    Dd=np.stack([tf_vec(d,vocab) for d in docs])
    return Q@Dd.T  # (nq, ndoc) cosine (already normalized)

# ---------------- RETRIEVAL EVAL ----------------
def eval_cell(servers, S, T, encoder_name, top_m_list):
    """Returns dict of reachable-recall metrics for FLAT, dense two-stage(editorial),
    pooled-member two-stage, lexical two-stage. GT held here, never in scores."""
    # flatten
    schemas=[]; sch_owner=[]  # (server_idx, tool_idx)
    queries=[]; q_gt=[]; q_covered=[]
    eds=[]; pooled=[]
    for si,sv in enumerate(servers):
        eds.append(sv["ed"]); pooled.append(sv["pooled"])
        for ti in range(T):
            schemas.append(sv["schemas"][ti]); sch_owner.append((si,ti))
            queries.append(sv["queries"][ti]); q_gt.append((si,ti)); q_covered.append(sv["covered"][ti])
    q_covered=np.array(q_covered)
    # encode
    if encoder_name=="lexical":
        QS = lexical_scores(queries, schemas)      # query x toolschema
        QE = lexical_scores(queries, eds)          # query x editorial
        QP = lexical_scores(queries, pooled)       # query x pooled-member
    else:
        Qe=encode(encoder_name, queries, "query")
        Se=encode(encoder_name, schemas, "passage")
        Ee=encode(encoder_name, eds, "passage")
        Pe=encode(encoder_name, pooled, "passage")
        QS=Qe@Se.T; QE=Qe@Ee.T; QP=Qe@Pe.T
    nq=len(queries)
    # server->tool index map
    server_tools={si:[i for i,o in enumerate(sch_owner) if o[0]==si] for si in range(S)}
    gt_flat=np.array([si*T+ti for (si,ti) in q_gt])  # since tools laid out server-major
    # FLAT: top-k=T over all N tools (k=T per pre-reg primary)
    k=T
    flat_hit=np.zeros(nq,dtype=bool)
    topN=np.argsort(-QS,axis=1)[:, :k]
    for i in range(nq):
        flat_hit[i]= gt_flat[i] in topN[i]
    out={"flat_rr": float(flat_hit.mean())}
    # TWO-STAGE generic, given stage1 score matrix QSTAGE1 (query x server)
    def two_stage(QSTAGE1, m):
        topm=np.argsort(-QSTAGE1,axis=1)[:, :m]  # (nq,m) server ids
        hit=np.zeros(nq,dtype=bool)
        for i in range(nq):
            routed=set(topm[i].tolist())
            gsi=q_gt[i][0]
            if gsi in routed:
                # stage-2 within routed servers: keep top-k=T per server -> GT always in if routed
                hit[i]=True   # k=T => whole server kept; routing is the only ceiling
            else:
                hit[i]=False
        return hit
    for m in top_m_list:
        de=two_stage(QE,m)   # dense/lex editorial two-stage
        pm=two_stage(QP,m)   # pooled-member two-stage
        out[f"ed_rr_m{m}"]=float(de.mean())
        out[f"pool_rr_m{m}"]=float(pm.mean())
        # coverage-gap-only reachable recall (the #4 discriminator)
        gapmask=~q_covered
        covmask=q_covered
        if gapmask.sum()>0:
            out[f"ed_rr_gap_m{m}"]=float(de[gapmask].mean())
            out[f"pool_rr_gap_m{m}"]=float(pm[gapmask].mean())
            out[f"n_gap"]=int(gapmask.sum())
        else:
            out[f"ed_rr_gap_m{m}"]=float('nan'); out[f"pool_rr_gap_m{m}"]=float('nan'); out[f"n_gap"]=0
        if covmask.sum()>0:
            out[f"ed_rr_cov_m{m}"]=float(de[covmask].mean())
        else:
            out[f"ed_rr_cov_m{m}"]=float('nan')
        # mechanism: of editorial two-stage misses, fraction that are coverage-gap items
        miss=~de
        out[f"miss_isgap_frac_m{m}"]= float((miss & gapmask).sum()/max(1,miss.sum()))
        out[f"n_miss_m{m}"]=int(miss.sum())
    return out
print("part2 loaded: encoders + lexical + eval_cell")

# ---------------- DRIVER ----------------
def run(encoders, c_list, S_list, T, top_m_list, n_seeds, out_path):
    rows=[]
    t0=time.time()
    for enc in encoders:
        for S in S_list:
            tm=[m for m in top_m_list if m<=S]+([S] if S not in top_m_list else [])
            tm=sorted(set(tm))
            for c in c_list:
                # accumulate over seeds
                seed_metrics=[]
                for seed in range(n_seeds):
                    rng=random.Random(1000*S+100*int(c*100)+seed)
                    servers=build_registry(S,T,c,rng)
                    m=eval_cell(servers,S,T,enc,tm)
                    seed_metrics.append(m)
                # aggregate mean + 95% CI over seeds
                keys=set().union(*[set(d.keys()) for d in seed_metrics])
                agg={}
                for kk in keys:
                    vals=np.array([d[kk] for d in seed_metrics if kk in d and not (isinstance(d[kk],float) and math.isnan(d[kk]))],dtype=float)
                    if len(vals)==0:
                        agg[kk]=float('nan'); agg[kk+"_ci"]=float('nan'); continue
                    agg[kk]=float(vals.mean())
                    if len(vals)>1:
                        agg[kk+"_ci"]=float(1.96*vals.std(ddof=1)/math.sqrt(len(vals)))
                    else:
                        agg[kk+"_ci"]=0.0
                agg.update(dict(encoder=enc,S=S,c=c,T=T,top_m=tm,n_seeds=n_seeds))
                rows.append(agg)
                print(f"[{time.time()-t0:6.1f}s] {enc:24s} S={S:3d} c={c} done flat={agg.get('flat_rr'):.3f} "
                      f"ed_gap_m1={agg.get('ed_rr_gap_m1',float('nan')):.3f} pool_gap_m1={agg.get('pool_rr_gap_m1',float('nan')):.3f}",flush=True)
    json.dump(rows, open(out_path,"w"), indent=1)
    print("WROTE", out_path, "rows", len(rows), "elapsed", round(time.time()-t0,1),"s")
    return rows

if __name__=="__main__":
    print("CUDA:", torch.cuda.is_available(), "dev", os.environ.get("CUDA_VISIBLE_DEVICES"))
    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(0.30, 0)  # cap GPU mem
    ENCODERS=["BAAI/bge-base-en-v1.5","intfloat/e5-base-v2","lexical"]
    rows=run(ENCODERS, c_list=[0.5,0.7,0.9,1.0], S_list=[10,20,40], T=8,
             top_m_list=[1,2,3], n_seeds=12, out_path="/home/dengcchi/exp0060/results.json")
    print("DONE_ALL")
    sys.stdout.flush()
    os._exit(0)
