# FD001 evidence and proposed acceptance targets

Status: **user-approved demonstrator targets frozen on 2026-10-04; evaluation pending**. These remain provisional product limits, not scientifically established operational limits. The official test RUL labels remain outside model selection. Targets are recorded in `configs/acceptance_proposal.yaml`; The user authorized freezing that policy before the official final-test evaluation. Passing it would support a simulated FD001 demonstrator claim, not aircraft maintenance clearance.

## Exact dataset and project protocol

The source is NASA C-MAPSS FD001, not N-CMAPSS or the multi-condition FD002/FD004 subsets. NASA documents 100 training and 100 test engines, one sea-level condition and one high-pressure-compressor degradation mode. Histories are noisy simulator outputs with differing initial wear; training reaches failure and test histories stop earlier. Each row has engine ID, cycle, three settings and 21 sensors. [NASA dataset documentation](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data).

The downloaded archive and FD001 files match every SHA-256 recorded in `data/sources.yaml`. The current loader requires the 26-column schema, finite values and consecutive cycles. Train and test engine numbers are separate identities. The implemented split is 70 fit, 15 validation and 15 calibration engines, seed 26249; all windows of an engine remain together. History/window minimum is 30 cycles. RUL is capped at 125 cycles as an early-life modelling convention, not a physical lifetime limit.

Measured on the reacquired **training partition only**: 20,631 rows; lifetime minimum/median/maximum 128/199/362 cycles; lifetime quartiles 177 and 229.25 cycles; zero nonfinite values. Seven columns are exactly constant: setting 3 and sensors 1, 5, 10, 16, 18, 19. Small numerical standard deviations of constant columns are floating-point summation effects. Sensor scales differ substantially, so the fitted transform and feature order must travel with the model. No operational missingness, maintenance action costs, spare-parts demand or inspection truth is supplied by FD001.

The current model derives current/mean/slope features and cycle number. It fits scaling only on fit engines. Validation and calibration each use one seeded cutoff per engine. The existing validation baseline MAE 9.42/RMSE 12.61 cycles and calibration residual quantile 30.55 cycles are internal diagnostics; they are not official-test benchmark scores. Fifteen calibration engines and calibration-set coverage cannot establish independent test coverage.

## Published reference, with comparability limits

Li, Ding and Sun (2018) report FD001 DCNN RMSE **12.61 ± 0.19** cycles and asymmetric score **273.7 ± 24.1**, with 100 test engines, 30-cycle windows and 125-cycle early-life cap. Their within-study neural-network RMSE is 14.80; their table lists an earlier window-based NN at 15.16. They use 14 selected sensors, a different model and training procedure. This project trains on only 70 of the 100 supplied training engines, so those numbers are context, not a reproduced head-to-head comparison. The reference does not establish our model's MAE, intervals or alert rates. [Author manuscript, Tables 1–4](https://escholarship.org/content/qt5ns8r3fs/qt5ns8r3fs.pdf).

Li et al. (2019) report their ensemble ResCNN FD001 RMSE **12.16** and score **212.48**. This is an additional published point-estimation reference, not an interval or operational alert benchmark. [Original research article](https://doi.org/10.3934/mbe.2019040).

NASA's original simulation paper describes an asymmetric score that penalizes late predictions more heavily. It also explains that the scoring preference must reflect the actual application; this benchmark does not supply this project's maintenance costs or tolerances. [Saxena et al., 2008](https://ntrs.nasa.gov/api/citations/20090029214/downloads/20090029214.pdf).

## Proposed product targets

| Metric | Proposed gate | Basis and limitation |
|---|---|---|
| RMSE | ≤15 cycles | Rounded provisional competitiveness floor near the historical NN references (14.80/15.16); weaker than the published DCNN. This is a chosen product target, not a validated universal threshold. |
| MAE | ≤12.5 cycles | A provisional average error allowance of 10% of the 125-cycle capped range. The reviewed references do not establish an MAE cutoff; no conversion from RMSE to MAE is assumed. |
| Interval coverage | 90% nominal; ≥90% observed, plus one-sided exact 95% lower bound ≥80% | Report successes/eligible engines and exact binomial uncertainty. The 80% floor acknowledges sampling uncertainty at about 100 independent engines; it does not assert 90% conditional coverage. Reject small unsupported groups or disclose them. |
| Interval width | Mean ≤62.5 cycles | A provisional utility limit of half the capped range; otherwise coverage could be purchased by unhelpfully broad intervals. Also report median, p90 and life-stage widths. Current symmetric pre-clipping width is about 61.10 cycles; its calibration diagnostic does not validate this utility target. |
| Missed events | ≤5% of eligible held-out complete failure histories | Provisional conservative target reflecting the late-error cost asymmetry. No inspected publication establishes this rate as operationally safe. Require detection before failure, report lead time and confidence bounds, and count withholding as a miss where a timely warning is absent. |
| False alerts | ≤10 early actionable episodes per 100 complete engine histories | Provisional workload target, episode start before the 45-cycle detection window. Report exposure and episode duration as well; this is not a 10% per-cycle false-positive rate. |

The 45-cycle warning horizon is inherited from the demonstration policy, **not** a validated procurement/inspection lead time. Maintenance slots are a separate synthetic unit; cycles must not be silently converted to hours or calendar deadlines.

## Required validation before acceptance

1. Freeze the proposal, model/transform/calibration hashes, seeds and metric definitions before opening official final-test labels. Retain any failures without retuning that same test.
2. Evaluate one final observed cutoff per eligible official test engine, with both capped-primary and uncapped-secondary error/coverage reports. Report short histories as withholding; never exclude failures silently. Bootstrap engine-level MAE/RMSE uncertainty and report the asymmetric late-error score.
3. Measure calibrated intervals on independent engines, not the 15 calibration observations. Show coverage and widths by true RUL band (0–20, 21–45, 46–125, >125 uncapped), with counts. Exchangeability of random calibration cutoffs and official truncation points is an assumption to investigate, not a guarantee.
4. Validate alerts by replaying independent complete run-to-failure trajectories. Official truncated test data alone cannot evaluate warnings through failure or distinguish all no-event periods. Current five synthetic histories test policy mechanics only. Extend held-out trajectory evaluation or obtain an independently reserved failure set; do not reuse fit engines as acceptance evidence.
5. For zero misses, the one-sided 95% upper miss-rate bound is `1 - 0.05 ** (1/n)`: about 18.1% for 15 engines and below 5% only with at least 59 independent events. A point rate of zero on 15 engines is insufficient evidence for a validated 5% miss bound. False-episode rates similarly need engine-level resampling/exposure reporting and cost review.
6. Repeat missingness/noise interventions and report withholding and error together. Serving currently withholds missing histories rather than claiming the offline imputation experiment is supported online.
7. Review warning horizon, tolerable missed events, false-alert workload and interval usefulness with an actual operational owner before any real-use claim. Public FD001 contains no evidence that can settle that decision.

No final-test pass, operational safety claim or complete original release acceptance is asserted by this proposal.
