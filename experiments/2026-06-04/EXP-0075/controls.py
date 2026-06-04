"""Control arms for EXP-0075.
(a) OpenAI-strict supported-keyword set (documented, offline) -> D_openai over same keywords.
(b) Client-side re-validation (Instructor/LangChain style) -> does pydantic/jsonschema CATCH
    the one dropped keyword (multipleOf)? (Demonstrates the seam is at vLLM's server default.)"""
import json, jsonschema

KW=["minimum","maximum","exclusiveMinimum","exclusiveMaximum","multipleOf","minLength","maxLength","pattern"]

# (a) OpenAI strict Structured Outputs supported value-constraint keywords (docs, 2025-05-21 update).
# Per platform.openai.com/docs/guides/structured-outputs "Supported properties":
#   String:  pattern, format, minLength, maxLength
#   Number:  minimum, maximum, exclusiveMinimum, exclusiveMaximum, multipleOf
# => OpenAI-strict ENFORCES all 8 (D_openai = 0 over the same keyword set).
OPENAI_SUPPORTED = {
 "minimum":True,"maximum":True,"exclusiveMinimum":True,"exclusiveMaximum":True,
 "multipleOf":True,"minLength":True,"maxLength":True,"pattern":True,
}
print("=== CONTROL (a): OpenAI-strict documented supported value-constraint keywords ===")
print("    source: platform.openai.com/docs/guides/structured-outputs -> 'Supported properties'")
for k in KW:
    print(f"    {k:18s} OpenAI-strict ENFORCES = {OPENAI_SUPPORTED[k]}")
D_openai = sum(1 for k in KW if not OPENAI_SUPPORTED[k]) / len(KW)
print(f"    D_openai (fraction of these keywords OpenAI drops) = {D_openai:.3f}")

# (b) Client-side re-validation: take an instance that violates multipleOf (xgrammar's one drop)
#     and show jsonschema/pydantic CATCHES it -> a client step ABSENT from vLLM default server path.
print("\n=== CONTROL (b): client-side re-validation catches the dropped keyword (multipleOf) ===")
sch = {"type":"object","properties":{"qty":{"type":"integer","multipleOf":5}},
       "required":["qty"],"additionalProperties":False}
bad = {"qty":7}  # grammar-accepted (multipleOf dropped) but violates schema
try:
    jsonschema.validate(bad, sch); print("    jsonschema: VALID (unexpected)")
except jsonschema.ValidationError as e:
    print(f"    jsonschema re-validation CATCHES it: {e.message}")
# pydantic equivalent
try:
    from pydantic import BaseModel, Field, ValidationError
    class M(BaseModel):
        qty: int = Field(multiple_of=5)
    try:
        M(qty=7); print("    pydantic: VALID (unexpected)")
    except ValidationError as e:
        print(f"    pydantic re-validation CATCHES it: {e.errors()[0]['msg']}")
except Exception as e:
    print("    pydantic check err:", str(e)[:100])
print("    NOTE: this client re-validate step is NOT in vLLM's default OpenAI-compat server response path.")
