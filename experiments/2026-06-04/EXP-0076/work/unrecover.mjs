import { z } from 'zod';
import { asSchema, safeParseJSON } from '@ai-sdk/provider-utils';
import { parse as losslessParse } from 'lossless-json';

const valStr = "1234567890123456789"; // a real-shaped snowflake > 2^53

console.log("=== UNRECOVERABILITY: the value is gone BEFORE any reviver/refine can see it ===");
const text = `{"id":${valStr},"ts":${valStr}}`;

// (1) .refine(Number.isSafeInteger) CANNOT recover: it runs AFTER parse, sees the already-rounded float.
const refineSchema = asSchema(z.object({
  id: z.number().refine(Number.isSafeInteger, { message: "unsafe int" }),
}));
const r1 = await safeParseJSON({ text, schema: refineSchema });
console.log("(1) z.number().refine(isSafeInteger): accepted =", r1.success,
  "-> it can REJECT but the original value is already lost. parsed =",
  r1.success ? BigInt(r1.value.id).toString() : "(rejected)", "vs original", valStr);

// (2) A JSON.parse reviver also runs AFTER native tokenization -> sees float, not text.
const revived = JSON.parse(text, (k, v) => v);
console.log("(2) JSON.parse reviver sees:", BigInt(revived.id).toString(), "!=", valStr,
  "-> reviver receives the float64, original digits unrecoverable");

// (3) The ONLY real fix: a LOSSLESS parser at PARSE time (lossless-json / BigInt reviver).
const ll = losslessParse(text, null, (value) => {
  // lossless-json reviver gets the raw numeric string -> can build BigInt losslessly
  return value;
});
console.log("(3) lossless-json parse: id =", String(ll.id), "matches original =", String(ll.id) === valStr);

// BigInt reviver at parse time (native JSON.parse cannot do this for numbers — reviver too late;
// demonstrate lossless-json is required, NOT the AI SDK default).
console.log("\n=== CONCLUSION: fix must be at PARSE time (lossless-json), which is NOT the AI SDK default ===");
