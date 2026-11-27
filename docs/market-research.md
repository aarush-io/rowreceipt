# Market research

Desk research conducted November 27, 2026. Scores are judgments based on public evidence and a solo-maintainer cost model. There were no user interviews, customer commitments or statistically representative demand estimates.

## Evidence by channel

- GitHub's 2025 report put MCP at 37,000 stars in eight months and listed uv and vLLM among the fastest-growing projects by contributors. The 2026 report compares independent projects with vendor-led ones and uses contributor growth and engagement measures. The November 26 Trending snapshot was heavy on coding agents. These show how attention and contributor growth can diverge from a durable workflow. Full individual historical star curves were unavailable for this study. [2025 Octoverse](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/) · [2026 Octoverse](https://github.blog/news-insights/octoverse/octoverse-commits-pushes-reach-new-highs-in-2026-as-developers-build-with-agents/) · [Trending archive](https://trend.ondo.sh/github/2026-11-26/en.html) · [Data portability topic](https://github.com/topics/data-portability) · [Offline-first topic](https://github.com/topics/offline-first)
- A Hacker News launch discussion asks for practical large-scale, low-network database comparison. Stack Overflow users document years of SQLite comparison workarounds and trouble comparing rows across storage layouts. A Reddit migration practitioner reports finding subtle copy errors after adopting row-level reconciliation. These directly validate comparison pain. They provide weaker evidence for independent receipts specifically. [Show HN](https://news.ycombinator.com/item?id=31837307) · [SQLite comparison](https://stackoverflow.com/questions/2093263/how-to-compare-two-sqlite-databases-on-linux) · [Ignoring rowid](https://stackoverflow.com/questions/70460111/show-diff-of-two-sqlite-databases-ignoring-rowid) · [Migration discussion](https://www.reddit.com/r/dataengineering/comments/1jwn3gu)
- Backup users describe restore exercises and the overhead of coordinating container shutdowns. Litestream issues report difficult restore failures and missing committed data. Product Hunt's Turso listing shows a commercial distribution channel for production SQLite tools and per-user databases, with no direct evidence of sales demand for receipts. [Docker backup discussion](https://www.reddit.com/r/selfhosted/comments/1xfqpq5/how_do_you_handle_backing_up_databases/) · [Restore experiences](https://www.reddit.com/r/selfhosted/comments/188kkjy) · [Litestream #1164](https://github.com/benbjohnson/litestream/issues/1164) · [Litestream #1540](https://github.com/benbjohnson/litestream/issues/1540) · [Turso on Product Hunt](https://www.producthunt.com/products/turso)
- Datafold stopped maintaining its open-source data-diff in May 2024. Reladiff continues the architecture in open source. Redgate listed SQL Data Compare at $327 per user per year and its Toolbelt Essentials bundle at $1,410 per user per year. It requires a commercial license for specified automated uses. The list prices describe SQL Server products with a different scope from the SQLite/CSV workflow. Tracetest announced the end of its cloud service and continued distribution of the open-source project. [Datafold archive](https://github.com/datafold/data-diff) · [Reladiff design](https://reladiff.readthedocs.io/en/latest/technical-explanation.html) · [SQL Data Compare price](https://www.red-gate.com/products/sql-data-compare/) · [Toolbelt price](https://www.red-gate.com/products/sql-toolbelt-essentials/) · [Redgate licensing](https://documentation.red-gate.com/sdc/getting-started/licensing) · [Tracetest announcement](https://tracetest.io/blog/end-of-life-announcement-for-tracetest-cloud)
- BagIt standardizes byte-level package manifests. Invertible Bloom lookup table research offers compact set reconciliation but introduces probabilistic decode and more protocol complexity than a fixed-bucket equality check. The SLSA spec covers build provenance. SQLite's documentation and the Datafold engineering blog describe related hashing and compare techniques. [BagIt RFC](https://www.rfc-editor.org/rfc/rfc8493.html) · [Set reconciliation research](https://dash.harvard.edu/entities/publication/73120378-eb24-6bd4-e053-0100007fdf3b) · [SLSA](https://slsa.dev/spec/v1.2/build-provenance) · [SQLite dbhash](https://www.sqlite.org/dbhash.html) · [Datafold engineering](https://www.datafold.com/blog/open-source-data-diff/)
- MCP fingerprint and replay issues establish tool contract demand. Inspector v2's documented test fixtures and multiple specialist tools make drift testing crowded. A2A and WASI standardize other interoperability layers. Local compute candidates face device-specific runtimes. [MCP fingerprint request](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2744) · [Inspector test servers](https://github.com/modelcontextprotocol/inspector/blob/main/docs/test-servers.md) · [A2A](https://github.com/a2aproject/A2A) · [WASI](https://github.com/WebAssembly/WASI) · [llama.cpp Android](https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md)

- Local-first software research framed storage ownership and offline operation years before the current sync products. WASI component work, the OTLP file exporter and in-process SQLite suggest interoperable files and vectors are sustainable extension surfaces. Intel's Unison discontinuation exposed an OS interoperability gap, but LocalSend, PairDrop, scrcpy and KDE Connect offer strong adjacent workflows. [Local-first paper](https://www.inkandswitch.com/essay/local-first/) · [WASM component model](https://github.com/WebAssembly/component-model) · [OTLP file exporter](https://opentelemetry.io/docs/specs/otel/protocol/file-exporter/) · [Intel notice](https://www.intel.com/content/www/us/en/support/articles/000102120/software.html) · [LocalSend](https://github.com/localsend/localsend) · [PairDrop](https://github.com/schlagmichdoch/PairDrop) · [scrcpy](https://github.com/Genymobile/scrcpy)
- The official SQLite forum includes database-comparison and snapshot-integrity questions. Bijection offers interactive schema and data diffing. Commercial Datafold's FAQ describes pricing models without a price directly comparable to this local tool. [SQLite compare thread](https://sqlite.org/forum/info/61e7e70236e03b19a9de47586bab0dc6cc85dd6d5f1b77f278b24975fcc9cd74) · [Backup API thread](https://sqlite.org/forum/info/3dd8dad9f82e457501176c1a2ac158640a0c90a090a8db320a425dbba9515f5d) · [Bijection](https://bijection.dev/) · [Datafold pricing FAQ](https://www.datafold.com/faq/how-does-datafolds-pricing-work/) · [GitHub Trending](https://github.com/trending?spoken_language_code=en)

## Concept inventory

Each entry describes an implementable wedge and the first adjacent implementation to inspect. The shortlist below received deeper alternate-terminology searches.

| # | Concept | Gap and initial comparator |
|---:|---|---|
| 1 | RowReceipt | Independently generated typed SQLite/CSV reconciliation receipts. Reladiff and dbhash. |
| 2 | RestoreLens | Verify business invariants against isolated SQLite restores. RestoreVerify and sqlite-backup-probe. |
| 3 | StackTransfer | Verify a Compose volume migration against declared state. docker-backup and Offen. |
| 4 | TraceParcel | Turn OTLP incident captures into scrubbed portable files for regression checks. Tracetest and Collector. |
| 5 | ToolContract | Offline MCP consumer contract gate with compatibility policy. Inspector and mcp-contracts. |
| 6 | RoomMatrix | Replay Android Room upgrades across an anonymized historical schema corpus. Room MigrationTestHelper. |
| 7 | DeviceTriage | Capture an opt-in, scrubbed Android permission/state bundle for support. ADB bugreport. |
| 8 | BridgeQueue | Resumable selective device transfer with a receipt for large offline folders. LocalSend and Syncthing. |
| 9 | DeskHandoff | Cross-platform clipboard with expiry and paste-time approval. KDE Connect. |
| 10 | DisplayProof | Reproduce Android display and input issues with a minimal interaction archive. scrcpy and Perfetto. |
| 11 | ModelFit | Measure actual model/backend compatibility before allocating large caches. llama-bench. |
| 12 | ThermalBudget | Repeatable Android CPU/GPU inference profiling under thermal and battery caps. Perfetto and llama.cpp. |
| 13 | ModelStore | Share verified model blobs between runtimes without duplicating disk. Hugging Face Hub cache and Ollama. |
| 14 | TaskFerry | Run retryable offline batch jobs on a LAN with content-addressed inputs. BOINC and Ray. |
| 15 | EdgeUpdate | Stage, verify, and roll back update bundles for disconnected edge operators. RAUC and Mender. |
| 16 | P2PResume | Validate resumable transfers across changing network interfaces and relays. Iroh and libp2p. |
| 17 | SyncClinic | Replay and shrink local-first replication divergences. Automerge and Jepsen. |
| 18 | ReplicaExit | Export typed records with convergence metadata from sync projects. PowerSync and Electric. |
| 19 | CaseCollision | Preflight sync trees for Unicode, case, and filesystem naming hazards. Syncthing and rclone. |
| 20 | StateWitness | Compare export completeness across vendor workspace versions offline. BagIt and Frictionless Data. |
| 21 | EnvWitness | Explain why two build environments behave differently with shareable stripped evidence. diffoscope and reprotest. |
| 22 | SBOMBridge | Verify component identity across SPDX and CycloneDX conversion. Syft and Protobom. |
| 23 | BuildParcel | Ship a rebuildable bundle with declared offline dependencies. Nix and Reproducible Builds tooling. |
| 24 | WasiAudit | Diff WASI component capability imports before deployment. wasm-tools and Wasmtime. |
| 25 | PluginContract | Test a WASI plugin against multiple host ABI revisions. cargo-component and component tooling. |
| 26 | EdgeReplay | Replay sanitized event streams on simulated edge clocks. Spin and OpenTelemetry Collector. |
| 27 | CrashParcel | Assemble symbol provenance and portable crash evidence without uploading a dump. minidump-stackwalk. |
| 28 | ConfigDrift | Explain configuration overrides from live services and deployment definitions. Conftest and Config Connector. |
| 29 | JobWitness | Capture artifact digests and retries for local automation runs. Task, just, and Dagger. |
| 30 | KeyScope | Review how development secret files move between decrypted workspaces. SOPS and age. |
| 31 | AttestLab | Reproduce permission and policy differences across confidential-computing templates. Trustee. |
| 32 | AgentCardCheck | Validate A2A Agent Cards and capability negotiation between implementations. A2A SDKs and inspector tools. |
| 33 | AgentRunCapsule | Capture deterministic user-controlled tool fixtures for regression tests. MCP Inspector replay and VCR. |
| 34 | ExportPolicy | See which typed fields and metadata an export exposes before sharing. Great Expectations and Frictionless. |
| 35 | QueueTransfer | Transfer pending jobs between self-hosted queue versions with idempotency evidence. RabbitMQ shovel and Redis tooling. |
| 36 | ArchiveRestore | Measure which archived deployment artifacts still restore without registry access. ORAS and Velero. |

## Scored shortlist

Columns in order follow the requested rubric. Each component is bounded by its column maximum.

| Candidate | Use 20 | Audience 15 | Diff. 15 | Innovation 10 | Relevance 10 | Adoption 10 | Feasible 10 | Cost 5 | Ecosystem 5 | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RowReceipt | 18 | 12 | 13 | 8 | 10 | 8 | 9 | 5 | 4 | 87 |
| RestoreLens | 19 | 12 | 6 | 6 | 10 | 8 | 9 | 5 | 4 | 79 |
| StackTransfer | 18 | 12 | 7 | 6 | 9 | 8 | 7 | 5 | 4 | 76 |
| TraceParcel | 16 | 11 | 8 | 7 | 9 | 7 | 7 | 5 | 4 | 74 |
| ToolContract | 16 | 12 | 5 | 6 | 8 | 7 | 9 | 5 | 4 | 72 |

### RowReceipt

**Compare the rows in two copies of a dataset without moving either copy.** The first audience is SQLite maintainers, embedded or edge developers, and migration operators exchanging SQL exports. Search terms included logical database hash, two-site or offline reconciliation, SQLite/CSV parity, checksum bisection, detached comparison manifests and keyed row digests. SQLite dbhash produces an independent logical hash already. It covers SQLite schema and content, and cannot identify a mismatching bucket. sqldiff is a better fit for generating changes from two available SQLite databases. Reladiff and archived Datafold data-diff perform segmented checks while connected to both sides. DataCompy, dumptales and row-reconcile compare two available data inputs. csvdb provides format-independent checksums and transparent, versionable exports. Redgate and commercial Datafold address centralized reconciliation with a broader feature set.

The wedge is independent capture under a shared typed contract, followed by authenticated comparison of compact JSON files. An SQLite table and a CSV may map different physical column names onto the same contract. The two sides do not exchange row lists, keys or database credentials. Changed buckets narrow follow-up while exposing distribution metadata. No existing tools need to be removed. Readers with simultaneous access to both sources and a need for exact changed rows should keep using a conventional diff. Separate capture is cheaper to deploy for the stated workflow because it requires no relay, dashboard or hosted account. The first integration is backup/restore or export CI, with a Python API and documented exchange format. Runtime infrastructure cost is $0/month and the implementation is medium complexity. The commercial risk is that many teams already allow both datasets in one comparison job. The technical risks are type semantics, duplicate keys, scratch I/O and privacy claims. Competitors can copy the format. Cross-language test vectors and independent producers are the plausible adoption advantage. [dbhash](https://www.sqlite.org/dbhash.html) · [sqldiff](https://www.sqlite.org/sqldiff.html) · [Reladiff](https://reladiff.readthedocs.io/en/latest/technical-explanation.html) · [csvdb](https://github.com/jeff-gorelick/csvdb) · [DataCompy](https://github.com/capitalone/datacompy) · [dumptales](https://pypi.org/project/dumptales/) · [row-reconcile](https://github.com/KanadeK/row-reconcile)

### RestoreLens

**Run your application's recovery checks against an isolated SQLite restore.** Self-hosters and embedded database maintainers need more than a completed backup job. Searches for restore drills, SQLite integrity probes, business invariants and backup checksum verification found sqlite-backup-probe, RestoreVerify, Restorable and SafeGrd. Litestream and its Rails integration already offer related restore and freshness workflows. A local runner with checked assertions and no container runtime could reduce setup for some teams, but the first competitor already covers much of this wedge. Medium complexity, $0/month for local operation. Start with Litestream CI examples. Users would switch for simple local checks only if they already restore via a tool that lacks them. Major risks are compatibility and misleading freshness claims. [sqlite-backup-probe](https://github.com/KanadeK/sqlite-backup-probe) · [RestoreVerify](https://github.com/RestoreVerify/restoreverify) · [Restorable](https://restorable.dev/) · [SafeGrd](https://safegrd.dev/) · [Litestream Ruby](https://github.com/fractaledmind/litestream-ruby)

### StackTransfer

**Move a Compose stack to another host and verify the restored state.** Self-hosters and homelab operators already report challenges with consistency and volume handoff. Searches for Compose evacuation, portable projects, volume rebinding, restore manifests and archive verification found docker-backup's Compose-aware volume mapping and existing volume backup tools. A preflight and post-restore compatibility check across engines could justify switching from scripts. High complexity, $0/month runtime with a local Docker or Podman host. Start with two common application migrations. Rootless volume ownership, architecture-specific images, secrets and app-safe snapshotting are risks, and many users rarely move stacks. [docker-backup](https://docker-backup.readthedocs.io/en/latest/compose/) · [volume-backup](https://github.com/loomchild/volume-backup) · [Offen](https://github.com/offen/docker-volume-backup)

### TraceParcel

**Share an incident trace as a scrubbed regression fixture.** SREs and library maintainers have a portable input in OTLP. Searches for trace replay, fixture packaging, telemetry redaction and trace-based tests found Collector processors and Tracetest. A deterministic file plus field removal and assertions would replace manual capture scripts for teams that only need a portable example. Medium-high complexity and $0/month with a local collector. Contribute a fixture exchange example to an OpenTelemetry demo. Data leaks through unexpected attributes and uncertainty around replay fidelity are primary risks. [Collector contrib](https://github.com/open-telemetry/opentelemetry-collector-contrib) · [Tracetest](https://github.com/kubeshop/tracetest) · [Tracetest Cloud end of life](https://tracetest.io/blog/end-of-life-announcement-for-tracetest-cloud)

### ToolContract

**Catch an incompatible MCP change before a client sees it.** Clients and server authors have requested stable fingerprints. Searches for MCP schema drift, snapshot gates, contract diff, replay and consumer compatibility found Inspector v2, mcpdrift, mcp-contracts, Covenant and mcpward. A fully offline client-specific policy matrix could avoid starting a server in some CI jobs. Medium complexity and $0/month runtime. Adopt via existing SDK tests. Users would switch if baselines were portable across consumers. Spec churn and direct competitors with comparable interfaces reduce the case for an independent project. [Inspector replay issue](https://github.com/modelcontextprotocol/inspector/issues/1893) · [mcpdrift](https://github.com/mujinlabs/mcpdrift) · [mcp-contracts](https://github.com/mcp-contracts/mcp-contracts) · [Covenant](https://github.com/Mhemd139/Covenant) · [mcpward](https://github.com/TsvetanG2/mcpward)

## Selection

RowReceipt takes on a recurring comparison problem with a smaller permission and deployment footprint. The test is whether two operators who cannot access each other's data can create receipts independently, detect a same-count value change, and exchange fewer than 8 KiB per side at the default resolution regardless of row count. Published evidence is strongest for data parity generally. Independent capture is a differentiated hypothesis. The closest surveyed tools and open-ended search leave room for undiscovered implementations. Organic adoption at any particular scale remains unverified.
