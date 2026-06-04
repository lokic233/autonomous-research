import { readFileSync, writeFileSync } from 'node:fs';
import { z } from 'zod';
import { tool } from 'ai';
import { parseToolCall } from 'ai/dist/index.mjs';  // may not be exported; fallback below
