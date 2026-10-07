# PS 26249: Predictive Maintenance & Fleet Availability

This plan goes from understanding to solution, then data, ML, architecture and implementation. It is written so you can hand sections to Antigravity phase by phase.

**Labels used throughout**
- **[PS]**: stated in the problem statement
- **[ASSUMPTION]**: a reasonable engineering assumption
- **[REAL DATA]**: would need real operational data to settle

Section 19 is the consolidated plan. It points back to the detailed sections instead of repeating them.

---

# PART A: Understanding the problem

## 1. Deep problem analysis

### 1.1 The real-world problem
- **[PS]** Availability is low because maintenance is fragmented and mostly reactive. Four data sources are not integrated: health-monitoring systems, technical records, spares, and maintenance agencies.
- **[PS]** The stated consequences are delayed fault prediction, avoidable downtime, and sub-optimal use of critical assets.
- **[ASSUMPTION]** In practice, an aircraft is grounded for three kinds of reasons:
  1. A fault occurs and nobody saw it coming.
  2. The fault is known, but the spare is not in stock.
  3. The spare is in stock, but the workshop or agency is backlogged.

  Prediction alone fixes only the first. A credible solution must also cover spares and workshop capacity. This is the central insight of the solution.

### 1.2 Stakeholders (all [ASSUMPTION])

| Stakeholder | What they need |
|---|---|
| Fleet / maintenance commander | Fleet availability today and in 30 days; where the risk is |
| Maintenance planner | Which aircraft to pull, when, in what order |
| Line technician / engineer | Which component to inspect, and why the system flagged it |
| Logistics / spares officer | Which spares will be needed, and shortfalls |
| Maintenance agency / workshop manager | Incoming workload and turnaround tracking |
| Reliability engineer | Failure trends, MTBF, bad-actor components |

### 1.3 Decisions maintenance personnel face today
1. Which aircraft to ground or inspect now versus defer.
2. Whether to replace a component early or keep flying.
3. Which scheduled tasks to bundle with an unscheduled one to save downtime.
4. How to order a backlog when several aircraft need work.
5. Which spares to order or reposition, and how early.
6. Which jobs to send to the workshop versus do in-house.
7. How many aircraft will be available next week or month.

### 1.4 Causes of low availability
- Unscheduled failures (corrective maintenance).
- Conservative fixed-interval replacement that wastes good components and still misses random failures.
- Waiting for parts (a "supply wait" category).
- Workshop turnaround delays and repeat defects.
- Poor visibility: no single view of aircraft state, parts and workshop load.
- Maintenance clustering, where many aircraft hit scheduled servicing at once.

### 1.5 What "fragmented data" means
Each of the four sources lives in a separate system, format and ownership: sensor downloads, paper or semi-digital logbooks, a stores system, and agency reports. They have different aircraft/part identifiers, different timestamps and no common key. Nobody can ask a question like "which aircraft have a rising hydraulic temperature trend, a pump with a long lead time, and a workshop already at capacity?"

**The solution's data layer therefore needs a unified identifier model** (aircraft → system → component → part number).

### 1.6 Realistic data sources

**Aircraft health-monitoring data**
- Per-flight or per-sortie summaries by parameter: engine temperatures, pressures, vibration levels, oil pressure/temperature, hydraulic pressure and temperature, bus voltages, fuel flow, cabin/ECS temperatures.
- Exceedance events, fault codes and built-in-test (BIT) messages, plus operating-condition context (flight hours, altitude band, ambient temperature, load).
- **[ASSUMPTION]** Real systems often download summaries post-flight rather than streaming. Simulating per-flight aggregates is more honest than faking high-rate IoT.

**Technical records / logbooks**
- Snag (defect) reports: date, aircraft, system, description, severity, reported by.
- Rectification actions taken, and component installation and removal history with part and serial numbers.
- Flight hours, cycles and landings, and scheduled inspection compliance with due dates.
- Modifications and directives.

**Spares and inventory**
- Part number, description, which components it fits, criticality and unit cost.
- Stock on hand and reserved, reorder level, lead time, and supplier/depot.
- Issue and receipt transactions, and repairable versus consumable status.
- Parts awaiting repair, and quantity pending procurement.

**Maintenance agency / workshop**
- Work-order ID, aircraft/component, agency, date received, promised and actual completion date, and status.
- Workshop capacity (bays, man-hours) and turnaround times.
- Findings on teardown, and repeat-defect flags.

### 1.7 Key KPIs
Fleet availability, aircraft-days lost (split by cause), MTBF, MTTR, maintenance turnaround time, unscheduled-to-scheduled maintenance ratio, backlog (open work orders and man-hours), spares fill rate / stock-out count, repeat-defect rate, predicted-versus-actual failure hit rate (once the model is running), and lead time gained (days of warning before failure).

### 1.8 Fleet availability: definition and calculation
**[ASSUMPTION]** The PS does not define it. I recommend stating this definition in your pitch, so evaluators see a deliberate choice.

Each aircraft-day is assigned one state:
- **Available (fully serviceable)**
- **Partially available**: flyable with a non-critical defect (optional; keep it simple in the MVP)
- **Unavailable, scheduled maintenance**
- **Unavailable, unscheduled repair**
- **Unavailable, awaiting spares** (the supply-wait state)
- **Unavailable, awaiting workshop/agency**

```
Fleet availability (%) = (Σ aircraft-days in Available state) / (Σ aircraft-days in period) × 100
```

Related standard measures:
- Inherent availability Ai = MTBF / (MTBF + MTTR)
- Operational availability Ao = MTBM / (MTBM + MDT), where MDT includes supply and admin delay

**Showing Ao alongside Ai makes the point visually:** the gap between them is the logistics and delay loss that predictive maintenance plus spares planning can recover.

### 1.9 Core concepts

- **Predictive maintenance:** use condition data to estimate when a component will degrade or fail, and intervene at the right time. That avoids both unplanned failures and wasteful early replacement.
- **Anomaly detection:** flagging data that deviates from expected normal behaviour, without needing labelled failures. It answers "is something unusual happening?"
- **Failure-risk prediction:** a probability that a component fails within a defined window, e.g. 14 days. It answers "how likely, and how soon?"
- **Remaining Useful Life (RUL):** the estimated remaining time (flight hours, cycles or days) before a component reaches a failure or retirement threshold. Always report it as a range, not a single number.
- **Maintenance types:**

| Type | Trigger | Weakness |
|---|---|---|
| Corrective | After failure | Unplanned downtime, possible secondary damage |
| Preventive | Fixed interval (hours/calendar) | Replaces healthy parts, misses random failures |
| Predictive | Measured condition | Needs data and model trust |

The platform does not abolish preventive maintenance. It adds a predictive layer on top, and keeps mandatory scheduled inspections as non-negotiable tasks.

### 1.10 Where digital twins and IoT fit
- **Digital twin (practical):** a software record of each aircraft and component holding configuration, current health state, history and predicted degradation. It also supports "what-if" runs. It is not a CFD or physics simulator. A physics twin would need proprietary design data you will not have.
- **IoT / health monitoring:** the data-acquisition layer. For this project, a data-ingestion API that accepts post-flight sensor summaries, plus a simulator that plays the role of the aircraft. This is honest, demonstrable and extensible to a live stream later.

### 1.11 What the platform should support
Prioritising an at-risk list, recommending an action, checking spares, proposing a schedule, quantifying availability impact, and comparing alternatives. It should do this with explanations.

### 1.12 What this plan deliberately avoids
- Real aircraft type names, real fleet numbers, or real failure modes of any specific type.
- Combat, weapons or mission-planning functions.
- Claims of model accuracy on real data. All accuracy numbers will be on synthetic data and labelled as such.

---

# PART B: Solution concept

## 2. Modules

Working name: **"Integrated Predictive Maintenance & Fleet Availability Platform"**.

| # | Module | Status |
|---|---|---|
| 1 | Data Integration Layer | **Essential** |
| 2 | Fleet Overview Dashboard | **Essential** |
| 3 | Aircraft Health Monitoring (incl. anomaly detection) | **Essential** |
| 4 | Predictive Maintenance Engine (risk + RUL + recommendations) | **Essential** |
| 5 | Digital Twin (software-level) | **Essential** (the PS names it) |
| 6 | Spares / Inventory Intelligence | **Essential** |
| 7 | Maintenance Planning and Work Orders (combined) | **Essential** |
| 8 | Fleet Availability Engine and Scenario Simulator | **Essential** (the PS's outcome) |
| 9 | Alerts | **Essential, minimal version** |
| 10 | Reports and Analytics | Optional (a lightweight analytics page) |
| 11 | Maintenance Agency Tracking | Folded into module 7 (agency field plus turnaround stats) |
| 12 | AI Maintenance Assistant (LLM) | **Future scope / stretch.** MVP uses template-based explanations |

### Module details

**1. Data Integration Layer**
- **Purpose:** unify the four sources under one schema. *User:* system (indirectly everyone).
- **Input:** CSV/Parquet or API payloads for sensors, logbook, spares and agency data.
- **Processing:** schema validation, ID mapping, timestamp normalisation, duplicate and missing-value handling, data-quality scoring.
- **Output:** clean relational tables plus a data-quality report.
- **Why:** this literally solves the "fragmented" half of the PS.

**2. Fleet Overview**
- *User:* commander. *Input:* aircraft states and predictions. *Processing:* aggregation. *Output:* availability %, aircraft by state, top risks, upcoming maintenance, spares alerts.
- **Why:** the first thing a decision-maker sees.

**3. Aircraft Health Monitoring**
- *User:* engineer. *Input:* sensor summaries. *Processing:* residual-based and Isolation Forest anomaly scoring. *Output:* trend charts with anomaly markers and a per-system health index.
- **Why:** it is the evidence behind every prediction.

**4. Predictive Maintenance Engine**
- *User:* planner/engineer. *Input:* features from sensors and history. *Processing:* failure-risk model, RUL model, rule-based priority. *Output:* a "maintenance advisory" per component (details in Section 5).
- **Why:** this is the core AI/ML value.

**5. Digital Twin**
- *User:* all. *Input:* hierarchy, health states, predictions, history. *Processing:* state update after each inference run. *Output:* an interactive aircraft → system → component view with health state and history.
- **Why:** it is a named technology opportunity, and it gives the integrated view.

**6. Spares Intelligence**
- *User:* logistics officer. *Input:* stock, lead times, predicted component demand. *Processing:* match advisories to stock, flag shortfalls, forecast demand. *Output:* "spare available / short by N / lead time exceeds RUL".
- **Why:** it addresses the supply-wait cause of downtime.

**7. Maintenance Planning and Work Orders**
- *User:* planner/workshop manager. *Input:* advisories, spares, hangar/bay capacity. *Processing:* schedule suggestions and delay-time prediction. *Output:* a work-order list, proposed slots and expected downtime.
- **Why:** it turns insight into action.

**8. Availability Engine and Scenario Simulator**
- *User:* commander/planner. *Input:* current fleet state, schedule, spares. *Processing:* availability calculation plus a Monte Carlo simulation. *Output:* current and forecast availability, and scenario A versus B comparisons.
- **Why:** it demonstrates the PS outcome (availability) directly and quantitatively.

**9. Alerts**
- Rule-based: risk above threshold, spare shortfall against RUL, overdue inspection, backlog above limit. Shown in-app only for the MVP; email and SMS are future scope.

### MVP definition
The MVP is modules 1–9 with **one fleet, 7 systems, about 20 component types, and 3 predictive models** (anomaly detection, failure risk, RUL), plus the rule-based priority and the simulation. The delay model, spare demand forecast and LLM assistant are stretch goals.

---

# PART C: Data strategy

## 3. Synthetic data

### Design principles
1. **Latent-health simulation:** each component has a hidden health index that degrades over time. Sensors are noisy functions of that hidden state plus operating conditions. Failures happen when health crosses a threshold. This is how NASA's C-MAPSS turbofan dataset was constructed, and it gives ML real structure to learn.
2. **Correlation by design:** components in the same system share stress factors, and operating conditions (ambient temperature, flight profile) affect sensor baselines.
3. **Ground truth stays hidden:** the true health value is stored in a separate "simulation truth" table that ML must not train on. It is used only for evaluation and for demo storytelling.

### Parameters ([ASSUMPTION], all configurable)

| Item | Choice |
|---|---|
| Fleet | 40 aircraft of one **generic** type (e.g. "Generic Twin-Engine Transport"). No real type name. |
| Period | 3 years of history (2023-01 to 2025-12) plus a "current" window ending today, with the last 60 days kept unlabelled for live demo |
| Utilisation | about 0.8–1.5 flights per aircraft-day, 1–2.5 flight hours each |
| Sensor granularity | one summary row per flight per monitored parameter (mean, max, min, std) |

### Aircraft hierarchy
Fleet → Aircraft → System → Component → (optional) Part instance.

| System | Example components |
|---|---|
| Propulsion (engine) | Compressor, Turbine, Oil system, Fuel control unit |
| Hydraulics | Pump, Actuator, Reservoir/filter |
| Electrical | Generator, Battery, Bus controller |
| Landing gear | Brake assembly, Strut, Tyre |
| Avionics | Flight computer, Display unit, Sensor suite |
| Fuel | Boost pump, Fuel quantity sensor |
| Environmental (ECS) | Cooling pack, Pressure controller |

That is about 20 component types per aircraft, so 800 component instances across the fleet. Keep it generic and non-sensitive.

### Entities and key columns

Ask Antigravity to produce the full DDL from this.

**Reference**
- `aircraft(aircraft_id, tail_code, type_code, commissioned_date, total_flight_hours, total_cycles, base_id)`
- `systems(system_id, name)` and `component_types(component_type_id, system_id, name, criticality 1–5, design_life_hours, mtbf_hours, part_number, is_repairable)`
- `components(component_id, aircraft_id, component_type_id, serial_no, installed_date, hours_at_install, hours_since_new, status)`

**Operations**
- `flights(flight_id, aircraft_id, date, duration_hours, cycles, ambient_temp_c, altitude_band, load_factor)`
- `sensor_readings(reading_id, flight_id, component_id, parameter, mean, max, min, std, quality_flag)`
- `fault_events(event_id, aircraft_id, component_id, timestamp, fault_code, severity, description, source)`

**Maintenance**
- `maintenance_events(event_id, aircraft_id, component_id, type [scheduled/unscheduled/inspection], start, end, action [replace/repair/inspect], labor_hours, work_order_id, root_cause)`
- `work_orders(wo_id, aircraft_id, component_id, agency_id, opened, planned_start, actual_start, promised_done, actual_done, status, priority, delay_reason)`
- `agencies(agency_id, name, level [line/base/depot], bays, capacity_hours_per_day, avg_turnaround_days)`
- `scheduled_tasks(task_id, aircraft_id, task_name, interval_hours, last_done_hours, due_hours, due_date)`

**Spares**
- `spare_parts(part_number, description, criticality, unit_cost, lead_time_days, reorder_level)`
- `inventory(part_number, location_id, on_hand, reserved, on_order, expected_receipt_date)`
- `inventory_transactions(txn_id, part_number, date, qty, type [issue/receipt/repair-return], work_order_id)`

**Derived / platform-generated**
- `aircraft_daily_status(aircraft_id, date, state, reason)`: the availability ground truth
- `anomaly_scores`, `predictions`, `twin_snapshots`, `alerts`, `scenario_runs` (Section 15)
- `simulation_truth(component_id, date, true_health)`: **hidden from ML**

### How each thing is simulated

**Component degradation (item 14).** Each component draws a degradation process: health starts near 1.0 and decreases through a stochastic process (gamma or Wiener with drift). The drift rate depends on stress, e.g. higher ambient temperature and higher load factor wear faster. Draw a per-component "personality" (some units are weak) so failures are not perfectly predictable. Failure = health hits 0, or a random shock event for a small share (about 15%) of failures that give little warning. **Include these sudden failures deliberately.** They keep the model honest and let you discuss limitations.

**Sensor readings (item 8).** Each parameter follows this pattern:
`reading = baseline(operating conditions) + signature(health) + noise`
- The signature is parameter-specific and drifts as health declines: vibration rises, hydraulic pressure drops or oscillates, oil temperature creeps up, bus voltage becomes unstable.
- Multiple parameters per component respond with different sensitivities and lags, so models must combine them.
- Operating conditions shift the baseline, which means a naive threshold fails and a residual or normalised approach works. This is a legitimate technical talking point.

**Missing and noisy data (item 15).** Random dropout (2–5% of readings), occasional stuck-at values, sensor drift on a few non-failing sensors (false-alarm sources), a handful of outlier spikes, and a few flights missing entire downloads. Add a `quality_flag`.

**Failures (item 9).** Each failure creates a `fault_event` (possibly preceded by earlier minor fault codes) and an unscheduled `maintenance_event`, and the true failure date is stored in the truth table.

**Maintenance events (item 10).**
- *Scheduled:* periodic inspections and time-based replacements (preventive baseline).
- *Unscheduled:* triggered by failure.
- After any replacement, the component's health resets with a new serial number.
- Duration is drawn from a distribution by task type.

**Spares and inventory (item 11).** Initial stock per part is set using a reorder rule. Issues occur when maintenance events consume parts. Receipts arrive after a random lead time (some very long for critical items). Some parts occasionally hit zero stock so there are real supply waits.

**Work orders and delays (items 12–13).** Each maintenance event spawns a work order. Delay causes are modelled: awaiting spares (conditional on stock), agency queue (conditional on load in that agency), awaiting manpower, and awaiting inspection. Turnaround = repair time + queue wait + spare wait, with random variation. This gives the delay model real signal.

**Realistic correlations (item 16).** These come from:
1. shared stress drivers (temperature, load) across components,
2. propagation (a degrading hydraulic pump raises actuator stress),
3. agency load driving delay,
4. spare criticality and lead time driving supply waits,
5. utilisation driving wear.

**Demo seeding.** Reserve 3–4 "hero" aircraft with scripted degradation so your live demo has guaranteed, interesting storylines (Section 10). Use a fixed random seed for reproducibility. Disclose that these are scripted.

### Validation against public data
Run your RUL and anomaly pipeline once on NASA's public **C-MAPSS** turbofan degradation dataset as a sanity check. That shows the ML code works on non-self-generated data. Keep it as a side script. It is a credibility add-on, not core.

---

# PART D: AI/ML strategy

## 4. Model-by-model

**General approach:** every task gets a simple baseline first, then a recommended model. Splits must be **temporal, and also grouped by aircraft where possible**, to prevent leakage (random row splits will inflate results badly).

### A. Anomaly detection
- **Formulation:** unsupervised "is this flight's behaviour unusual for this component under these conditions?"
- **Features:** the sensor summary statistics, normalised for operating condition. Rolling windows (last 5, 20 flights): mean, slope, std, deviation from the component's own baseline.
- **Target:** none (unsupervised). Evaluate against the known degradation onset in synthetic truth.
- **Baseline:** fixed thresholds / rolling z-score.
- **Candidates:** residual model (regress sensor on operating conditions, flag large residuals), Isolation Forest, autoencoder.
- **Recommended:** **residual + Isolation Forest.** Both are fast and explainable (the residual says *which* parameter and *by how much*). Skip autoencoders in the MVP, because they add training complexity without clearer explanations.
- **Metrics:** detection lead time (days before failure the first sustained alert fires), false-alarm rate per 1,000 flights, and recall of degradation episodes.
- **Output/display:** anomaly score timeline with shaded alert regions on the sensor chart, and "top contributing parameters".

### B. Failure prediction
- **Formulation:** for each component on each day, classify whether it fails within the next *H* days (H=14, maybe also 30).
- **Features:** rolling sensor statistics and slopes, anomaly scores, hours since new / since last maintenance, cycles, recent fault-event counts, operating-stress summaries, component type and criticality.
- **Target:** binary `fail_within_H_days`.
- **Baseline:** logistic regression.
- **Candidates:** logistic regression, Random Forest, XGBoost, LightGBM.
- **Recommended:** **LightGBM** (or XGBoost) with calibrated probabilities; keep logistic regression in the pipeline as the interpretable baseline. Use SHAP for per-prediction explanation.
- **Handling imbalance:** class weights and PR-AUC as the headline metric, not accuracy. Do not use SMOTE, because it is unnecessary and risky with time series.
- **Metrics:** PR-AUC, recall at a fixed precision, calibration curve/Brier score, and *lead-time distribution of true alerts*.
- **Output/display:** risk score 0–100 (calibrated probability), a "risk band" (Low/Watch/High/Critical), and a SHAP bar chart.

### C. Remaining Useful Life
- **Formulation:** regress days (or flight hours) to failure. Use a **clipped target** (e.g. cap at 60 days), the standard trick from C-MAPSS work, because a component far from failure is simply "healthy".
- **Features:** same as B, plus health-indicator trend and its slope.
- **Baseline:** linear extrapolation of a smoothed health indicator to its threshold.
- **Candidates:** gradient-boosted regression, survival models (Cox or Weibull via `lifelines`), LSTM/GRU.
- **Recommended:** **LightGBM regression with quantile outputs (10th/50th/90th percentile)** to give a range. Optionally add a Weibull survival model as a cross-check and to handle censoring (components never seen failing). Skip LSTM in the MVP: it is plausible on synthetic data but harder to explain and tune. Mention it as future scope if you have time to compare it against the baseline.
- **Metrics:** MAE and the C-MAPSS-style asymmetric score (late predictions penalised more), interval coverage (does the 10–90 band contain the truth about 80% of the time?).
- **Output/display:** "RUL ≈ 18 days (range 11–27)" with a shrinking-RUL plot over time.

### D. Maintenance priority
- **Formulation:** a **transparent rule-based score, not ML.** Priority needs to be auditable and tunable by users, and there is no ground-truth label for "correct priority".
- **Formula (example, adjustable):**
  `priority = w1·risk + w2·criticality + w3·(1 / RUL) + w4·spare-shortfall-penalty + w5·availability-impact`
- **Output:** P1/P2/P3/P4, with the contributing factors shown.
- **Why not ML:** saying "I used a rule so the commander can understand and change it" is a strength.

### E. Spare parts demand forecasting
- **Formulation:** expected demand for each part over the next 30/60/90 days.
- **Features:** predicted failures from model B/C, scheduled-task demand, historical issue rates, fleet utilisation.
- **Baseline:** moving-average historical consumption.
- **Recommended:** **demand = scheduled demand + expected predicted-failure demand** (sum of calibrated failure probabilities over the horizon), compared against the baseline. This ties spares to the predictive engine, which is the integrated story. Croston's method is an option for intermittent parts.
- **Metrics:** MAE or a pinball loss, stock-out hit rate in backtest.
- **Display:** "Part X: expected demand 3 (range 1–5) in 30 days; stock 2; lead time 45 days → shortfall risk".

### F. Fleet availability forecasting
- **Formulation:** projected availability for the next 7–30 days.
- **Recommended: simulation, not ML.** Use a Monte Carlo discrete-event model (Section 7) driven by risk scores, schedules, spares and capacity. Report P10/P50/P90.
- **Why:** it is explainable and supports what-if runs, which a black-box time-series forecast cannot.
- **Optional baseline:** a seasonal/naive time series to show the simulation beats it.

### G. Maintenance delay prediction (stretch)
- **Formulation:** predict work-order turnaround days.
- **Features:** component type, agency, agency queue length, spare availability, priority, day of week.
- **Baseline:** agency average turnaround.
- **Recommended:** LightGBM regression.
- **Metrics:** MAE against the baseline.
- **Display:** "expected completion: Mar 14 (±3 days)".

### Models summary (for your pitch)
**3 core ML models + 1 optional + a rule engine + a simulation.** Everything with a clear reason, no deep learning in the MVP.

---

# PART E: Predictive maintenance logic

## 5. The pipeline

```
Sensor/flight data → Processing → Features → Health Indicators → Anomaly Detection
  → Risk/RUL → Priority → Recommended action → Spares check → Scheduling → Availability impact
```

| Stage | Produces |
|---|---|
| 1. Data processing | Clean, validated, time-aligned readings and a data-quality flag per reading |
| 2. Feature engineering | Rolling means, slopes, volatility, deviations from the component's baseline, operating-condition-normalised values, counters since last maintenance |
| 3. Health indicator (HI) | One 0–100 score per component, derived from a weighted combination of normalised parameters (or a PCA/first-component score). System and aircraft HI roll up from components, weighted by criticality |
| 4. Anomaly detection | Anomaly score plus top contributing parameters |
| 5. Risk / RUL | Failure probability in 14/30 days, RUL with a 10–90 range |
| 6. Priority | P1–P4 with a factor breakdown |
| 7. Recommended action | One of: *continue monitoring / inspect at next opportunity / schedule replacement within X days / ground now* (from rules on risk, RUL and criticality) |
| 8. Spares check | Required part number, stock status, lead time versus RUL |
| 9. Scheduling | A proposed maintenance window using bay and workshop capacity, bundled with scheduled tasks when possible |
| 10. Availability impact | Predicted aircraft-days lost under *act now* versus *wait* |

### The "Maintenance Advisory" object
This is the product's central output. It replaces "component will fail":

```
Aircraft AC-017 | Hydraulics | Main pump
Health state: Degraded (HI 41/100, down from 68 over 20 days)
Risk: 14-day failure probability 0.62 (High)
RUL: ~12 days (range 7–19)
Contributing parameters: outlet-pressure oscillation ↑ (+3.1σ), fluid temp ↑ (+2.4σ)
Recommended action: replace within 7 days
Priority: P2
Spare: Pump P/N HYD-114 — 1 in stock (reserved: 0) ✔
Expected downtime: ~2.5 days (incl. bay wait)
Availability impact: replace now −2.5 aircraft-days; run to failure −9.0 expected
Confidence/limits: model confidence moderate; 18% of this pump class fails without warning
```

### Guard rails against false confidence
- Calibrated probabilities and ranges, never a single date.
- A "confidence" note (data quality, model uncertainty).
- Mandatory scheduled inspections are never overridden by the model.
- A human-in-the-loop status on each advisory: *Proposed → Accepted → Scheduled → Completed / Dismissed (with reason)*. Dismissal reasons are fed back as a monitoring signal.

---

# PART F: Digital twin and availability

## 6. Digital twin

**Definition for this project:** a continuously-updated software model of the fleet that stores structure, state, history and prediction for every aircraft and component, and can be queried and simulated. **[ASSUMPTION]** This is the right scope for a student team and still meets the PS's "digital twins" wording.

### Data model
```
Fleet → Aircraft → System → Component
  each node: { id, type, config, health_index, health_state, risk, rul, last_updated,
               maintenance_history[], predicted_trajectory[] }
```

### Health states
**Healthy** (HI ≥ 80) → **Watch** (60–80) → **Degraded** (40–60) → **Critical** (<40 or risk > 0.7) → **Failed** → **Under maintenance** → back to **Healthy** (new part). Thresholds are configurable. Roll-up: an aircraft's state is the worst state among its critical components, with the contributing component shown.

### Component lifecycle
Installed → in service (hours and cycles accumulate) → degradation → maintenance trigger (predicted or scheduled) → removed → repaired or scrapped → returns to stores or is replaced. Serial numbers are tracked through this cycle.

### How ML updates the twin
After each batch inference run (daily in the demo, or on new data ingestion), the engine writes: HI, anomaly score, risk, RUL, and a `twin_snapshot` row. The twin's current state is the latest snapshot; history is the snapshot series. A "twin time slider" can replay past states.

### User interaction
Click the fleet → click an aircraft → system map → component panel (sensor trend, advisory, history) → "Run what-if" button.

### Visualisations
- A fleet heat-grid (aircraft × system, coloured by health state).
- A **generic 2D aircraft schematic (SVG)** with systems highlighted by health. This is much cheaper than Three.js and easier to maintain, and it is clear enough for a demo. Use Three.js only if there is spare time at the end, and treat it as cosmetic.
- A hierarchical tree.
- A degradation trajectory plot with a projected threshold crossing.
- A maintenance history timeline.

### What-if scenarios from the twin
1. "Replace this component now" versus "defer 10 days".
2. "What if this spare is unavailable?"
3. "What if two aircraft need the same bay at the same time?"

## 7. Fleet availability engine

### Metrics

| Metric | Definition |
|---|---|
| Fleet availability | See §1.8 |
| Aircraft serviceability | Fraction of aircraft currently available (a snapshot) |
| Downtime | Aircraft-days not available, split by cause (scheduled, unscheduled, supply wait, agency wait) |
| MTBF | Total operating hours ÷ number of failures, per component type |
| MTTR | Mean active repair time |
| Turnaround time | Mean time from work-order open to aircraft release, including waits |
| Failure rate | Failures per 1,000 flight hours |
| Readiness proxy | Fraction of aircraft that are available *and* have no P1/P2 open advisory. Label it a proxy, not an operational readiness measure |
| Component health | Distribution of HI states |
| Spare availability | Fill rate; parts with stock below predicted demand |
| Backlog | Open work orders and outstanding man-hours |

### How decisions affect availability
- An early replacement costs a known, short, **planned** downtime and can be scheduled when spares and bays are free.
- A deferred replacement risks a longer **unplanned** outage, with possible supply wait and queue.
- Bundling tasks reduces total downtime.
- Spare shortfalls convert a short repair into a long outage, so ordering early is high-leverage.

### Simulation (scenario) engine
A lightweight **Monte Carlo discrete-event simulation** over a 14–60 day horizon, run roughly 200–500 times:
- **State:** each aircraft's state, the open work orders, bay occupancy, spare stock and incoming receipts.
- **Events:** component failures (sampled from the model's risk/RUL distribution), repairs, receipts, scheduled-task starts.
- **Outputs:** the availability curve with P10/P50/P90 bands, aircraft-days lost by cause, and the probability of a stock-out.

### Scenario types

| Scenario | Interventions modelled |
|---|---|
| "Schedule aircraft X for maintenance on date D" | Aircraft removed from the pool for the estimated duration; planned instead of risked downtime |
| "Critical spare unavailable" | Stock set to 0 or lead time extended; the repair waits |
| "Address predicted failure early" | Replacement moved earlier vs. baseline "run to failure" |
| "Add one bay / extra shift" | Capacity changed |

Each run returns a **side-by-side comparison** (baseline vs. scenario) with the difference in expected availability and aircraft-days lost. **Framing:** these are decision-support simulations on synthetic maintenance data, not operational planning.

---

# PART G: Architecture and UX

## 8. System architecture

```
[Simulator / CSV importers] → [Ingestion API + validation]
                                   ↓
                    [PostgreSQL: relational + readings]
                                   ↓
        [ML pipeline (batch)] → [Model artifacts] → [Inference service in FastAPI]
                                   ↓
        [Twin updater] [Alert engine] [Availability engine/simulator]
                                   ↓
                         [FastAPI REST API layer]
                                   ↓
                           [React dashboard]
```

| Layer | Choice | Why |
|---|---|---|
| Frontend | **React + Vite + TypeScript + Tailwind**; charts with **ECharts** (rich time series, heatmaps) or Recharts (simpler); React Router; TanStack Query | Standard, well-supported by coding agents. Skip Three.js initially |
| Backend | **Python 3.11 + FastAPI**, Pydantic, SQLAlchemy 2, Alembic | Same language as ML, auto-generated API docs help the demo |
| Database | **PostgreSQL** (plain). **TimescaleDB not justified**: about a few million sensor rows is easy for indexed Postgres | Fewer moving parts. Mention Timescale as a scaling path |
| Ingestion | REST endpoints plus a CLI loader. No Kafka/MQTT | Honest for batch post-flight downloads. Mention streaming as a future path |
| ML | pandas, NumPy, scikit-learn, **LightGBM**, SHAP, lifelines (optional), joblib. **No PyTorch in MVP** | Explainable, quick to train on a laptop |
| Model serving | Load joblib artifacts at FastAPI startup; batch scoring job plus an on-demand endpoint | Avoids a separate model server |
| Scheduling | A CLI/cron-style script, or APScheduler | Enough for a demo |
| Alerts | Rule engine writing to `alerts`, shown in UI | MVP |
| Auth | JWT, three roles (Commander, Planner, Technician), seeded demo users | Basic security story: role-based views, password hashing, input validation |
| Logging/monitoring | Python structured logging, a `/health` endpoint, model-run logs in DB, simple data-drift check | Production-style without a full observability stack |
| Packaging | **Docker Compose** (db + backend + frontend) | "Demonstrable locally" requirement |
| CI | GitHub Actions: lint + tests + build | Optional but good |

**Optional AI assistant (stretch):** an LLM chat that answers from your own API (never from free text) such as "Why is AC-017 flagged?". Add it only after everything else works. The MVP uses template-based natural-language explanations generated from the advisory fields, which are deterministic and cannot hallucinate.

## 9. User experience: screens

Seven screens, with others merged or cut.

**1. Fleet Dashboard**
- *Purpose:* instant fleet picture. *KPIs:* availability % (today, 7-day, 30-day forecast), aircraft by state, open P1/P2 advisories, backlog, parts at risk.
- *Charts:* availability trend with forecast band; downtime-by-cause stacked bar; aircraft × system health heat-grid.
- *Tables:* top-10 risk advisories; upcoming maintenance. *Filters:* date range, base, system. *Alerts:* banner strip.
- *Drill-down:* click aircraft → Aircraft Detail; click advisory → Component view.

**2. Aircraft Detail (with Digital Twin tab)**
- *Purpose:* all information about one aircraft. *KPIs:* HI, state, flight hours since last inspection, open work orders.
- *Views:* system schematic and tree, component list with HI/risk/RUL, history timeline.
- *Interactions:* select a component → Component view; "What-if" → Simulator pre-filled.

**3. Component Health / Health Monitoring**
- *Purpose:* evidence behind a flag. *Charts:* multi-parameter sensor trends with anomaly shading and operating-condition overlay, HI trajectory with projected threshold crossing, SHAP contributors, RUL band.
- *Panels:* the Maintenance Advisory card, with Accept/Dismiss/Schedule buttons.

**4. Predictive Maintenance (risk queue)**
- *Purpose:* the planner's worklist. *Table:* all advisories sorted by priority, with risk, RUL, spare status, expected downtime, and recommended action. *Filters:* priority, system, spare status, aircraft. *Interactions:* bulk-select to Plan.

**5. Maintenance Planning and Work Orders**
- *Purpose:* convert advisories to scheduled work. *Views:* Gantt-style timeline by aircraft and bay; work-order table with agency, status, promised vs. actual dates, delay reason.
- *KPIs:* backlog, turnaround, on-time rate. *Interactions:* drag or select a slot, then see the availability impact immediately.

**6. Spares Inventory**
- *Purpose:* connect demand to stock. *Table:* part, stock, reserved, on order, lead time, 30-day expected demand, status (OK / At risk / Short). *Charts:* demand-vs-stock bars, lead time versus RUL scatter for flagged parts. *Alerts:* shortfall.

**7. Scenario Simulator**
- *Purpose:* decision support. *Inputs:* scenario type and parameters. *Outputs:* baseline vs. scenario availability curves with bands, aircraft-days lost delta, stock-out probability. *Interaction:* save scenario, compare up to three.

**Analytics** (MTBF, MTTR, failure rate, model-performance panel) is an optional eighth page; keep it to one scrollable page, and cut it if time runs short. **AI Assistant** is a stretch.

---

# PART H: Demo

## 10. Demo story (about 6–7 minutes)

Use a scripted "hero" aircraft, AC-017, with a degrading hydraulic main pump. Spare stock is deliberately tight, so the supply-wait point lands.

| Step | UI state | Data visible |
|---|---|---|
| 1. Fleet Dashboard | Availability 82%, 30-day forecast trending down to 74% | Aircraft states, heat-grid with AC-017 hydraulics amber, 2 spares-at-risk flags |
| 2. Spot the issue | Click AC-017 → heat-grid cell; Aircraft Detail opens | System "Degraded"; HI 68 → 41 over 20 days |
| 3. Sensor trends | Component page, hydraulic pump | Outlet-pressure oscillation and fluid temperature drifting; fixed thresholds have **not** fired yet |
| 4. Anomaly | Anomaly score timeline | First sustained anomaly marked **~19 days before** the simulated failure |
| 5. Risk and RUL | Risk gauge and RUL band | Risk rising 0.12 → 0.62 as data accumulates (use a time slider to replay); RUL 12 days (7–19) |
| 6. Advisory | Advisory card | "Replace within 7 days", P2, SHAP drivers shown |
| 7. Spare check | Spares panel | 1 pump in stock, but a second aircraft's pump is also trending: **fleet-level shortfall in ~3 weeks**; lead time 45 days |
| 8. Schedule | Planning screen | Bay slot proposed, bundled with a due inspection; expected downtime 2.5 days |
| 9. Availability impact | Planner shows delta | Replace now: −2.5 aircraft-days; run-to-failure expected: −9 aircraft-days (includes supply wait) |
| 10. Scenarios | Simulator, three runs side by side | (a) baseline; (b) replace early; (c) spare unavailable: availability bands compared |
| 11. Close | Dashboard | Before/after summary: availability uplift, downtime reduction, with an explicit "on synthetic data" label |

**Why it solves the PS:** you show all four fragmented sources (sensors, logbook history, spares, agency/bay data) on one screen, producing earlier warning, an action, and a measured availability benefit.

---

# PART I: Implementation

## 11. Phased implementation roadmap

Each phase has an independent, testable output. Do not let Antigravity skip ahead.

**Phase 0: Repository and environment**
- *Objective:* an empty but runnable skeleton. *Prereqs:* GitHub repo, Python 3.11, Node 20+, Docker.
- *Create:* repo structure (§13), `README.md`, `.gitignore`, `docker-compose.yml`, `backend/` FastAPI "hello" with `/health`, `frontend/` Vite+React+TS+Tailwind page, `Makefile`, `AGENTS.md`.
- *APIs:* `GET /health`. *DB:* Postgres container only. *ML/Frontend:* none beyond a placeholder page.
- *Tests:* one backend smoke test; frontend builds.
- *Output:* `docker compose up` shows both apps. *DoD:* health check works, lint and tests pass, committed.

**Phase 1: Data model**
- *Objective:* the full relational schema as migrations. *Prereqs:* Phase 0.
- *Create:* SQLAlchemy models, Alembic migrations, `docs/data-dictionary.md`. *DB:* all tables from §15.
- *Tests:* migrations apply and roll back; constraint tests (FK, uniqueness, enum values).
- *DoD:* a fresh DB is created from migrations with no manual steps.

**Phase 2: Synthetic data generation**
- *Objective:* a reproducible simulator that fills the DB. *Prereqs:* Phase 1.
- *Create:* `data_gen/` package (config, hierarchy builder, degradation engine, sensor generator, maintenance/spares/work-order generators, noise injector), CLI `generate_data --seed`, loader, a "hero aircraft" scenario file, a data-quality report script.
- *ML work:* none yet. *Tests:* seed reproducibility; row counts; no negative stock; correlations present (degrading sensors correlate with truth health); FK integrity; missing-data rates within spec.
- *DoD:* one command produces about 40 aircraft × 3 years; the quality report passes; hero aircraft have the intended arcs.

**Phase 3: Backend foundation**
- *Objective:* read APIs, auth and ingestion. *Prereqs:* Phase 2.
- *Create:* routers (fleet, aircraft, components, sensors, maintenance, inventory, work orders), services, Pydantic schemas, JWT auth with 3 seeded roles, ingestion endpoint with validation, structured logging, pagination.
- *Tests:* API tests per endpoint, auth tests (401/403), validation tests. *DoD:* OpenAPI docs list all endpoints and tests pass.

**Phase 4: ML pipeline**
- *Objective:* train and persist the models. *Prereqs:* Phase 3 data in the DB.
- *Create:* `ml/` package: feature engineering, labels, temporal splits, anomaly module, failure model, RUL model, evaluation and SHAP, artifact saving with metadata JSON, `train` CLI, model-evaluation report (markdown plus plots).
- *Tests:* no leakage test (features use only past data), split-by-time test, metrics above baseline, artifact load test.
- *DoD:* models beat their baselines on held-out time; the evaluation report exists; artifacts versioned.

**Phase 5: Predictive maintenance engine**
- *Objective:* turn models into advisories. *Prereqs:* Phase 4.
- *Create:* health-indicator calculator, batch scoring job, advisory generator (priority rules, recommended action, template explanations), spare check, alert rules, `predictions`/`advisories`/`alerts` writes, endpoints for them.
- *Tests:* rule-table unit tests, advisory schema tests, hero-aircraft test (AC-017 produces the expected advisory trajectory). *DoD:* one scoring run produces advisories for the whole fleet.

**Phase 6: Fleet availability engine**
- *Objective:* KPIs and simulation. *Prereqs:* Phase 5.
- *Create:* KPI calculators (availability, MTBF, MTTR, backlog and so on), the Monte Carlo simulator, scenario endpoints, `scenario_runs` storage.
- *Tests:* KPIs verified against hand-computed small fixtures; simulator reproducible with a seed; monotonic sanity checks (no spares → availability not higher).
- *DoD:* the three scenario types return comparable outputs.

**Phase 7: Digital twin**
- *Objective:* twin state model and snapshots. *Prereqs:* Phase 5.
- *Create:* twin service (hierarchy, state roll-up, snapshots), twin endpoints (tree, component, history, replay by date), what-if hooks that call the simulator.
- *Tests:* roll-up logic, state transitions, replay returns the right historical state. *DoD:* the twin API answers for any aircraft and date.

**Phase 8: Frontend dashboard**
- *Objective:* all seven screens. *Prereqs:* Phases 3–7 APIs.
- *Create:* app shell/routing/auth, API client with typed models, reusable KPI/Chart/Table components, the seven screens, SVG aircraft schematic.
- *Tests:* component tests (Vitest/React Testing Library), build and lint pass. *DoD:* every screen loads real data and drill-downs work. Build screens in order: Dashboard → Aircraft/Component → Predictive → Planning → Spares → Simulator.

**Phase 9: Integration and polish**
- *Objective:* make the end-to-end flow smooth. *Prereqs:* Phase 8.
- *Create:* loading and empty and error states, consistent filters, performance fixes (indexes, caching), demo user flow wiring, "replay time" control, the "synthetic data" label.
- *DoD:* the full demo script (§10) runs without manual database edits.

**Phase 10: Testing and validation**
- *Objective:* prove it works. *Create:* integration tests, Playwright end-to-end test of the demo path, a scenario regression suite, a final model-evaluation report, a security checklist.
- *DoD:* all acceptance criteria in §17 are met and documented.

**Phase 11: Demo and deployment**
- *Objective:* one-command local demo plus a recorded backup. *Create:* seed-and-run script, Docker Compose finalisation, a demo script document, README, architecture diagrams, screenshots, and optional cloud deploy.
- *DoD:* a clean machine can run `docker compose up` and the seed script and reproduce the demo.

## 12. Antigravity execution strategy

### How to work
1. Create the GitHub repo first and put `AGENTS.md` (below) in the root. Antigravity's mechanism for persistent rules has changed over time, so check its current docs; if rules are unsupported, paste the preamble at the top of every prompt.
2. **One phase = one branch** (e.g. `phase-2-synthetic-data`). Run the phase, review the diff, run tests yourself, merge only when green, and tag the commit (`phase-2-done`).
3. Start each phase in a **fresh agent session** to keep context clean. Tell the agent to read `AGENTS.md`, `docs/`, and the repo.
4. Ask the agent to produce a short **plan before coding** and approve it. Review the plan against this document.
5. When the agent drifts, don't argue. Revert the commit and re-prompt with tighter constraints.
6. Bring me the results of each phase (test output, evaluation report, screenshots). I can review them and sharpen the next prompt.

### `AGENTS.md` / shared preamble (paste once; reference in every prompt)

```
PROJECT: Integrated Predictive Maintenance & Fleet Availability Platform (hackathon PS 26249).
All data is SYNTHETIC. Use generic aircraft names only. No real aircraft types, no weapons,
no combat or operational planning functionality. Decision-support for maintenance only.

STACK: Backend Python 3.11 + FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL.
ML: pandas, numpy, scikit-learn, lightgbm, shap, joblib. No deep learning unless told.
Frontend: React + Vite + TypeScript + Tailwind + ECharts. Docker Compose for local run.

RULES FOR EVERY TASK:
1. Inspect the existing repository before changing anything. Summarise what you find.
2. Write a short plan and wait for it to be approved before large changes.
3. Implement ONLY the current phase. Do not implement future phases or stubs for them.
4. Do not break existing functionality; run existing tests before and after.
5. Run tests, lint and build where applicable; fix failures before finishing.
6. Keep code typed, small-function, documented where non-obvious. No secrets in code.
7. When finished: report files created/changed, commands run, test results, known gaps. Then STOP.
```

### Ready-to-use prompts

Paste each into a fresh Antigravity session. Replace `[brackets]` as needed. Where a prompt says "see the schema," give Antigravity the relevant section of this plan (or save it in `docs/plan.md` and say "see `docs/plan.md` §N").

**Prompt: Phase 0 (Repository and environment)**
```
You are implementing PHASE 0 (Repository & Environment). Read AGENTS.md first.
OBJECTIVE: A runnable skeleton: FastAPI backend, React+Vite+TS+Tailwind frontend, Postgres, Docker Compose.
STATE: The repo is empty except AGENTS.md and docs/plan.md.
CREATE: the directory structure in docs/plan.md §13 (empty folders with .gitkeep where needed);
backend/ with FastAPI app, GET /health, config via environment variables, pytest setup, ruff config;
frontend/ with Vite React TS, Tailwind, a placeholder page that calls /health and displays the result;
docker-compose.yml (postgres, backend, frontend), .env.example, .gitignore, Makefile (up, down, test, lint),
README.md with run instructions.
MAY MODIFY: only the files above. 
ACCEPTANCE: `docker compose up` runs all services; the frontend shows backend health;
`make test` and `make lint` pass; frontend build passes.
Inspect first, plan, implement, run checks, report, STOP. Do not add models, ML, or other endpoints.
```

**Prompt: Phase 1 (Data model)**
```
You are implementing PHASE 1 (Data Model). Read AGENTS.md and docs/plan.md §3 and §15.
OBJECTIVE: The complete relational schema as SQLAlchemy models + Alembic migrations.
STATE: Phase 0 skeleton exists and runs.
CREATE: backend/app/models/* (one module per domain: fleet, sensors, maintenance, spares, platform),
alembic setup and an initial migration, database/ docs: docs/data-dictionary.md (every table/column/meaning),
tests for constraints.
REQUIREMENTS: primary/foreign keys, indexes (e.g. sensor_readings(component_id, flight_id), flights(aircraft_id, date),
aircraft_daily_status(aircraft_id, date), predictions(component_id, as_of_date)), CHECK constraints for enums/ranges,
no ML tables logic beyond schema. The simulation_truth table must be clearly marked as not for model training.
ACCEPTANCE: `alembic upgrade head` on an empty DB succeeds, `downgrade base` succeeds,
constraint tests pass, the data dictionary matches the models.
Inspect, plan (wait for approval), implement, test, report, STOP. No data generation, no APIs.
```

**Prompt: Phase 2 (Synthetic data)**
```
You are implementing PHASE 2 (Synthetic Data Generation). Read AGENTS.md and docs/plan.md §3.
OBJECTIVE: A reproducible simulator that populates the database with realistic synthetic fleet data.
STATE: The schema exists via Alembic migrations (Phase 1).
CREATE: data_gen/ package with: config (YAML: fleet size 40, 3 years, seed, noise rates),
hierarchy builder (7 systems, ~20 component types, generic names), flight generator,
latent-health degradation engine (gamma/Wiener process, stress-dependent drift, per-unit variation,
~15% sudden failures), sensor generator (reading = baseline(op-conditions) + signature(health) + noise),
maintenance/work-order/delay generator (spare wait + agency queue + repair time),
spares/inventory generator (reorder logic, lead times, occasional stock-outs),
noise injector (2-5% dropout, stuck values, drift, spikes, quality_flag),
aircraft_daily_status derivation, simulation_truth writes,
hero-aircraft scenario file (3-4 scripted aircraft incl. AC-017 hydraulic pump degradation with tight spares),
CLI: `python -m data_gen generate --seed 42`, and a data-quality report script (markdown output).
ACCEPTANCE: one command fills the DB; same seed gives identical data; quality report shows
row counts, missing rates, failure counts per component type, correlation check between sensors and true health;
tests for reproducibility, FK integrity, non-negative stock.
Do NOT train models or build APIs. Inspect, plan, implement, run, report, STOP.
```

**Prompt: Phase 3 (Backend foundation)**
```
You are implementing PHASE 3 (Backend Foundation). Read AGENTS.md and docs/plan.md §14, §15.
OBJECTIVE: REST APIs for reading the integrated data, JWT auth with roles, and a validated ingestion endpoint.
STATE: Schema (Phase 1) and populated DB (Phase 2) exist.
CREATE: routers/services/schemas for fleet, aircraft, components, sensors, maintenance, work orders,
inventory, agencies; JWT login with roles (commander, planner, technician) and seeded demo users;
role checks (technician read-only); POST /ingest/sensor-readings with Pydantic validation and per-row error reporting;
pagination and filtering; structured JSON logging; consistent error format.
Endpoints per docs/plan.md §14 for these domains only. No prediction/scenario/twin endpoints yet.
ACCEPTANCE: OpenAPI docs complete; API tests per endpoint; auth tests (401, 403); ingestion validation tests;
all tests and lint pass.
Inspect, plan, implement, test, report, STOP.
```

**Prompt: Phase 4 (ML pipeline)**
```
You are implementing PHASE 4 (ML Pipeline). Read AGENTS.md and docs/plan.md §4, §16.
OBJECTIVE: Train, evaluate and persist: (A) anomaly detection, (B) 14-day failure-risk model, (C) RUL model.
STATE: DB is populated with synthetic data; simulation_truth exists but MUST NOT be used as a feature.
CREATE: ml/ package: data loading from DB, feature engineering (rolling mean/slope/std over 5 and 20 flights,
operating-condition normalisation, hours/cycles since maintenance, fault counts), label creation, 
time-based AND grouped-by-aircraft train/val/test splits,
anomaly module (condition-regression residuals + Isolation Forest), failure model (logistic regression baseline + LightGBM, calibrated),
RUL model (linear health-trend baseline + LightGBM quantile 10/50/90, target clipped at 60 days),
evaluation (PR-AUC, recall@precision, Brier, MAE, interval coverage, detection lead time), SHAP outputs,
artifact saving to models/<name>/<version>/ with metadata.json (features, metrics, data hash, date),
CLI `python -m ml.train --all`, and a generated reports/model_evaluation.md with plots.
ACCEPTANCE: models beat baselines on the held-out test period; leakage test proves features only use past data;
artifacts reload and predict; the report exists.
Do NOT build advisory logic or APIs. Inspect, plan, implement, run, report honestly (including weaknesses), STOP.
```

**Prompt: Phase 5 (Predictive maintenance engine)**
```
You are implementing PHASE 5 (Predictive Maintenance Engine). Read AGENTS.md and docs/plan.md §5.
OBJECTIVE: Convert model outputs into Maintenance Advisories and alerts.
STATE: Trained model artifacts in models/; DB with data; backend APIs from Phase 3.
CREATE: backend/app/engine/: health_indicator.py, scoring_job.py (batch inference for a given as_of_date,
writes anomaly_scores/predictions), advisory.py (priority rules with configurable weights in YAML,
recommended-action rules, template-based plain-language explanation, SHAP top factors, confidence note),
spares_check.py (part requirement, stock, lead time vs RUL), alert_rules.py (risk threshold, shortfall vs RUL,
overdue inspections, backlog), advisory status workflow (proposed/accepted/scheduled/completed/dismissed+reason),
endpoints: GET /predictions, GET /advisories, PATCH /advisories/{id}, GET /alerts, POST /engine/run.
ACCEPTANCE: one run produces advisories for the full fleet; the AC-017 hero advisory shows the expected progression
when replayed across dates; rule unit tests; API tests.
Do NOT implement availability simulation or twin. Inspect, plan, implement, test, report, STOP.
```

**Prompt: Phase 6 (Availability engine)**
```
You are implementing PHASE 6 (Fleet Availability Engine). Read AGENTS.md and docs/plan.md §7.
OBJECTIVE: KPI calculations and a Monte Carlo scenario simulator.
STATE: Phases 0-5 complete.
CREATE: backend/app/availability/: kpis.py (availability, serviceability, downtime by cause, MTBF, MTTR,
turnaround, failure rate, backlog, readiness proxy, spare fill rate), simulator.py (discrete-event Monte Carlo:
aircraft states, bays, work orders, spare stock/receipts, failures sampled from risk/RUL; N runs; seeded; P10/P50/P90),
scenarios.py (schedule-maintenance, spare-unavailable, early-vs-run-to-failure, extra-capacity),
endpoints: GET /kpis/*, POST /scenarios/run, GET /scenarios/{id}, GET /scenarios (compare).
ACCEPTANCE: KPI functions match hand-computed fixtures; simulations reproducible with a seed;
sanity tests (removing spares never raises availability; adding capacity never lowers it);
run time under ~10s for a 30-day, 300-run scenario.
Inspect, plan, implement, test, report, STOP.
```

**Prompt: Phase 7 (Digital twin)**
```
You are implementing PHASE 7 (Digital Twin). Read AGENTS.md and docs/plan.md §6.
OBJECTIVE: A software-level digital twin service: hierarchy, health-state roll-up, snapshots, replay.
STATE: Phases 0-6 complete.
CREATE: backend/app/twin/: state model (Healthy/Watch/Degraded/Critical/Failed/Under maintenance, configurable thresholds),
roll-up (component → system → aircraft, criticality-weighted, worst-component driver reported),
snapshot writer called after each engine run (twin_snapshots), 
endpoints: GET /twin/fleet, /twin/aircraft/{id}, /twin/component/{id}, /twin/aircraft/{id}?as_of=DATE (replay),
POST /twin/whatif (delegates to scenario engine).
ACCEPTANCE: roll-up tests; state-transition tests; replay returns the correct historical state for AC-017.
No UI work. Inspect, plan, implement, test, report, STOP.
```

**Prompt: Phase 8 (Frontend dashboard)**
```
You are implementing PHASE 8 (Frontend Dashboard). Read AGENTS.md and docs/plan.md §9.
OBJECTIVE: The seven screens, driven by the real backend APIs.
STATE: Backend APIs for all domains exist (Phases 3-7).
CREATE: app shell, routing, login, role-aware nav, typed API client, TanStack Query hooks,
shared components (KpiCard, StatusBadge, DataTable, TimeSeriesChart with anomaly shading, Heatgrid, AdvisoryCard),
and screens in this order, checking in after each: Fleet Dashboard; Aircraft Detail (+ twin tab, SVG schematic);
Component Health; Predictive Maintenance queue; Maintenance Planning & Work Orders; Spares; Scenario Simulator.
Use ECharts, Tailwind. Show a persistent "Synthetic data" label. Loading, empty and error states on all data views.
ACCEPTANCE: build, lint and component tests pass; each screen shows real data; the drill-downs in docs/plan.md §9 work.
Do NOT change backend contracts without reporting it. Inspect, plan (wait for approval), implement, report, STOP.
```

**Prompt: Phase 9 (Integration and polish)**
```
You are implementing PHASE 9 (Integration & Polish). Read AGENTS.md and docs/plan.md §10.
OBJECTIVE: Make the full demo script run end to end without manual DB edits.
STATE: Phases 0-8 complete.
DO: walk the 11-step demo in docs/plan.md §10, list every gap or bug, fix them; add a time-replay control that
drives the as-of date across screens; add DB indexes/caching where pages are slow (>1s); polish consistency (filters, units, 
colours, empty states); ensure advisory Accept/Schedule actions update planning and availability views.
ACCEPTANCE: each demo step reachable by clicks only; no console errors; pages load < 2s on the seeded data.
Report the gap list and fixes. STOP.
```

**Prompt: Phase 10 (Testing and validation)**
```
You are implementing PHASE 10 (Testing & Validation). Read AGENTS.md and docs/plan.md §17.
OBJECTIVE: Prove the system works and document it.
CREATE: missing unit/API/DB tests to reach sensible coverage of services and engine rules; integration tests
(data → scoring → advisory → scenario); Playwright E2E for the demo path; scenario regression tests with fixed seeds;
data validation checks; final reports/model_evaluation.md refresh; docs/security-checklist.md
(auth, input validation, secrets, role access); GitHub Actions workflow (lint, test, build).
ACCEPTANCE: all criteria in docs/plan.md §17 are met or explicitly listed as gaps. 
Do not add features. Report results. STOP.
```

**Prompt: Phase 11 (Demo and deployment)**
```
You are implementing PHASE 11 (Demo & Deployment). Read AGENTS.md.
OBJECTIVE: One-command reproducible local demo and documentation.
CREATE: `make demo` (compose up, migrate, generate data seed 42, train models, run engine, start app);
docs/demo-script.md (the 11 steps with exact clicks and expected values); README with architecture diagram (mermaid),
setup, screenshots placeholders; docs/limitations.md (synthetic data, model scope, what real data would change).
Do not change functionality. Verify from a clean clone. Report. STOP.
```

## 13. Repository structure

```
/
├── AGENTS.md                  # Rules every Antigravity session follows
├── README.md
├── docker-compose.yml  .env.example  Makefile
├── backend/
│   ├── app/
│   │   ├── main.py  config.py
│   │   ├── api/               # routers (HTTP layer only)
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── models/            # SQLAlchemy ORM
│   │   ├── services/          # business logic (data access, ingestion)
│   │   ├── engine/            # scoring, advisories, alerts
│   │   ├── availability/      # KPIs + Monte Carlo simulator
│   │   ├── twin/              # twin state, roll-up, snapshots
│   │   └── core/              # auth, logging, errors
│   ├── alembic/  tests/  pyproject.toml
├── ml/                        # training code, separate from serving
│   ├── features/ models/ evaluation/ cli.py  tests/
├── data_gen/                  # synthetic data simulator
├── models/                    # versioned artifacts (git-ignored, or git-lfs)
├── frontend/
│   ├── src/ (pages/ components/ api/ hooks/ types/)  tests/  
├── data/                      # generated datasets (git-ignored) + sample config
├── reports/                   # model evaluation, data-quality reports
├── scripts/                   # seed, demo, utilities
├── docs/                      # plan.md, data-dictionary, demo-script, limitations, security
├── e2e/                       # Playwright tests
└── .github/workflows/         # CI
```
**Key responsibilities:** `backend` serves and orchestrates; `ml` trains (offline); `data_gen` creates synthetic data; `models` holds artifacts the backend loads; `docs` keeps the plan and the agent's reference material. Keeping `ml` and `data_gen` separate from `backend` keeps each phase's work isolated for the coding agent.

## 14. API design

All endpoints under `/api/v1`. Auth: JWT bearer. Roles: **C**ommander, **P**lanner, **T**echnician. "Read" = all roles unless noted.

| Method | Endpoint | Purpose | Request / key params | Response (abridged) | Auth | Consumer |
|---|---|---|---|---|---|---|
| POST | `/auth/login` | Get token | `{username, password}` | `{access_token, role}` | none | Login |
| GET | `/fleet/summary` | Dashboard KPIs | `as_of` | `{availability_pct, by_state, open_p1, open_p2, backlog, parts_at_risk}` | Read | Fleet Dashboard |
| GET | `/fleet/availability/trend` | History and forecast | `from, to, horizon` | `{points:[{date, avail, p10, p90}]}` | Read | Dashboard |
| GET | `/aircraft` | List aircraft | `state, base, page` | list with state, HI, top risk | Read | Dashboard, tables |
| GET | `/aircraft/{id}` | Detail | none | aircraft, systems, components summary | Read | Aircraft Detail |
| GET | `/components/{id}/sensors` | Sensor trends | `parameter, from, to` | series + anomaly flags | Read | Component Health |
| GET | `/components/{id}/health` | HI/risk/RUL history | `from, to` | `{hi:[…], risk:[…], rul:[…]}` | Read | Component Health |
| GET | `/predictions` | Latest predictions | `aircraft_id, system, min_risk` | list | Read | Predictive |
| GET | `/advisories` | Risk queue | `priority, status, spare_status` | list of advisory objects (§5) | Read | Predictive |
| PATCH | `/advisories/{id}` | Accept/dismiss/schedule | `{status, reason?}` | updated advisory | P, C | Component Health |
| GET | `/work-orders` | Work orders | `status, agency, aircraft` | list | Read | Planning |
| POST | `/work-orders` | Create from advisory | `{advisory_id, agency_id, planned_start}` | work order + impact preview | P, C | Planning |
| GET | `/maintenance/schedule` | Bay timeline | `from, to` | slots by bay/aircraft | Read | Planning |
| GET | `/inventory` | Stock status | `status, part` | parts with demand forecast | Read | Spares |
| GET | `/inventory/{part}/forecast` | Demand forecast | `horizon` | `{expected, p10, p90, shortfall_prob}` | Read | Spares |
| GET | `/alerts` | Active alerts | `severity` | list | Read | Banner |
| GET | `/kpis` | KPI set | `from, to, group_by` | MTBF/MTTR/turnaround etc. | Read | Analytics |
| POST | `/scenarios/run` | Run what-if | `{type, params, horizon, runs}` | `{id, baseline, scenario, delta}` | P, C | Simulator |
| GET | `/scenarios` | Saved scenarios | none | list | P, C | Simulator |
| GET | `/twin/aircraft/{id}` | Twin state | `as_of?` | tree with states | Read | Aircraft Detail |
| POST | `/engine/run` | Trigger scoring | `{as_of}` | run summary | C | Admin/demo |
| POST | `/ingest/sensor-readings` | Ingest | batch of readings | accepted/rejected counts | P, C | Integration layer |
| GET | `/health` | Liveness | none | `{status}` | none | Ops |

**Example payloads**

`POST /scenarios/run`
```json
{ "type": "spare_unavailable", "params": {"part_number": "HYD-114", "lead_time_days": 60},
  "horizon_days": 30, "runs": 300, "seed": 7 }
```
Response:
```json
{ "id": "sc_0042",
  "baseline": {"availability_p50": 0.81, "p10": 0.77, "p90": 0.84, "aircraft_days_lost": 48.2},
  "scenario": {"availability_p50": 0.76, "p10": 0.70, "p90": 0.81, "aircraft_days_lost": 71.5},
  "delta": {"availability_pct_points": -5.0, "aircraft_days_lost": 23.3},
  "by_cause": {"supply_wait": 21.0, "scheduled": 0.0, "unscheduled": 2.3} }
```

`PATCH /advisories/{id}` request: `{"status": "scheduled", "reason": null}`

## 15. Database design

**Conceptual ER:**
```
aircraft 1──* components *──1 component_types *──1 systems
aircraft 1──* flights 1──* sensor_readings *──1 components
components 1──* fault_events
aircraft/components 1──* maintenance_events *──1 work_orders *──1 agencies
component_types *──1 spare_parts 1──* inventory 1──* inventory_transactions
components 1──* anomaly_scores | predictions | twin_snapshots | advisories
advisories 0..1──* work_orders
aircraft 1──* aircraft_daily_status
scenario_runs (standalone, references params)   alerts (references aircraft/component/advisory)
users (id, username, password_hash, role)       simulation_truth (components, hidden from ML)
```

**Tables:** as listed in §3, plus:
- `anomaly_scores(component_id, flight_id, score, top_parameters JSON)`
- `predictions(prediction_id, component_id, as_of_date, risk_14d, risk_30d, rul_p10, rul_p50, rul_p90, model_version)`
- `advisories(advisory_id, component_id, as_of_date, priority, action, status, dismiss_reason, explanation JSON, spare_status, expected_downtime_days, created_at)`
- `twin_snapshots(snapshot_id, node_type, node_id, as_of_date, health_index, state, risk, rul_p50)`
- `alerts(alert_id, type, severity, aircraft_id, component_id, message, created_at, acknowledged)`
- `scenario_runs(id, type, params JSON, results JSON, seed, created_by, created_at)`
- `users`, `model_runs(model_name, version, metrics JSON, trained_at)`

**Key indexes:** `sensor_readings(component_id, flight_id)`, `flights(aircraft_id, date)`, `predictions(component_id, as_of_date DESC)`, `aircraft_daily_status(aircraft_id, date)`, `work_orders(status, agency_id)`, `inventory(part_number, location_id)`, `twin_snapshots(node_id, as_of_date)`.

**Key constraints:** FK integrity everywhere; `UNIQUE(component_id, as_of_date, model_version)` on predictions; CHECK on enums (state, priority, status), `on_hand ≥ 0`, `end ≥ start`, `severity` range; a component belongs to one aircraft at a time.

## 16. ML development pipeline

```
Ingestion → Validation → Cleaning → Feature engineering → Split → Training → Tuning
  → Evaluation → Explainability → Persistence → Inference → Monitoring
```

| Stage | What happens |
|---|---|
| Ingestion | Read from Postgres into pandas. Never read `simulation_truth` for features |
| Validation | Schema checks, range checks, missing-rate report (e.g. Pandera or custom checks) |
| Cleaning | Handle dropouts (forward-fill limited window), clip spikes, flag stuck sensors; keep `quality_flag` as a feature |
| Features | Strictly past-only windows. A unit test asserts that shifting future data doesn't change features |
| Split | Time-based (e.g. train 2023–2024, validate H1 2025, test H2 2025) and component-grouped so a unit's rows never span splits |
| Training | Baseline first, then the main model |
| Tuning | Small randomised or Optuna search with time-series cross-validation. Keep it modest |
| Evaluation | Metrics from §4, plus the plots in `reports/` |
| Explainability | SHAP for tree models; anomaly residuals per parameter |
| Persistence | `models/<name>/<version>/model.joblib` + `metadata.json` (features, metrics, data hash, date, library versions) |
| Inference | Backend loads the latest version at startup; `scoring_job` builds features as of a date and writes `predictions` |
| Monitoring | Log score distributions per run, compare to the training distribution, compare predicted versus realised failures, and surface a drift flag in Analytics |

## 17. Testing and validation

| Type | What | Acceptance criterion (initial targets, tune after seeing results) |
|---|---|---|
| Unit | Rules, KPIs, roll-up, feature functions | 100% of rules and KPI functions covered |
| API | Each endpoint, auth, validation | All endpoints tested; 401/403 verified |
| Database | Migrations, constraints | Up/down migrations clean |
| Data validation | Synthetic data quality | Reproducible by seed; missing rate within spec; sensor-health correlation present |
| ML evaluation | Held-out time period | Failure model PR-AUC clearly above baseline; RUL MAE better than the linear baseline; RUL 10–90 interval coverage ≈ 75–85%; median detection lead time of several days with a low false-alarm rate |
| Integration | data → score → advisory → scenario | Hero aircraft produces the expected advisory trajectory |
| Frontend | Component tests, build, lint | Pass |
| E2E | Playwright runs the §10 path | Completes with no manual steps |
| Scenario tests | Fixed-seed simulation regression | Monotonic sanity checks hold; results reproducible |

I deliberately don't commit to specific numeric thresholds for model metrics. Set them after you see the first honest baseline results, then state them in the pitch. **Always report that results are on synthetic data.**

## 18. Hackathon / evaluation readiness

**[Inference]** The PS gives no evaluation rubric. These are reasonable expectations based on the PS wording and typical hackathon judging, not facts.

| Likely focus | How you address it |
|---|---|
| Integration of fragmented data (PS wording) | Data layer unifying four sources; the data-quality report; a one-screen view |
| AI/ML credibility | Baselines versus models, temporal splits, honest metrics, calibration, lead time |
| Predictive, not just reactive | Anomaly → risk → RUL → action chain with lead time gained |
| Digital twin and IoT (named in the PS) | Twin hierarchy with replay; ingestion API standing in for a health-monitoring feed |
| Availability outcome | Availability engine and scenario comparisons |
| Explainability | SHAP, parameter contributions, rule-based priority |
| Real-world applicability | Limitations doc; a plan for swapping the synthetic data for real exports; a human-in-the-loop workflow |
| UI/UX | Decision-maker-oriented screens, drill-downs |
| Scalability | Architecture notes: Timescale/stream ingestion/model server as scale paths |
| Security | Role-based access, JWT, validation; note that a real deployment would be on an air-gapped or accredited network |

**Final presentation should include:** the problem in one slide (the three causes of downtime); the architecture diagram; the data strategy and why synthetic; one model-evaluation slide with honest numbers; the live or recorded demo; the availability uplift in the scenario comparison; limitations and what real data would change; and the roadmap.

**What not to claim:** accuracy on real aircraft, readiness for operational use, or compliance with any military airworthiness standard.

---

# PART J

## 19. Final master implementation plan

1. **Architecture:** §8 diagram (Python FastAPI + PostgreSQL + batch ML + React).
2. **Tech stack:** React/Vite/TS/Tailwind/ECharts; FastAPI/SQLAlchemy/Alembic; PostgreSQL (no Timescale); pandas/scikit-learn/LightGBM/SHAP; Docker Compose; GitHub Actions.
3. **Modules:** §2 (9 essential, analytics optional, LLM assistant stretch).
4. **Data architecture:** §3: 40 generic aircraft, 3 years, latent-health simulation, hero aircraft, hidden truth table.
5. **ML architecture:** §4 and §16: anomaly (residual + Isolation Forest), failure risk (LightGBM), RUL (quantile LightGBM), rule-based priority, simulation-based availability forecasting.
6. **Database schema:** §3 and §15.
7. **API architecture:** §14.
8. **Frontend structure:** §9 (7 screens) and §13 (`frontend/src`).
9. **Repository structure:** §13.
10. **Implementation order:** Phases 0 → 11 (§11), one branch each, merged only when green.
11. **Antigravity prompts:** §12.
12. **Testing strategy:** §17.
13. **Demo flow:** §10.
14. **Deployment:** local Docker Compose (`make demo`) is the primary target; optional cloud deploy is a bonus; keep a recorded backup of the demo.
15. **Definition of Done:**
- `make demo` on a clean clone reproduces the full demo with no manual edits;
- all tests, lint and build pass in CI;
- models beat baselines on the held-out period, with an honest evaluation report;
- the §10 demo path works click by click;
- three scenario comparisons run and show availability differences;
- docs include the architecture, data dictionary, limitations and demo script;
- the UI and docs clearly state that all data is synthetic.

### Assumptions to keep visible
- The generic fleet, sensor-summary granularity, 40 aircraft and 3 years are **my design choices**, not from the PS.
- The availability definition is mine. State it explicitly.
- Real data would change feature distributions, failure modes, ID mapping and data quality. Say so in the pitch.

---

# WHAT I SHOULD DO NEXT

1. **Create the GitHub repo** and save this document as `docs/plan.md`. The Antigravity prompts refer to its section numbers.
2. **Create `AGENTS.md`** with the preamble from §12.
3. **Check your tools:** Python 3.11, Node 20+, Docker Desktop, Git. Confirm Antigravity can open the repo and run terminal commands.
4. **Decide your team's split**, if you have teammates: someone who reviews the data/ML phases, and someone who reviews the frontend phases. A phase is only done when a human has read the diff.
5. **Skim these sections until they feel natural**, since you will be defending them: §1.8 (availability definition), §3 (latent-health simulation), §5 (Maintenance Advisory).
6. **Decide on two open questions** and tell me: how many people are on the team, and how many days you have before the deadline. That lets me trim the stretch scope and decide whether Phase 9 polish or the optional modules fit.
7. **Run Phase 0 only,** with the prompt in §12. Bring me the result, including anything surprising, before you start Phase 1.

This is a lot to read at once. If you'd like it as a single downloadable Markdown or Word file for the repo, say so and I'll create it.
