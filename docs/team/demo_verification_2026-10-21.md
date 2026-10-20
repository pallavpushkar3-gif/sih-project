# Dashboard presentation verification — 21 October 2026

**Prepared locally for owner review. Not pushed or deployed.** Source baseline: `fd81d73`.
Current captures use the running localhost:8080 application with existing synthetic supervisor
credentials. The running image's source identity was not independently matched to HEAD.

| Item | Result and scope |
|---|---|
| Dashboard gallery | Real local captures: overview, aircraft register, findings, maintenance, spares and analysis. No mocked API responses or fabricated values. |
| Mobile/themes | Actual browser captures at 390px for light/dark and desktop dark. These are selected visual checks, not full accessibility acceptance. |
| Ask AI record delivery | Two completed, cited service-backed answers were visible. In the first capture run, click-to-visible-final checks including a 300ms settling delay measured 680ms and 420ms. One sample each; no percentile, concurrency, cold-Qwen or WAN claim. |
| Generative inference | Model service unavailable in this local installation; the notice is retained in the image/recording. Qwen conversational quality and latency were not verified here. |
| Guided maintenance journey | Fresh local attempt found guided trials disabled. The annotated walkthrough uses retained prior captures and links the existing test/verification record. No new trial was completed. |
| Browser errors | Initial gallery run recorded zero JavaScript page errors. This does not establish all network calls/views succeeded; individual captures still require review for loading/unavailable states. |
| Public installation | Earlier read-only checks reported root/readiness/registration HTTP 200. This capture session does not verify public signup, role transitions, copilot or deployed revision. |
| Team | Six names/accounts supplied by the owner are recorded. Individual responsibilities were not supplied and are intentionally not invented. |

## Reviewable material

- [Dashboard gallery](../design/product_gallery.md)
- [Annotated historical maintenance walkthrough](../design/maintenance_walkthrough.md)
- [Team Null Paradox](team_null_paradox.md)
- [Ask AI recording](../design/recordings/ask-ai-record-answers.webm) — real-time local browser capture;
  direct record queries with model service unavailable, not Qwen generation.

## Remaining proof gaps

A fresh full maintenance walkthrough requires a configured isolated trial installation.
Generative Ask AI recording requires a working model service and explicit correctness/timing checks.
Team responsibilities need owner-supplied assignments. These limitations prevent calling every
requested proof item freshly verified. Do not replace an unavailable model or disabled trial with
scripted answers, altered screenshots or historical captures labelled as current.
