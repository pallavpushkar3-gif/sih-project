# PS 26249 — technology selection study

Date: 3 October 2026. Decision: React/TypeScript frontend, Python/FastAPI application backend and scientific workers, PostgreSQL, Celery/RabbitMQ, PyTorch/XGBoost, OR-Tools CP-SAT, and SimPy.

## 1. Decision and scope

The earlier Rust/Axum recommendation was too confident. Rust is a strong operational backend option, but we have not established that our workload needs its throughput or latency advantages. Selecting it because it is a high-performance language does not establish that a mixed Rust/Python architecture is the best product architecture.

After comparing the requirements and official documentation, the recommended application is a modular Python backend with separately running scientific workers and a TypeScript browser interface. This is a technical-fit decision, not a concession to development difficulty, team familiarity, or the hackathon deadline. Sharing scientific transformations and domain logic, controlling process boundaries, and avoiding duplicate implementations are reliability advantages even with unlimited engineering time.

This is a documentation-backed architecture study. It is not an executed performance benchmark, security audit, library compatibility test or exhaustive survey of every technology. Capability statements are linked to primary documentation. Selection judgments are our inferences from those capabilities and the intended product. The study does not claim that documentation proves universal superiority.

## 2. Requirements that drive the choice

| Requirement | Concrete consequence for the architecture |
|---|---|
| Sensor histories and replay | Batch ingestion, explicit units, data provenance and repeatable historical queries. Initially public engine datasets, not a measured high-frequency aircraft telemetry deployment. |
| Predictive-maintenance research | Reproduce classical and neural baselines, add calibration, and retain exactly the preprocessing used in training. |
| Maintenance decisions | Combine predictions with mandatory jobs, part availability, technician capacity and workshop slots. |
| Long calculations | Optimizations and repeated simulations must not block browser requests or disappear when an API process restarts. |
| Multi-user approval | Prevent double reservation of stock, detect edits to stale plans, and preserve approval history. |
| Rich browser interface | Linked charts, tables, filters, evidence cards, task timelines and progress updates. |
| Reproducibility | Dataset split, transformation version, model artifact, solver settings, simulation seed and source revision must accompany results. |
| Deployment independence | A deployment should be able to run with local datasets/models without depending on external inference APIs. This is not a claim of certified air-gapped operation. |
| Five-person collaboration | One domain vocabulary, shared contracts and explicit ownership across modules. AI-generated code still needs validation and contract checks. |

No fleet size, ingestion rate, concurrency target, retention horizon, hardware budget, or real-time deadline has been established. Inventing those numbers would produce a misleading performance justification. Performance tests below define how to resolve those unknowns.

## 3. Final stack and responsibilities

| Layer | Decision | Responsibility | Confidence in requirement fit |
|---|---|---|---|
| Browser application | React + TypeScript + Vite | Dashboard, evidence cards, plan editor and scenario comparison. | Moderate: Vue and Svelte also fit well. |
| UI and server state | Radix UI, Tailwind CSS, TanStack Query | Accessible interaction primitives, consistent design tokens, fetched-data cache and mutations. | Moderate: implementation quality matters more than brand. |
| Analytical charts | Apache ECharts | Sensor traces, interval bands, heatmaps and fleet comparisons; custom read-only timeline where appropriate. | Moderate: validate the actual chart workloads. |
| Application API | Python + FastAPI + Pydantic + Uvicorn | Requests, validated contracts, workflow rules, permissions, jobs and result retrieval. | Strong for a Python scientific application. |
| Persistence | PostgreSQL + SQLAlchemy + Alembic | Relational records, transactional reservations, plans, job state and migrations. | Strong for shared operational records. |
| Long-running work | Celery workers + RabbitMQ | Durable dispatch of prediction batches, planning and simulation jobs. | Strong for restartable background calculations; reliability requires configuration. |
| Neural research | PyTorch | Sequence models, custom losses and uncertainty experiments. | Moderate: original paper code can justify another framework. |
| Classical baselines | scikit-learn + XGBoost | Engineered-feature regression, baseline comparison and quantile candidates where supported by the chosen model. | Strong as comparators; final model remains empirical. |
| Scheduling | OR-Tools CP-SAT | Discrete task placement, resource capacity, precedence, deadlines and commitments. | Strong for the proposed discrete scheduling formulation. |
| Fleet simulation | SimPy + NumPy | Event-driven downtime, resource queues and repeatable stochastic scenarios. | Strong for logistics events, not flight physics. |
| Research traceability | MLflow + versioned artifact manifests | Experiment parameters, metrics and model artifacts. | Strong for organizing experiments; does not itself guarantee reproducibility. |
| Packaging | Docker Compose, dependency lockfiles | Repeatable service topology and environments. | Strong for a single-host demonstrator; not a high-availability platform. |

Use maintained stable versions verified together at implementation time; do not blindly select the newest version or development documentation version. Keep artifacts behind a storage interface, initially a mounted persistent directory with hashes and manifests. Move to object storage when multi-host access or retention requirements justify it.

## 4. Frontend comparison

React's component/state model maps naturally to a page where selecting an engine updates charts, details, predictions and planning controls together. TypeScript helps make states and contracts explicit. Vite provides a build tool appropriate for a client application. [React state](https://react.dev/learn/managing-state), [TypeScript support](https://react.dev/learn/typescript), [Vite](https://vite.dev/guide/).

| Alternative | Actual strength | Why it is not selected here | When we should reconsider |
|---|---|---|---|
| React + TypeScript | Explicit component composition and state modelling. | Selected. Needs disciplined state ownership and careful rendering. | Change if prototype measurements or an existing component system favour another framework. |
| Svelte | Compiler-based components and reactive state. | Fully credible. We have no evidence React renders this dashboard faster. React is a composition preference, not a performance victory. | A measured smaller/faster interface or a better matching existing UI system. [Svelte](https://svelte.dev/docs/svelte/overview). |
| Vue | Reactive components and a progressive application model. | Also fully credible. No missing fundamental capability prevents using it. | Strong existing Vue components or superior prototype results. [Vue](https://vuejs.org/guide/introduction). |
| Next.js | React framework with server/client rendering facilities. | Our authenticated, interactive workspace already has an API and does not currently require a server-rendered frontend. Its additional runtime has no established architectural role here. | Public searchable pages, server-rendered reports or a justified frontend server layer. [Next.js](https://nextjs.org/docs/app/getting-started/server-and-client-components). |
| Raw JavaScript | Complete control over DOM and rendering. | Possible, but state coordination, lifecycles and error/loading states would be custom infrastructure rather than an explicit shared component model. | A very small interface or a narrowly isolated visualization widget. |
| Rust/Wasm UI | Rust types and compiled browser computations. | It changes the browser integration model without improving our server-side scientific results. We have no demonstrated browser numerical bottleneck. | A specific CPU-heavy browser computation with measured benefit. [Wasm integration](https://developer.mozilla.org/en-US/docs/WebAssembly/Guides/Using_the_JavaScript_API). |

TanStack Query should own server-derived state; local component state should own unsaved interactions. Do not duplicate a fetched plan in several independent state stores. Its documented caching and mutation facilities support this distinction. Radix supplies focus and keyboard behaviour foundations, but labels, contrast and application accessibility still need our checks. [TanStack Query](https://tanstack.com/query/latest/docs/framework/react/overview), [Radix accessibility](https://www.radix-ui.com/primitives/docs/overview/accessibility).

Tailwind is a styling choice. It does not establish product usability or performance superiority over CSS Modules. Keep design tokens consistent regardless of styling syntax.

## 5. Charts and graphics

Select ECharts for the dashboard's ordinary analytical charts because its chart abstraction and Canvas/SVG options suit traces, comparisons and dense views. This is a fit inference from documented capabilities, not a universal speed claim. [ECharts renderers](https://echarts.apache.org/handbook/en/best-practices/canvas-vs-svg/).

| Alternative | Decision rationale |
|---|---|
| D3 | Excellent for custom scales, brushing, geometry and bespoke interactions. It is a lower-level visualization toolbox. Use selected modules for a custom planning editor if necessary, rather than rebuilding every chart. [D3](https://d3js.org/what-is-d3). |
| Plotly | Strong scientific visualization alternative. Choose it if research-oriented plots or its available chart types dominate the interface; we have not benchmarked it against ECharts. [Plotly](https://plotly.com/javascript/). |
| Custom Canvas/WebGL | Appropriate for a demonstrated rendering bottleneck or special interaction; requires our own hit testing, accessibility and chart semantics. |
| 3D aircraft graphics | An optional component-navigation aid. It supplies no predictive validation and should not determine the architecture. |

ECharts is not assumed to be a complete editable Gantt scheduler. The plan editor may need a dedicated React timeline using SVG or a scheduling component chosen after an interaction prototype. Never show raw millions of sensor points by default: retrieve a window and downsample while preserving important extrema.

## 6. Backend: why Python/FastAPI replaces Rust/Axum

FastAPI documents validated Python request models and OpenAPI contracts; its concurrency guidance distinguishes waiting on I/O from parallel computation. The application can import the same domain and scientific packages as its workers. [FastAPI features](https://fastapi.tiangolo.com/features/), [concurrency](https://fastapi.tiangolo.com/async/).

Example: a temperature-series transformation used during training must be identical during prediction. Sharing one tested implementation reduces training/serving differences. The planner can consume the same typed life estimates as the simulator. Rust plus Python can also do this correctly through a contract, but that boundary must be managed without an established benefit for this workload.

| Candidate | Credible advantage | Why it is not the default |
|---|---|---|
| Python/FastAPI | Direct scientific integration, validated API models, shared application/worker packages. | Selected. API responsiveness depends on keeping compute outside request handlers. |
| Rust/Axum | Ownership/type checking prevents many memory/concurrency errors; Axum integrates with Tokio/Tower. | Those guarantees do not validate maintenance logic, database transactions or model assumptions. Additional language/service contracts have not yet earned their place. [Rust concurrency](https://doc.rust-lang.org/book/ch16-00-concurrency.html), [Axum](https://docs.rs/axum/latest/axum/). |
| Go | Goroutines and a runtime built for concurrent services. | Strong API/ingestion option, but scientific calculations still naturally live in another process. No workload currently requires that split. [Go](https://go.dev/doc/effective_go#concurrency). |
| Node.js/TypeScript | Shared frontend/backend language and asynchronous I/O. | Scientific integration still crosses a boundary. CPU-heavy work must not block the event loop. Node is not incapable of parallel work. [Node guidance](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop). |
| Django | Integrated ORM and administrative application facilities. | Prefer it if back-office record administration dominates. Our chosen focus is a contract-oriented scientific API and worker system. [Django overview](https://docs.djangoproject.com/en/5.2/intro/overview/). |
| Flask | Flexible Python application foundation. | Credible, but FastAPI directly supplies the typed API contract model we want. Flask can support async views; its deployment model still needs consideration. [Flask async](https://flask.palletsprojects.com/en/stable/async-await/). |

Rust remains an extension candidate for a measured parsing, ingestion or numerical hotspot. Isolate that component through a native extension or service only after profiling. We do not promise Python satisfies an unspecified hard real-time deadline.

## 7. Database: why PostgreSQL

Our records are relational: a component belongs to an aircraft, a job requires parts, an approved plan reserves resources, and a prediction references a model and input snapshot. PostgreSQL offers constraints, transaction isolation and JSONB for flexible metadata. Those capabilities align with shared reservations and traceability. They require correct schema design and transaction handling. [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html), [isolation](https://www.postgresql.org/docs/current/transaction-iso.html), [JSON](https://www.postgresql.org/docs/current/datatype-json.html).

| Candidate | Why it is not our primary database |
|---|---|
| MongoDB | Supports multi-document transactions, so claiming it cannot provide consistency would be wrong. Its document model offers less direct alignment with our many shared relationships and cross-record reservations. [MongoDB transactions](https://www.mongodb.com/docs/manual/core/transactions/). |
| MySQL/InnoDB | A valid relational alternative with foreign keys. PostgreSQL's constraint/metadata combination is our preference, not a claim that MySQL cannot implement the product. [MySQL foreign keys](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html). |
| SQLite | Excellent embedded/offline option. A shared service with concurrent writers is better matched to a client/server database. [SQLite uses](https://www.sqlite.org/whentouse.html). |
| DuckDB | Strong analytical database for local research and large scans. It can complement operational storage; it is not our chosen multi-process shared-record service. [DuckDB](https://duckdb.org/docs/current/connect/concurrency). |
| Separate time-series database | Potentially useful if measured ingestion/retention demands require it. Initially it introduces another store to reconcile with parts, jobs and approvals. |

SQLAlchemy manages persistence units of work; Alembic manages schema history. Give each request/task its own session. Models do not make race conditions disappear. Use transactions and explicit reservation checks; optimistic plan versions detect stale edits. [Sessions](https://docs.sqlalchemy.org/en/20/orm/session_basics.html), [Alembic](https://alembic.sqlalchemy.org/en/latest/).

## 8. Prediction framework: why PyTorch, and why not one predetermined model

PyTorch is the default neural experimentation framework; scikit-learn/XGBoost supply classical comparators. We need controlled preprocessing, custom asymmetric losses, uncertainty estimates and ablations. That does not establish that a neural model wins. The final model is selected on unseen-engine error, interval coverage/width, robustness and serving behaviour. [PyTorch](https://docs.pytorch.org/docs/), [XGBoost](https://xgboost.readthedocs.io/en/stable/python/python_intro.html).

| Alternative | Decision |
|---|---|
| TensorFlow/Keras | Equally capable of custom training. Use it when the paper's original implementation or an existing validated model makes it a stronger reproduction choice. PyTorch is not inherently more accurate. [Custom training](https://www.tensorflow.org/guide/keras/writing_a_training_loop_from_scratch). |
| JAX | Strong transformation/JIT-based numerical system; reconsider for a workload demonstrably benefiting from that execution model. No such need is established. [JAX JIT](https://docs.jax.dev/en/latest/jit-compilation.html). |
| Rust/Burn | A real Rust ML option. Reimplementing the scientific workflow there has no demonstrated advantage over retaining our chosen Python libraries and paper implementations. [Burn](https://burn.dev/books/burn/). |
| ONNX/native inference | An export/deployment option after a model is chosen. Verify operators, transformations and numerical equivalence; it is not a replacement for training and evaluation. |

MLflow records runs and artifacts; also preserve input hashes, engine splits and source revisions. PyTorch documentation warns that reproducibility is not guaranteed across all releases/platforms; log environments and test tolerances rather than promising universal identical outputs. [MLflow](https://mlflow.org/docs/latest/ml/tracking/), [PyTorch reproducibility](https://docs.pytorch.org/docs/main/notes/randomness.html).

## 9. Scheduling: why CP-SAT, and its boundary

Our proposed planner assigns discrete maintenance tasks to resources over a finite horizon. Interval variables, precedence and no-overlap constraints match this structure. OR-Tools documents a job-shop formulation illustrating these capabilities. [Job-shop scheduling](https://developers.google.com/optimization/scheduling/job_shop).

CP-SAT uses integer formulations. Choose and document time/cost discretization, scaling and rounding. A feasible result is not necessarily optimal: retain status, objective and available bounds; do not label a timed-out solution optimal. [CP-SAT](https://developers.google.com/optimization/cp/cp_solver).

| Alternative | When it is better / why it is not our default |
|---|---|
| MILP with HiGHS or SCIP | Strong alternative for continuous costs, inventory flows or scenario-based linear formulations. Benchmark against CP-SAT if the planner takes that form. [HiGHS](https://highs.dev/), [SCIP](https://www.scipopt.org/doc/html/WHATPROBLEMS.php). |
| Earliest-deadline heuristic | Essential baseline and possible fallback. It does not generally search global combinations of grouping/resources. |
| Reinforcement learning | Candidate for repeated sequential decisions after a credible environment exists. Learned policies still need hard-constraint handling and fair comparisons. |
| LLM-generated schedule | Could explain a validated solver result. Text generation must not be the authority for feasibility or reservations. |

We are selecting an optimization formulation, not letting the stack itself prove maintenance safety. Mandatory deadlines remain hard constraints; prediction-driven recommendations do not override them.

## 10. Simulation: why SimPy

Grounding, waiting for parts, acquiring a bay, completing work and returning a component to simulated service are events and resource queues. SimPy directly models processes that interact through events. [SimPy concepts](https://simpy.readthedocs.io/en/latest/simpy_intro/basic_concepts.html).

A game engine/3D physics simulator addresses different mechanics. A custom Rust/C++ event simulator could outperform Python on a particular workload, but we have no measurement requiring it. SimPy does not guarantee correct assumptions or computational speed. Parallelize independent replications and retain seeds, input manifests and policy versions. Compare downtime and resource contention under common scenarios. Maintenance effectiveness remains explicitly assumed when unsupported by the dataset.

## 11. Jobs, messaging and live updates

Select Celery with RabbitMQ for long calculations. The Python workers import shared packages but run independently of FastAPI. FastAPI's documentation explicitly points to tools such as Celery for heavy computation beyond small in-process background tasks. [FastAPI caveat](https://fastapi.tiangolo.com/tutorial/background-tasks/), [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html).

RabbitMQ supports durable messaging mechanisms, acknowledgements and publisher confirms. Configure these deliberately. Delivery can be repeated; tasks must be idempotent. Neither broker choice nor Celery provides an automatic exactly-once application outcome. [RabbitMQ reliability](https://www.rabbitmq.com/docs/reliability), [Celery task semantics](https://docs.celeryq.dev/en/stable/userguide/tasks.html).

PostgreSQL is the authority for job state and results. Save a job and an outbox entry atomically, then dispatch with confirmation and retry. Deduplicate by job/attempt identity; reject stale results from cancelled or superseded jobs. This is a proposed design, not behaviour supplied automatically by the libraries.

Redis is a supported alternative broker/cache, but RabbitMQ's task-messaging role is the chosen default. Kafka becomes relevant for independently replayed high-volume event streams across many consumers; no such requirement is established for our current job workflow. A database-only job queue is viable but would require us to implement dispatch, leasing and retry semantics. Avoid introducing it solely to reduce the service count.

Use REST/OpenAPI for commands and result queries; generate frontend types/clients and still perform runtime validation. Use SSE for one-way progress/alert updates, with event IDs and reconnection handling. Use WebSockets when a specific bidirectional interaction warrants them. [SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events). gRPC offers generated cross-language RPC contracts and can be appropriate for service streaming, but no internal RPC-heavy architecture is required here. [gRPC](https://grpc.io/docs/what-is-grpc/core-concepts/).

## 12. System topology and module ownership

The browser calls one application API. That API accesses PostgreSQL and submits durable jobs. Worker pools handle inference, planning and simulation separately, allowing different process limits and hardware. They share application packages, validation rules and result schemas; they do not duplicate the web application's business rules.

One Python codebase does not mean one process or one overloaded service. Keep modules for records, health assessments, alerts, planning, inventory, scenarios and approval history. Allocate CPU/GPU resources explicitly and keep heavyweight model loading out of ordinary record endpoints.

| Product feature | Principal module / technology |
|---|---|
| Unified records | FastAPI domain services + PostgreSQL relationships |
| Life estimates and intervals | Python inference workers + trained/calibrated artifacts |
| Evidence cards | Stored prediction provenance + React/ECharts |
| Stable alerts | Versioned Python policy + database alert history |
| Feasible maintenance plans | OR-Tools worker + transactional approval/reservation |
| Grouping and parts bottlenecks | Planner constraints + inventory service |
| Fleet what-if comparisons | SimPy workers + scenario/result manifests |
| Data-quality warnings | Shared ingestion/preprocessing checks + visible UI states |

For the five-person team, useful responsibility boundaries are: interface/design; records/API/persistence; data/prediction; planning/inventory; and simulation/integration. Shared contracts and integration reviews remain collective responsibilities.

Docker Compose describes the service network and persistent volumes; it does not create clustering or automatic failover. Keep deployment manifests portable and bundle model/data artifacts needed by the demonstration. [Compose model](https://docs.docker.com/compose/intro/compose-application-model/).

## 13. What would prove the choice, and what could overturn it

The following are planned acceptance comparisons, not tests already performed. Define numerical budgets from actual hardware and requirements before interpreting results.

| Decision | Fair validation | Change trigger |
|---|---|---|
| FastAPI backend | Replay representative ingestion and multi-user commands while background jobs run; measure p95/p99 latency, CPU/RAM, queue delay and failures. | A profiled API/parsing bottleneck remains after batching, query tuning and process isolation; test a Rust/Go implementation of that component. |
| React/ECharts | Test realistic visible points, linked selections, interval plots and timeline editing on target browsers. | Failed interaction latency or required interactions are better served by another renderer/component system. |
| PostgreSQL | Concurrent plan approval/stock reservations, rollback, stale-version rejection, representative history queries and restore tests. | Measured retention/analytics workload justifies a complementary store; do not discard transactional authority casually. |
| PyTorch/model choice | Compare identical engine splits and transformations, multiple runs, prediction error, calibration, missing-data robustness and inference cost. | Another framework's reproducible implementation or another model yields better validated tradeoffs. |
| CP-SAT | Compare feasible objectives/runtime/bounds against heuristic and MILP on the same task instances. | Continuous formulation or benchmark outcomes favour MILP. |
| SimPy | Check small analytically understandable scenarios, event ordering, seeds and policy comparisons; profile large replications. | Simulation overhead is the measured limit and an alternative gives equal validated behaviour faster. |
| Celery/RabbitMQ | Kill/restart workers and API processes, repeat messages, interrupt dispatch and submit cancellations. | Jobs are lost or effects duplicated: repair semantics/configuration before changing brands. |

Architecture quality cannot substitute for empirical model quality. NASA simulated engines plus synthetic logistics do not establish real military readiness, irrespective of programming language.

## 14. Commitment

Commit to the Python-centred scientific application architecture. React and PyTorch are replaceable choices within it; PostgreSQL and separation of durable computation from web requests have particularly strong requirement support. Reserve Rust for an identified component with a measured benefit.

The best-supported advantage is consistency from dataset preparation through prediction, scheduling and simulation, combined with transactional records and a responsive interface. No evidence presently establishes a universal fastest stack, and our selection should remain falsifiable through the tests above.
