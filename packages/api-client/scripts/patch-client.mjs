/**
 * Compatibility patcher for the generated client (run after every generate).
 *
 * Two deviations between the generator output and the published
 * @hey-api/client-fetch are applied mechanically, so regeneration stays
 * reproducible:
 *   1. each `*Data` type gains the `url` (and `headers`) fields the SDK
 *      supplies at the call site but the published TDataShape requires;
 *   2. generated imports are repointed to ./runtime.ts, which widens
 *      Options with the per-request fields the runtime honours;
 *   3. parameterless endpoints are emitted as Options<unknown> — TDataShape
 *      fits and is imported as a type.
 * Delete this script and src/runtime.ts when the published types catch up.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

// Paths are anchored to this script so the step runs from any working directory.
const here = dirname(fileURLToPath(import.meta.url));

const types = join(here, '..', 'src', 'types.gen.ts');
let t = readFileSync(types, 'utf8');
if (!t.includes('Emitted by the SDK builder')) {
  t = t.replace(/^(export type \w+Data = \{\n)/gm,
    '$1  /** Emitted by the SDK builder at the call site; typed here to satisfy Options<TDataShape>. */\n  url: string;\n  headers?: Record<string, string>;\n');
  writeFileSync(types, t);
}

const services = join(here, '..', 'src', 'services.gen.ts');
let s = readFileSync(services, 'utf8');
s = s.replaceAll('(options?.client ?? client)', 'client');
s = s.replaceAll('"@hey-api/client-fetch"', '"./runtime"');
s = s.replaceAll('Options<unknown,', 'Options<TDataShape,');
if (!s.includes('type TDataShape,')) {
  s = s.replace('  type Options,\n', '  type Options,\n  type TDataShape,\n');
}
writeFileSync(services, s);
console.log('patched generated client');
