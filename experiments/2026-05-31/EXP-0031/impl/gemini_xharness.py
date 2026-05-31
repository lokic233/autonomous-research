#!/usr/bin/env python3
"""Cross-harness replication (Gemini CLI corpus) for CLAIM-0011 gate-taxonomy + recovery-modality.
CPU/stdlib-only. Mirrors EXP-0009 (Claude Code) and codex_xharness.py logic, re-implemented for
Gemini CLI's session schema: ~/.gemini/tmp/*/chats/session-*.json
  messages[].toolCalls[] = {name, args, result[].functionResponse.response, status, resultDisplay}
  status in {success, error}; error text in resultDisplay / functionResponse.response.error.

Gemini tool inventory (this corpus): read_file, write_file, list_directory, glob, grep_search,
run_shell_command (HARD-BLOCKED in this harness), activate_skill. NO web/fetch tool present.
"""
import json, glob, os, re, math
from collections import Counter, defaultdict

ROOT = os.path.expanduser("~/.gemini/tmp")
K = 6

# ---- intent classes (file-discovery / file-read / file-write / exec / skill) ----
DISCOVERY = {'glob','list_directory','grep_search'}   # find files / search content / list dirs
READ      = {'read_file'}
WRITE     = {'write_file','replace'}
def intent_gem(name):
    n = name or ''
    if n in DISCOVERY: return 'DISCOVERY'
    if n in READ:      return 'FILE_READ'
    if n in WRITE:     return 'FILE_WRITE'
    if n == 'run_shell_command': return 'EXEC'   # but in THIS harness it routes to discovery/edit
    if n == 'activate_skill':    return 'SKILL'
    return 'OTHER'

def err_class_gem(name, rd, fre):
    t = (str(rd) + ' ' + str(fre)).lower()
    if 'not found. did you mean' in t or ('not found' in t and 'did you mean' in t):
        return 'policy.tool_blocked'        # REDIRECTABLE: hard tool-block + sanctioned alternative
    if 'path not in workspace' in t:
        return 'policy.workspace_boundary'  # policy gate, no alt-tool (different path, same tool)
    if 'must have required property' in t:
        return 'schema.missing_param'       # TRANSIENT: fixable in place
    if 'invalid regular expression' in t:
        return 'arg.bad_regex'              # TRANSIENT
    if 'no such file' in t or 'does not exist' in t or 'enoent' in t:
        return 'fs.notfound'
    return 'other.error'

# gate-type taxonomy (harness-agnostic): REDIRECTABLE / GRANT_REQUIRED / TRANSIENT
def gate_type(cls):
    if cls == 'policy.tool_blocked':       return 'REDIRECTABLE'   # blocked tool + sanctioned alt
    if cls == 'policy.workspace_boundary': return 'GRANT_REQUIRED' # policy block, no alt tool; needs corrected path/grant
    return 'TRANSIENT'

def parse(fp):
    """ordered tool calls across the session: name,intent,is_error,err_class,text"""
    try: d = json.load(open(fp))
    except Exception: return []
    calls = []
    for m in d.get('messages', []):
        for tc in (m.get('toolCalls') or []):
            name = tc.get('name')
            st   = tc.get('status')
            is_err = (st == 'error')
            rd = tc.get('resultDisplay') or ''
            fre = ''
            for r in (tc.get('result') or []):
                if isinstance(r, dict):
                    fr = r.get('functionResponse', {})
                    resp = fr.get('response', {}) if isinstance(fr, dict) else {}
                    if isinstance(resp, dict) and 'error' in resp:
                        fre = str(resp['error'])
            cls = err_class_gem(name, rd, fre) if is_err else None
            calls.append({'name': name, 'intent': intent_gem(name),
                          'is_error': is_err, 'cls': cls,
                          'text': (str(rd) + ' ' + str(fre))[:160]})
    return calls

def wilson(k, n, z=1.96):
    if n == 0: return (float('nan'), float('nan'))
    p = k / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (max(0.0, c-h), min(1.0, c+h))

files = glob.glob(os.path.join(ROOT, '*', 'chats', 'session-*.json'))
sessions = [parse(f) for f in files]
sessions_nz = [s for s in sessions if any(c['name'] for c in s)]
sessions = [s for s in sessions if len(s) >= 1]

ncall = sum(len(s) for s in sessions)
fails = []  # (si, i, cls, intent, name)
for si, s in enumerate(sessions):
    for i, c in enumerate(s):
        if c['is_error']:
            fails.append((si, i, c['cls'], c['intent'], c['name']))

# ---- recovery + modality (BROAD, K=6) ----
# SAME_TOOL_RETRY: a later success with the SAME tool name within K
# CROSS_TOOL_REDIRECT: no same-tool success, but a later success with a DIFFERENT tool within K
#   For the tool_blocked gate, the blocked tool can NEVER succeed (it's not in the inventory),
#   so ANY in-thread recovery is necessarily a cross-tool redirect -> this is the cleanest
#   redirectable-gate modality probe.
def recovered_modality(si, i, name):
    s = sessions[si]
    same = redir = False
    for j in range(i+1, min(i+1+K, len(s))):
        c = s[j]
        if c['is_error']: continue
        if c['name'] == name: same = True
        else: redir = True
    if same:  return 'SAME_TOOL_RETRY'
    if redir: return 'CROSS_TOOL_REDIRECT'
    return None

print(f"Gemini corpus: {len(files)} session files, {len(sessions_nz)} with tool calls, "
      f"{ncall} tool calls, {len(fails)} ground-truth failures (status==error)")
print()

# per-class census
cls_n=Counter(); cls_rec=Counter(); cls_redir=Counter(); cls_same=Counter()
gate_n=Counter(); gate_rec=Counter(); gate_redir=Counter(); gate_same=Counter()
for (si,i,cls,intent,name) in fails:
    cls_n[cls]+=1
    g=gate_type(cls); gate_n[g]+=1
    m=recovered_modality(si,i,name)
    if m:
        cls_rec[cls]+=1; gate_rec[g]+=1
        if m=='CROSS_TOOL_REDIRECT': cls_redir[cls]+=1; gate_redir[g]+=1
        else: cls_same[cls]+=1; gate_same[g]+=1

print("PER-ERROR-CLASS modality (n=failures; rec=recovered in K=6; redir_share=cross-tool / recovered):")
print(f"{'class':28} {'n':>3} {'rec':>3} {'rec_rate':>8} {'redir':>5} {'same':>4} {'redir_share':>11}  gate")
for cls,n in cls_n.most_common():
    rc=cls_rec[cls]; rd=cls_redir[cls]; sm=cls_same[cls]
    rr=rc/n if n else 0
    rs=rd/rc if rc else float('nan')
    print(f"{cls:28} {n:>3} {rc:>3} {rr:>8.3f} {rd:>5} {sm:>4} {rs:>11.3f}  {gate_type(cls)}")
print()
print("PER-GATE-TYPE modality (the harness-agnostic taxonomy):")
print(f"{'gate':16} {'n':>3} {'rec':>3} {'redir':>5} {'same':>4} {'redir_share':>11}  {'Wilson95 (redir/rec)':>22}")
for g in ['REDIRECTABLE','GRANT_REQUIRED','TRANSIENT']:
    n=gate_n[g]; rc=gate_rec[g]; rd=gate_redir[g]; sm=gate_same[g]
    rs=rd/rc if rc else float('nan')
    lo,hi=wilson(rd,rc)
    print(f"{g:16} {n:>3} {rc:>3} {rd:>5} {sm:>4} {rs:>11.3f}  [{lo:.3f},{hi:.3f}]")
print()

# ---- THE REDIRECTABLE-GATE ANCHOR (run_shell_command hard-block) ----
# Codex/CC anchor was the web-block. Gemini has NO web tool; its REDIRECTABLE anchor is the
# run_shell_command hard-block ("not found. Did you mean grep_search/...") = blocked tool +
# explicit sanctioned alternative.
print("="*70)
print("REDIRECTABLE-GATE ANCHOR: run_shell_command hard-block (Gemini's web-block analog)")
print("  block text: 'Tool \"run_shell_command\" not found. Did you mean grep_search/replace/cli_help?'")
blocks=0; in_thread_redir=0; abandon=0; same_tool=0
routes=Counter()
for si,s in enumerate(sessions):
    for i,c in enumerate(s):
        if not (c['is_error'] and c['cls']=='policy.tool_blocked'): continue
        blocks+=1
        # the blocked tool can never succeed; look for ANY successful tool in window = in-thread redirect
        got=None
        for j in range(i+1, min(i+1+K, len(s))):
            n=s[j]
            if n['is_error']: continue
            got=n['name']; break
        if got is None:
            abandon+=1
        elif got==c['name']:
            same_tool+=1   # impossible for a blocked-not-in-inventory tool, but checked for honesty
        else:
            in_thread_redir+=1; routes[(c['name'],got)]+=1
lo,hi=wilson(in_thread_redir, blocks)
print(f"  total run_shell_command blocks: {blocks}")
print(f"  recovered IN-THREAD by cross-tool REDIRECT (success within K={K}): {in_thread_redir}")
print(f"  abandoned / no in-thread recovery: {abandon}    same-blocked-tool 'success': {same_tool}")
print(f"  in-thread redirect-share (redir / all blocks): {in_thread_redir}/{blocks} = "
      f"{in_thread_redir/max(blocks,1):.3f}  Wilson95 [{lo:.3f},{hi:.3f}]")
print("  redirect routes (blocked -> recovered-with):")
for k,v in routes.most_common(): print('    ', k[0],'->',k[1],'x',v)

# also: redirect-share AMONG RECOVERED (matching CC 66/66, Codex 0/142 framing)
rec_total=in_thread_redir+same_tool
loR,hiR=wilson(in_thread_redir, rec_total) if rec_total else (float('nan'),float('nan'))
print(f"  redirect-share among RECOVERED (redir/(redir+same)): "
      f"{in_thread_redir}/{rec_total if rec_total else 0} "
      + (f"= {in_thread_redir/rec_total:.3f} Wilson95 [{loR:.3f},{hiR:.3f}]" if rec_total else "= n/a (0 recovered)"))

# ---- QUALITATIVE: show each run_shell_command block + the following window (in-thread check) ----
print()
print("="*70)
print("QUALITATIVE in-thread check (each block -> next calls, same gemini turn = in-thread):")
bi=0
for si,s in enumerate(sessions):
    for i,c in enumerate(s):
        if not (c['is_error'] and c['cls']=='policy.tool_blocked'): continue
        bi+=1
        print(f"\n  BLOCK #{bi} (sess {si}, pos {i}):  {c['name']} -> ERROR")
        for j in range(i+1, min(i+1+K, len(s))):
            n=s[j]
            mark = 'ERR' if n['is_error'] else 'OK '
            print(f"     +{j-i}  [{mark}] {n['name']:18} {('('+n['cls']+')') if n['is_error'] else ''}")
