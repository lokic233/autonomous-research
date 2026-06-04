import { readFileSync, writeFileSync } from 'node:fs';
import { z } from 'zod';
import { tool } from 'ai';
import { asSchema, safeParseJSON } from '@ai-sdk/provider-utils';

// EXACT production path replication.
// AI SDK v6 ai/src/generate-text/parse-tool-call.ts::doParseToolCall does:
//   const schema = asSchema(tool.inputSchema);
//   const parseResult = await safeParseJSON({ text: toolCall.input, schema });
// where safeParseJSON internally does secureJsonParse(text) -> validateTypes({value, schema}).
// We call the SAME exported functions with the SAME schema wrapper.

const probes = JSON.parse(readFileSync('probes.json','utf8'));

// Two schema variants the claim names:
//  - plain z.number()  (the "recommended pattern" default for an integer arg)
//  - z.number().int()  (the explicit-integer pattern)
const toolPlain = tool({
  description: 'lookup by id',
  inputSchema: z.object({ id: z.number(), ts: z.number() }),
});
const toolInt = tool({
  description: 'lookup by id',
  inputSchema: z.object({ id: z.number().int(), ts: z.number().int() }),
});
const schemaPlain = asSchema(toolPlain.inputSchema);
const schemaInt = asSchema(toolInt.inputSchema);

// Run one probe through the real path for a given schema.
async function runOne(valStr, schema) {
  // Serialize EXACTLY as a provider hands tool_call.function.arguments: raw integer literal, no quotes.
  const toolInputText = `{"id":${valStr},"ts":${valStr}}`;
  const res = await safeParseJSON({ text: toolInputText, schema });
  if (res.success) {
    // BigInt-exact comparison: the parsed value is a JS number (float64). Convert back to its
    // exact integer decimal via BigInt(value) and compare to the original decimal STRING.
    const parsedId = res.value.id;
    let parsedExactStr;
    try { parsedExactStr = BigInt(parsedId).toString(); }
    catch { parsedExactStr = String(parsedId); }
    const survived = (parsedExactStr === valStr);
    return { accepted: true, survived, parsedExactStr };
  } else {
    return { accepted: false, survived: false, parsedExactStr: null };
  }
}

async function runVariant(schema, label) {
  const rows = [];
  let totalAbove=0, survAbove=0, acceptedCorruptAbove=0, corruptAbove=0;
  let totalBelow=0, survBelow=0;
  for (const [band, source, valStr] of probes) {
    const r = await runOne(valStr, schema);
    rows.push({ band, source, original: valStr, parsed: r.parsedExactStr ?? '', survived: r.survived?1:0, zod_passed: r.accepted?1:0 });
    if (band === 'above') {
      totalAbove++;
      if (r.survived) survAbove++;
      const corrupted = !r.survived;       // value cannot be represented exactly -> corrupted
      if (corrupted) { corruptAbove++; if (r.accepted) acceptedCorruptAbove++; }
    } else {
      totalBelow++;
      if (r.survived) survBelow++;
    }
  }
  const survival_above = survAbove/totalAbove;
  const survival_below = survBelow/totalBelow;
  const silent_pass = corruptAbove ? acceptedCorruptAbove/corruptAbove : 0; // frac of CORRUPTED that Zod accepted
  // write CSV
  const header = 'band,source,original,parsed,survived,zod_passed\n';
  const csv = header + rows.map(r=>`${r.band},${r.source},${r.original},${r.parsed},${r.survived},${r.zod_passed}`).join('\n');
  writeFileSync(`results_${label}.csv`, csv);
  return { label, totalAbove, totalBelow, survival_above, survival_below, silent_pass, corruptAbove, acceptedCorruptAbove };
}

const out = {};
out.plain = await runVariant(schemaPlain, 'plain');
out.int = await runVariant(schemaInt, 'int');

// node/zod/sdk versions
out.versions = {
  node: process.version,
};
console.log(JSON.stringify(out, null, 2));
writeFileSync('js_summary.json', JSON.stringify(out, null, 2));
