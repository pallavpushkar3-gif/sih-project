# Aircraft inspection verification — 2026-10-04

## Implemented and inspected

The actual React app was run against local FastAPI/PostgreSQL/RabbitMQ/Celery services with public simulated FD001 records and synthetic logistics. The aircraft inspection entry, component evidence, retained planning schedules, scenario results and unavailable-model fallback were captured and visually inspected. The neutral 64px header, local Inter, semantic colours, readable controls, larger nose-left aircraft framing and direct evidence action replace the previous navy-rail presentation. No reference screenshots were supplied in this session; the written brief guided implementation.

The Cesium GLB has a local license and a poster captured from its real render. Engine annotations and keyboard list selection share identity/state. Tests exercise aircraft switching, delayed previous responses, unavailable GLB, unavailable WebGL and lost context. Quantitative charts remain 2D with observation/result tables. The model evidence reads actual calibration and noncausal sensitivity metadata. Permissions, durable jobs and transactional approval remain server-owned.

## Verification environment and reproducibility

Base Git revision: `753dabb`; changes are an uncommitted working tree, including earlier authorized backend work. The source manifest in `artifacts/ui-redesign/source-manifest.json` identifies the checked code (SHA-256 `1107e4bb95c6e25f2111cc658311841f9cdb45479a7bf67d8b22c402598ebbdc`). All 55 recorded browser files matched the checked temporary copy. An earlier `git diff --check` passed; a final whole-worktree repeat stalled on host file reads and was interrupted, so that repeat is not a passed check. A narrower retry exited 138 without diagnostics and is also retained as unsuccessful. Existing host dependency reads repeatedly stalled/timed out, so browser checks used an exact source copy in `/tmp/fleet-ui-verification`, installed from the actual frozen pnpm lock into a fresh temporary store. This is a dependency workaround, not a replacement implementation. Backend checks used Docker's locked Python 3.13 dependencies, Torch 2.8.0 CPU and a separate PostgreSQL verification database. The demonstration workspace database was preserved.

Verified checks for this redesign:

- Web TypeScript and ESLint passed; production Vite build passed, with chart and aircraft runtime in separate lazy-loaded bundles. Six Vitest tests passed.
- Backend Ruff passed and mypy passed across 121 source files with Torch installed. The full backend suite passed **81 tests**, including sequence checks and PostgreSQL concurrent reservation evidence. Read-only inspection scope/free stock and immutable supply revisions are covered. The initial non-Torch/SQLite run passed 78 and skipped two; that limited run is superseded by the full dependency/database run.
- Browser tests cover API-fixture interaction paths separately from live local jobs/results. All **22 browser tests passed in 53.5 seconds** against the built Docker/Nginx preview at `http://localhost:8080`, with one Chrome worker and no service restarts. Five tests use live local API/jobs/results; the others use explicitly labelled API fixtures for edge cases and interaction contracts. Fixtures are named tests; runtime never substitutes these results.
- OpenAPI was exported from the actual running FastAPI app; `scripts/generate_web_client.mjs` generated the browser declarations. They were not hand edited.
- Actual Chrome browser zoom was set to 200% through native controls and inspected at upper/lower portions: layout stacked, controls/text remained readable and quantitative evidence remained available. Zoom was restored and the temporary review tab closed. Keyboard list selection, mobile dialog trapping/Escape/focus restoration and table viewport containment are tested. Reduced-motion and no-WebGL modes are separately checked. This does not claim a screen-reader audit or WCAG certification.

Representative actual-app captures (full ignored artifacts retained locally; selected PNGs are also retained in `docs/design/screenshots/` and linked from README):

| Surface | Artifact |
|---|---|
| Desktop 1440×900 | `artifacts/ui-redesign/inspection-1440x900.png` |
| Desktop 1366×768 | `artifacts/ui-redesign/inspection-1366x768.png` |
| Tablet 900×1000 / mobile 390×844 | `inspection-tablet.png` / `inspection-mobile.png` in the same directory |
| Reduced motion | `inspection-reduced-motion.png` |
| Engine/history/model evidence | `component-evidence.png` |
| Saved planning constraints | `planning-constraints.png` |
| Saved baseline/supply-delay comparison | `scenario-comparison.png` |
| Unavailable GLB fallback | `inspection-fallback.png` |

Run `FLEET_E2E_BASE_URL=http://localhost:8080 corepack pnpm --filter @fleet-maintenance/web test:e2e --workers=1` to check a built local preview; omit the environment variable to use the default development server.

Run `node scripts/capture_aircraft_ui.mjs` with installed browser dependencies and the local app running. `FLEET_CAPTURE_URL` chooses the local app (default 5173), `FLEET_CAPTURE_DIR` chooses output. `FLEET_POSTER_PATH` optionally captures the actual model canvas as a poster. The script deliberately returns 503 for the last GLB request to verify fallback; that expected exception is recorded separately from normal page errors. No protected operational data or external publishing is involved.

## Measured budgets and limits

Model raw size 586,652 bytes; reproducible gzip 515,163 bytes; both textures 1024²: the proposed compressed-size/texture budgets pass. The corrected production capture recorded an 8.2 ms GLB resource request (loopback, no network throttling). This is asset fetch time, not end-to-end first interactive time or public-host performance.

Headless Chrome 154 on macOS reported 8 logical threads, 16 GB `deviceMemory`, DPR 1 and a 1440×900 viewport. The corrected production build produced 150 requestAnimationFrame samples during scripted pointer orbit: median **16.7 ms**, p95 **16.8 ms**, passing the proposed local median ≤33 ms budget for this recorded run. Earlier development captures measured 33.3 ms / 33.4 ms and failed that strict budget; that evidence is retained. These measurements use different build/workload conditions and are browser frame intervals, not GPU render duration. No causal performance improvement is inferred from the comparison. Chrome Energy Saver was visible during native review; no power setting was changed. Intended-device/power/display/network acceptance remains pending. Full data is in `browser-verification.json`. Normal capture page/console errors were empty; the deliberately unavailable GLB reports expected 503 errors separately.

## Failures retained and corrected

Initial build failed on a direct `three-stdlib` type import; using the implemented OrbitControls component type fixed it. A test glob caught `/src/shared/api/` module requests and caused blank pages; restricting the pathname to `/api/` fixed it. Drei HTML annotations exposed a React root-unmount race and overlapping pointer labels; projected HTML buttons in the app's existing React tree fixed selection and error recovery. Visual review found white secondary-button text and small aircraft framing; semantic text colour and responsive camera fitting corrected them. Older live tests assumed a missing model even after an evaluated artifact was installed; they now use the actually unavailable component or inspect returned evidence. A live planner assertion used a five-second UI wait; it now follows the real durable result with a bounded 30-second wait. Comparison controls now have explicit label associations and stable scenario identities. Missing retained demand metadata prevents a comparison.

Typing against newer locked NumPy/Torch stubs exposed three return-type errors; explicit type casts preserve the original numerical operations. Initial optional-dependency skips are retained above. Deprecation warnings remain for Starlette/httpx, a NumPy boolean inversion and the upstream Three Clock/shadow fallback; they are not reported as scientific failures. A local frontend restart briefly used the base Compose configuration and dropped preview overrides; the isolated overrides were restored, with no volume/data deletion. Screenshot capture during that restart timed out and was retried against healthy services.

A final built-preview check exposed `TypeError: w is not a constructor` in the forced size-split chart vendor chunks. Development-mode checks had not exposed it. Removing the manual vendor size-split override retains route-level lazy loading and fixes initialization; the production browser suite was repeated. Node type definitions were also added explicitly for the configurable Playwright test base URL. The default build reports large lazy chart/3D chunks (about 542 kB / 1,004 kB minified); this warning is retained rather than hidden.

The production capture also exposed CSP-blocked WebAssembly initialization from the default Meshopt decoder. The registered GLB has no Draco/Meshopt extensions; `useGLTF` now disables those unused decoders, preserving the original strict `script-src` policy. No external decoder request or broad `unsafe-eval` permission was introduced. Console review then identified blocked embedded texture blob fetches. Both proxy policies now allow `blob:` only for image/connect resources; script policy remains unchanged. Browser regression checks and captures now retain console errors as well as page exceptions. This follows the [Drei loader implementation](https://github.com/pmndrs/drei/blob/master/src/core/Gltf.tsx); CSP WebAssembly behaviour is described in [MDN’s script-src reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src). Capture waits for a settled textured frame and hides live annotations while recording the asset poster.

## Acceptance still open

### Decision-flow follow-up

The subsequent [user flow](../product/user_flow.md) changes the default entry to `/overview`, reduces primary navigation to Start/Fleet/Planning and places supporting destinations in a shared dialog. Fleet register removes repeated summary/workflow panels; component model evidence precedes charts with an explicit next-step link. These are local working-tree changes based on `b73bbef`, preserving earlier work.

`COREPACK_HOME=/tmp/fleet-corepack make web-check` passed, including six unit tests. The built Chrome run at `http://localhost:8080` passed 30/31 tests in 49.5 seconds. The one failure exposed an existing test dependency on a pre-existing baseline scenario outcome. Explicit baseline calculation and equality-checking its saved record fixed that dependency; the corrected scenario test passed in a separate 4.2-second run. All 31 distinct checks passed across runs; final lint/typecheck passed. Five cases used the real local API/job chain, 26 used labelled API fixtures. This is not new model-accuracy evidence.

Actual source-rendered desktop captures (1440×900) are `artifacts/ui-flow/start-desktop.png`, `fleet-desktop.png` and `component-desktop.png`; mobile (390×844) is `start-mobile.png`. Captures were inspected; no page exceptions or mobile page overflow were recorded. The Start route chunk is 3.08 kB minified / 1.22 kB gzip and imports neither chart nor 3D renderer. No end-to-end latency improvement is inferred from bundle size. The fresh local setup still shows legitimate model-unavailable evidence. Participant comprehension remains untested and the release gaps below remain open.

Intended-device performance acceptance and the participant comprehension study remain open. The latest local production orbit measurement passes its declared budget; that does not establish all-device performance. Public trusted HTTPS deployment is blocked pending real AWS host/domain/credentials and host checks. Internal untouched-engine alert evaluation is blocked because all 100 FD001 training engines were already used; no independent operational complete-history data or operator-approved alert/cost targets were supplied. Explanation-stability, broader robustness and workload acceptance gaps retain their earlier status. This is implemented demonstrator work with explicit evidence limits, not operational aircraft readiness or a claim of 100% release acceptance.

## Customer trial — 2026-10-05

The full Chrome suite passed **34/34 in one run** against `http://localhost:8080` (eight live service cases, 26 API-fixture cases). Three new live cases cover the customer's actual entered cutoff/usage/supply, real model/plan/simulation jobs, expected-stock approval block, receipt/replanning, original-plan preservation, actual reservation/consumption, completed-work reload, insufficient-history withholding and an impossible review window. The full happy path recorded no page exceptions; mobile withholding remained within 390px. Source/artifact qualifications remain distinct from UI verification.

Actual desktop entry, AI, options and completed-work plus mobile withholding captures are retained in ignored `artifacts/ui-flow/customer-trial-*.png` and were visually reviewed. The original interactive aircraft renders in the trial; model and fallback inspection regressions still pass. Review found and fixed inaccessible cutoff labelling, tight card spacing, low-contrast text-button styling and the cached-old-proposal approval gap after receipt. Saved inputs now show the actual case and download exact imported rows. These checks establish demonstrator behaviour, not participant comprehension or intended-device performance acceptance.

A fourth live trial case additionally verified user-supplied edited JSON, exact imported cutoff rows and the assessment’s retained import/source hash. The expanded full run passed 34/35; the upload assertion was corrected to compare actual JSON bytes/values, which normalize negative zero to zero, and that case passed separately. **35 distinct browser checks passed across the final runs (nine live, 26 fixture); no single 35/35 run is claimed.** No application change was needed for this assertion.

## Release-v2 verification

The final isolated built application passed **37/37** browser checks in one run (`browser-ready-final.log`), including initial-load/contrast/keyboard and actual-health-change checks: the same model and logistics at cutoffs 140 and 180 change the actual estimate, policy review state and conservative planning window. A prior run started before web readiness and recorded seven connection failures; it is retained. Full final evidence is indexed in `docs/team/release_acceptance.md`.

`browser-performance.json` records unthrottled desktop Chrome initial `/demo` requests/navigation/long tasks and token contrast against white. Case entry downloads no AircraftScene or GLB until interactive exploration; a 2D engine action remains keyboard accessible. The final parallel-suite observation had DOM content ready at about 206ms and no observed >50ms task during that bounded capture; this is not production/device performance acceptance. Final main JS was 394.99KB uncompressed (124.47KB gzip), lazy chart 541.62KB (184.18KB gzip), lazy 3D 1,003.75KB (268.73KB gzip). Chunk warnings remain visible; thresholds were not raised. Full-library replacement was not justified by this small local measurement.

Selected checks cover [WCAG 2.2](https://www.w3.org/TR/WCAG22/) keyboard/focus, labels/errors, mobile containment, graphic fallback and semantic text colors against white. They do not assess every rendered combination or full AA conformance. The intended-user study is specified in `user_study_protocol.md` and remains pending. Build guidance follows [Vite](https://vite.dev/guide/build.html); dynamic optional-route loading and runtime validation are implemented, not evidence of universal responsiveness.
