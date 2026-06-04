import json, urllib.request, random, re, ssl
random.seed(7)
d = json.load(open("apis_list.json"))
# collect the preferred spec swaggerUrl for each api
specs = []
for name, info in d.items():
    vs = info.get("versions", {})
    pref = info.get("preferred")
    v = vs.get(pref) or (list(vs.values())[0] if vs else None)
    if not v: continue
    url = v.get("swaggerUrl") or v.get("swaggerYamlUrl")
    if url: specs.append((name, url))
print("total specs with url:", len(specs))
sample = random.sample(specs, 150)
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
total_int_fields=0; int64_fields=0; apis_ok=0; apis_with_int64=0
err=0
for name, url in sample:
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'research'})
        raw = urllib.request.urlopen(req, timeout=12, context=ctx).read()
        txt = raw.decode('utf-8','ignore')
    except Exception:
        err+=1; continue
    apis_ok+=1
    # count integer-typed schema fields and how many declare format int64
    # crude but deterministic textual count over the spec JSON/YAML
    n_int = len(re.findall(r'"type"\s*:\s*"integer"', txt)) + len(re.findall(r'type:\s*integer', txt))
    n_int64 = len(re.findall(r'"format"\s*:\s*"int64"', txt)) + len(re.findall(r'format:\s*int64', txt))
    total_int_fields += n_int
    int64_fields += n_int64
    if n_int64>0: apis_with_int64+=1
print(json.dumps({
  "sampled_apis": len(sample),
  "fetched_ok": apis_ok,
  "fetch_errors": err,
  "total_integer_typed_fields": total_int_fields,
  "int64_format_fields": int64_fields,
  "pct_int_fields_that_are_int64": round(100*int64_fields/total_int_fields,2) if total_int_fields else 0,
  "apis_with_at_least_one_int64": apis_with_int64,
  "pct_apis_with_int64": round(100*apis_with_int64/apis_ok,2) if apis_ok else 0,
}, indent=2))
