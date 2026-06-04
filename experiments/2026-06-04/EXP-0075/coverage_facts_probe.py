import json
import xgrammar as xgr
def accepts(s,i):
    g=xgr.Grammar.from_json_schema(s); cg=xgr.GrammarCompiler(xgr.TokenizerInfo([])).compile_grammar(g)
    m=xgr.GrammarMatcher(cg)
    if not m.accept_string(i): return False
    return m.is_terminated() or m.is_completed()
def w(l): return json.dumps({"type":"object","properties":{"x":l},"required":["x"],"additionalProperties":False})
facts={}
# 1. clean single-keyword (ARM1)
facts["clean_single_keyword_enforced"]={
 "minimum_int(min=10,viol=5)": not accepts(w({"type":"integer","minimum":10}),'{"x":5}'),
 "maximum_int(max=100,viol=999)": not accepts(w({"type":"integer","maximum":100}),'{"x":999}'),
 "minLength(5,viol=hi)": not accepts(w({"type":"string","minLength":5}),'{"x":"hi"}'),
 "maxLength(3,viol=abcdefg)": not accepts(w({"type":"string","maxLength":3}),'{"x":"abcdefg"}'),
 "pattern(^[a-z]+$,viol=ABC)": not accepts(w({"type":"string","pattern":"^[a-z]+$"}),'{"x":"ABC"}'),
 "multipleOf(5,viol=7)": not accepts(w({"type":"integer","multipleOf":5}),'{"x":7}'),
}
# 2. integer range boundary bug
facts["integer_max_boundary_bug"]={str(M): not accepts(w({"type":"integer","maximum":M}),'{"x":%d}'%(M+1)) for M in [100,130,153,180,255]}
facts["integer_min_boundary_bug"]={str(m): not accepts(w({"type":"integer","minimum":m}),'{"x":%d}'%(m-1)) for m in [1,2,5,10]}
# 3. number range dropped
facts["number_range_enforced"]= not accepts(w({"type":"number","minimum":5}),'{"x":4.0}')
# 4. integer-min violated by float
facts["int_min_violated_by_float(min=5,viol=4.0)"]= not accepts(w({"type":"integer","minimum":5}),'{"x":4.0}')
# 5. pattern+length interaction
facts["pattern_plus_maxLength_enforced"]= not accepts(w({"type":"string","pattern":"^[a-z]+$","maxLength":5}),'{"x":"aaaaaaaaaa"}')
facts["pattern_plus_minLength_enforced"]= not accepts(w({"type":"string","pattern":"^[a-z]+$","minLength":5}),'{"x":"aa"}')
facts["maxLength_alone_enforced"]= not accepts(w({"type":"string","maxLength":5}),'{"x":"aaaaaaaaaa"}')
facts["multipleOf_always_dropped"]= all(accepts(w({"type":"integer","multipleOf":m}),'{"x":%d}'%(m+1)) for m in [2,3,5,10])
print(json.dumps(facts,indent=2))
json.dump(facts,open("/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0075/coverage_facts.json","w"),indent=2)
