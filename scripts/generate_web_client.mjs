import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const schema = path.join(root, "apps/web/src/shared/api/generated/openapi.json");
const types = path.join(root, "apps/web/src/shared/api/generated/schema.d.ts");
const result = spawnSync(
  "corepack",
  ["pnpm", "--filter", "@fleet-maintenance/web", "exec", "openapi-typescript", schema, "-o", types],
  { cwd: root, stdio: "inherit" },
);
if (result.status !== 0) process.exit(result.status ?? 1);
