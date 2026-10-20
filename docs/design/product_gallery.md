# AeroCare product gallery

Published in commit `0765bdb`, with captures prepared 21 October 2026. These captures come from the real
local application at `http://localhost:8080`, with a synthetic supervisor account, at source
revision `fd81d73`. They are not mockups or new public-deployment verification. The API's
runtime image revision was not independently matched to that source revision.

## Fleet dashboard

![Fleet dashboard](screenshots/product/fleet-dashboard.png)

## Aircraft register

![Aircraft register](screenshots/product/aircraft-register.png)

## Findings and maintenance

![Findings](screenshots/product/findings.png)

![Maintenance](screenshots/product/maintenance.png)

## Spares and analysis

![Spares](screenshots/product/spares.png)

![Analysis](screenshots/product/analysis.png)

## Research workspace

![Research workspace](screenshots/product/research.png)

Research availability depends on installed evidence; a screenshot is not model qualification.

## Ask AI: actual record answers

![Completed record answers with citations](screenshots/product/ask-ai.png)

The visible model-unavailable notice is retained. These are service-backed record answers,
not a demonstration of generative Qwen inference. The owner reports that the separate deployed
generative assistant is fixed and responsive; the local notice does not describe its current state. The short recording and exact measurement
scope are linked in the [verification summary](../team/demo_verification_2026-10-21.md).

## Dark theme and mobile

![Dark dashboard](screenshots/product/dashboard-dark.png)

| Mobile light | Mobile dark |
|---|---|
| ![Mobile light](screenshots/product/dashboard-mobile-light.png) | ![Mobile dark](screenshots/product/dashboard-mobile-dark.png) |

## Maintenance walkthrough

Follow the [annotated walkthrough](maintenance_walkthrough.md). It uses retained historical
captures because the current local installation disables the guided-trial entry.
