import { defineConfig } from "@hey-api/openapi-ts";

// Regenerate with `make openapi` (root) or `pnpm --filter @replo/api-client generate`.
// The schema is exported from apps/api — never edit the generated files by hand.
export default defineConfig({
  input: "../api/openapi.json",
  output: "./src",
  // The modern fetch client (not `legacy/fetch`); it ships as
  // @hey-api/client-fetch and is a runtime dependency of this package.
  client: "@hey-api/client-fetch",
  schemas: true,
});
