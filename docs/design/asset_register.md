# Asset register

Downloaded/registered 2026-10-04. Assets are served locally; normal runtime does not depend on a remote model or font CDN.

| Asset | Source / author / license | Local use and modifications |
|---|---|---|
| Cesium Air GLB | [CesiumJS sample source](https://github.com/CesiumGS/cesium/tree/main/Apps/SampleData/models/CesiumAir), [exact downloaded file](https://raw.githubusercontent.com/CesiumGS/cesium/main/Apps/SampleData/models/CesiumAir/Cesium_Air.glb). Copyright 2011–2026 CesiumJS Contributors; repository Apache 2.0 notice retained in `apps/web/public/licenses/cesium-LICENSE.md`. No individual artist is identified by the inspected source. | `apps/web/public/models/aircraft.glb`, original binary unchanged. Runtime recenters/rescales a clone, supplies studio lighting/shadow and synthetic engine annotations. Source livery remains asset artwork; no operational airframe, fleet or product branding is inferred. |
| Aircraft fallback poster | Derived by rendering the above licensed GLB in the implemented viewer with `scripts/capture_aircraft_ui.mjs`; same source attribution/Apache notice. | `apps/web/public/models/aircraft-poster.png`; actual canvas capture, no evidence values or mapped labels baked into the model image. |
| Inter Latin regular/medium/semibold | [Inter project](https://github.com/rsms/inter), [Fontsource package](https://fontsource.org/fonts/inter/about), Copyright 2016 The Inter Project Authors; SIL OFL 1.1 retained in `apps/web/public/licenses/inter-OFL.txt`. | Installed `@fontsource/inter` 5.3.0; bundled CSS/local font files. No font modification. |
| Shared line icons | Repository-authored SVG paths in `shared/ui/Icon.tsx`. | Existing local icon system extended for account access. No external aircraft brand icons. |

GLB SHA-256: `e72f627c5f0c9dc50726059703df55d74e634a32dbccb25b18f1783f913360b8`. Raw 586,652 bytes; reproducible gzip 515,163 bytes (mtime=0), below the proposed 10 MB compressed budget. Both embedded images are 1024×1024 (JPEG body artwork and PNG propeller), below 2K. Model meshes are `Cesium_Air` and shared `Prop`; no validated separable engine assembly/explode model is supplied. These measurements describe asset delivery, not physical fidelity.

The earlier unused bitmap illustration remains in the repository but is no longer imported by the fleet register or inspection route. No reference screenshot, Bombardier identity, passenger count or cabin controls were copied into product data. Before substituting an asset, record exact source/license/author, acquisition date, modifications and measurements here.
