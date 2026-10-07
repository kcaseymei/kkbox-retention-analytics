# KKBox Retention Analytics — Master Plan

Version: 1.0  
Last updated: 2026-10-05  
Project owner: Casey Mei  
Development project display name: `kkbox-analytics`  
Repository: [`kcaseymei/kkbox-retention-analytics`](https://github.com/kcaseymei/kkbox-retention-analytics)  
Canonical location: `KKBOX_MASTER_PLAN.md` at the repository root

## At a glance (updated 2026-10-05)

**Headline question:** Which behavioral signals appear before a KKBox subscriber churns, how early do they appear, and whom should be prioritized for intervention at a limited operational capacity?

| Stage | Work | Detailed phases (Section 6) | Status |
|---|---|---|---|
| A. Audit and definitions | Full-dataset audit (v1 + v2), issue register, churn definition, cutoff and feature windows | 1, and the definitions part of 3 | **In progress** |
| B. Relational analytics | PostgreSQL, metric definitions, cohort and renewal SQL | 2, descriptive part of 3 | **In progress** (database built, SQL analyses next) |
| C. Behavioral features | `user_logs` to user × cutoff features (Databricks/PySpark) | 4 | Planned |
| D. Serving and BI | Snowflake marts, Power BI dashboard (Tableau optional) | 5, 6, 7 | Planned |
| E. Prediction and prioritization | Baseline plus one stronger model, top-k evaluation | 8 | Planned |
| F. Recommendations and write-up | Intervention and experiment design, README, case study | 9, 10 | Planned |

Public README uses five layers: Python/pandas/Parquet, PostgreSQL, Databricks/PySpark, Snowflake, Power BI/Tableau. Fabric is an optional extension. Details: Section 3 (simplified roadmap) and the 2026-10-02 decision log entries.

**Current state:** Phase 1 (data audit) is complete and published on `main` (README, `notebooks/01_data_audit.ipynb`, reports, register DQ-001 to DQ-019, reusable checks, tests). The label rebuild (`src/churn_labels.py`, `notebooks/02_population_and_churn.ipynb`) reproduces the official February and March 2017 labels for 98.4% and 95.7% of shared users and builds 25 monthly cohorts; it is published with a chart in the README. Open: how early renewers are labeled, why the official sample includes users outside the last-expiration rule, the cause of the batch cohorts, and the `total_secs` treatment.

**Next action:** build the relational layer (stage B: PostgreSQL schema, metric definitions, cohort retention SQL) and the behavioral features (stage C) following `docs/prediction_design.md`, updating the README status table after each block. Later: decide whether to hide or trim this plan on the public repository (reminder). Open checks: how early renewers are labeled; whether users without logs are the users without member profiles.

## 1. Purpose and continuity

This document is the source of truth for project scope, architecture, sequencing, decisions, and progress. Read it at the start of future work and update it when a phase, definition, or material decision changes. It expands the original project charter (`PROJECT_PLAN.md`, removed on 2026-10-06 and kept in the Git history); this document is the only plan.

The local Git repository is the development workspace. The Codex project should point to that existing directory, rather than create another copy of the repository. ChatGPT project discussions can support learning and ideation; any accepted decisions must be recorded here. A copied or uploaded version is a dated snapshot, not an independently maintained master.

## 2. Source, repository, and established setup

- Original competition: **WSDM – KKBox's Churn Prediction Challenge**.
- Official Kaggle URL: https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge
- GitHub repository: https://github.com/kcaseymei/kkbox-retention-analytics
- Existing local clone: the repository directory under the owner's `workspace/projects` folder (absolute path omitted).
- Prior planning conversation: `kkbox-github`, conversation ID `6ab5692c-9088-83e8-b5de-88b93c8a9ecf`.

### Completed setup

The user and prior conversation report that Homebrew, Git, GitHub CLI authentication, repository creation, cloning under `workspace/projects`, staging, committing, and pushing were completed successfully. The first project charter, `PROJECT_PLAN.md`, was created and pushed (later removed; see the decision log).

Direct local inspection on 2026-09-25 confirmed the repository directory, initial charter, README, and existing `data/`, `notebooks/`, `reports/`, `sql/`, and `src/` directories. The `.gitignore` contains:

```gitignore
data/raw/*
data/processed/*
```

Recent local history includes `5fe904c` (initial commit), `807cbff` (data-directory ignore configuration), and `503d237` (initial project plan). A successful push was shown in the prior conversation, and the user subsequently confirmed pushing the project plan. Current remote synchronization and authentication have not been re-tested for this documentation task.

Do not treat setup completion as evidence that the data audit, SQL models, cloud pipelines, dashboards, or predictive model are complete.

## 3. Project positioning

Build an **end-to-end subscription retention and modern analytics stack case study**, from raw data to a defensible business decision. Kaggle provides the dataset and original prediction setting; the portfolio expands the scope to subscriber behavior, retention measurement, analytical engineering, visualization, prediction, and intervention design.

The portfolio should demonstrate the ability to clarify an ambiguous business problem, evaluate data quality, define trustworthy metrics, design reproducible transformations, communicate evidence, and propose testable retention actions. Model performance is one component of the case study.

### Primary business question

> What subscriber behaviors and transaction patterns are associated with churn, when do those signals emerge, and how can KKBox use them to improve retention?

### Analytical questions

1. What does churn look like across the eligible subscriber base and observable time periods?
2. Which transaction and subscription patterns are associated with churn, including renewal timing, cancellation indicators, auto-renewal, plan duration, and payment behavior where supported by the data?
3. How does listening engagement differ between retained and churned subscribers?
4. How early before a prediction or renewal cutoff do behavioral signals become visible?
5. Which cohorts and subscriber segments have elevated churn or weaker retention?
6. Which associations remain useful after accounting for differences in tenure, plan, and other observed characteristics?
7. Which customers could be prioritized at a realistic intervention capacity, and with how much lead time?
8. Which retention actions should be tested, and how would incremental impact be measured?

Historical associations do not establish causal impact. Do not claim a retention lift or financial return without observed experimental evidence; any scenario estimate must disclose its assumptions.

### Simplified public roadmap (adopted 2026-10-02)

The 10 phases below remain the detailed internal plan. The recruiter-facing story and the working priority use six stages and one headline question.

> **Headline question:** Which behavioral signals appear before a KKBox subscriber churns, how early do they appear, and whom should be prioritized for intervention at a limited operational capacity?

The eight analytical questions above collapse into four: (1) what churn looks like and who is higher risk; (2) which transaction and listening signals precede churn, including a robustness check after controlling for tenure and plan; (3) how early the signals appear and what top-k prioritization achieves; (4) which interventions to test and how to measure them.

| Stage | Work | Questions | Platforms | Time cap |
|---|---|---|---|---|
| A. Audit and definitions | Core-table audit, issue register, churn definition, **cutoff and feature windows**, verify the label window of `train_v2` | Foundation | Python / pandas / Parquet | 2 weeks |
| B. Relational analytics | Load, metric definitions, cohort retention and renewal SQL | 1, 2 | PostgreSQL | 2 weeks |
| C. Behavioral features | `user_logs` aggregated to user × cutoff features | 2, 3 | Databricks / PySpark | 2 weeks |
| D. Serving and BI | Three marts and one dashboard | 1, 2 | Snowflake, Power BI | 2 weeks |
| E. Prediction and prioritization | Baseline plus one stronger model, top-k evaluation | 3 | Python | 1 week |
| F. Recommendations and write-up | Intervention and experiment design, README, case study | 4 | GitHub | 1 week |

- Phase 3 definitions (cutoff, feature windows, eligible population) are fixed during stage A so stage C does not need rework. **Cutoff** = the as-of date for prediction: data before it builds features, data after it only determines the outcome label.
- Tableau and Fabric are optional extensions after the main line is complete.
- Stage A completion standard: core-table audit and issue register done, `train_v2` label window verified against transactions; remaining items are recorded as known unresolved, not expanded.
- Cohort retention over time may require reconstructing labels per month from transactions. This depends on the unverified assumption that the supplied labels cover only one or two expiration months; verify in stage A.
- Each stage needs one demonstrable artifact (see the 2026-10-02 update entry).

## 4. Learning and implementation principles

- Introduce each tool when a concrete project requirement makes it useful. Start locally; add cloud platforms after the data and analytical contracts are understood.
- Use the actual KKBox project to learn database concepts, distributed processing, warehouse design, and business intelligence.
- Keep a small end-to-end slice working before scaling it. Profile runtime and memory before moving a workload.
- Define population, time windows, table grain, and metric denominators before publishing comparisons.
- Preserve raw inputs. Record each quality issue as finding → decision → treatment → validation.
- Distinguish full-data checks from sample checks, hypotheses from findings, and planned deliverables from implemented ones.
- Make notebook execution reproducible, extract reused logic into `src/`, and keep SQL readable and versioned.
- Keep raw/processed datasets, credentials, personal machine configuration, and large generated artifacts out of Git.
- Use Git continuously: inspect changes, stage deliberately, commit coherent work, and push at appropriate milestones.

## 5. Target architecture and tool responsibilities

This is the planned architecture, not an assertion that these systems are deployed.

```text
KKBox raw data + file/version manifest
                 |
          Python / pandas audit
                 |
       Population and time contracts
                 |
       +---------+-------------------------+
       |                                   |
Members / transactions / labels       Large user_logs workload
       |                                   |
PostgreSQL + pgAdmin                  Databricks + PySpark
Relational storage and SQL           Delta Bronze → Silver → Gold
       |                                   |
       +---------- curated exports --------+
                          |
                       Snowflake
              Conformed analytics marts
                          |
       +------------------+------------------+
       |                  |                  |
    Power BI           Tableau        Point-in-time feature data
Executive monitoring   Exploration    Predictive modeling
       |                  |                  |
       +------------------+------------------+
                          |
           Recommendations and experiment design
                          |
              GitHub README and case study
```

| Tool/layer | Responsibility and rationale | Intended output |
|---|---|---|
| Python / pandas / Jupyter | Inspect files, quantify quality issues, explore patterns, and prototype transparent transformations. Use bounded reads or chunks where needed. | Reproducible audit, data dictionary, findings and treatment log |
| PostgreSQL | Learn relational fundamentals and maintain local structured storage and analytical models: database, schema, tables, keys, joins, indexes, views, and queries. | Versioned DDL, load steps, quality checks, SQL analyses |
| pgAdmin | Inspect and manage PostgreSQL and run or review SQL. It is the database client, not another storage layer. | Documented local database workflow |
| Product/retention analytics | Establish business definitions and describe cohorts, engagement, subscription behavior, and intervention windows. | Metric contracts and evidence-backed descriptive findings |
| Databricks / PySpark / Delta | Process the large behavioral `user_logs` workload and learn distributed transformations and layered data quality. Audit the actual input grain before calling it individual event data; source logs may already summarize activity by user and date. | Bronze source-preserving tables, Silver validated records, Gold behavioral aggregates |
| Snowflake | Serve as the cloud analytics warehouse and shared serving layer for curated structured data and behavioral aggregates. Avoid duplicating every raw transformation from the other systems. | Documented marts, refresh dependencies, reconciled totals |
| Power BI | Executive retention monitoring with clear KPI definitions, cohort context, segment filters, and actionable views. | Executive dashboard and measure documentation |
| Tableau | Complementary exploration and storytelling, such as cohort patterns, behavioral trajectories, and segment comparisons. | Focused exploratory workbook/story rather than a duplicate dashboard |
| Predictive modeling | Add risk prioritization after descriptive/product analysis, using only information available at prediction time. | Baseline, evaluated model, calibration and prioritization analysis |
| Business recommendations | Translate validated patterns into intervention hypotheses and measurable experiments. | Prioritized actions and experiment specifications |
| GitHub | Explain the problem, methods, architecture, evidence, limitations, and reproducibility. | Polished README and final case study |

The public README presents a compressed five-layer version of this architecture; see the 2026-10-02 decision log entry.

The planned exchange between systems is explicit, versioned curated exports or supported connectors, with row counts, schemas, date coverage, and checksums or batch identifiers recorded. Select the actual transfer method during implementation. Do not imply real-time orchestration or production deployment unless implemented and verified.

## 6. Phases, deliverables, and completion gates

### Phase 0 — Git and project setup: complete

Established the repository, development folder structure, ignore rules, initial charter, and commit/push workflow. Continue using these practices in all phases.

### Phase 1 — Python/pandas data audit: in progress

Create `notebooks/01_data_audit.ipynb` and build a reproducible inventory before cleaning:

- File names, source versions, sizes, compression formats, and available date coverage.
- Row and column counts, schemas, types, candidate keys, observed grain, and relationships.
- Missing values, categorical distributions, date parsing, numeric ranges, and invalid values.
- Exact duplicates versus legitimate repeated transactions; member coverage and unmatched joins.
- Transaction chronology and anomalies, including expiration before transaction date, zero plan days, cancellation and renewal patterns, and same-day records.
- Behavioral log coverage, duplicate user/date combinations, metric validity, and possible aggregation grain.
- Runtime and memory observations to choose sampling, chunking, or later distributed processing.

Earlier exploratory concerns include missing `gender`, unusual `bd`, expiration/transaction inconsistencies, zero plan days, and same-day transaction duplicates. These are **items to re-check**, not accepted audit findings or reasons to delete records automatically.

Outputs: the notebook, `reports/data_audit.md`, `docs/data_dictionary.md`, and an issue/treatment register. Completion requires reproducible execution, clearly labeled sample versus full-data evidence, and documented unresolved issues.

### Phase 2 — PostgreSQL and pgAdmin

Define staging and analytical schemas; load audited structured data; practice DDL, data types, candidate keys, foreign-key coverage, indexes, joins, CTEs, window functions, views, and query inspection. Keep large logs sampled or aggregated locally if full ingestion is impractical.

Proposed entities are members, transactions, behavioral aggregates, and churn labels. Treat natural keys and transaction identifiers as hypotheses until audited. Do not silently drop unmatched records to force referential integrity.

Outputs: DDL, repeatable ingestion, a relationship diagram, SQL checks, and local setup instructions. Completion requires reconciliation to source counts and a documented join strategy without unexplained row multiplication.

### Phase 3 — Churn definition and product/retention analysis

Read the official competition definition and record the exact data version, label rules, eligible population, observation window, prediction cutoff, outcome window, renewal/grace rules, and handling of censoring. The supplied Scala labeller has now been inspected: renewal gap < 30 means retained; gap >= 30 means churn. See `docs/churn_definition.md` for the exact rules. Local data/version and window alignment remain unverified.

Distinguish Kaggle-provided labels from any independently derived business churn metric. An observed label rate in a labeled sample is not automatically the full subscriber-base churn rate. Cancellation flags alone should not be assumed to equal churn.

Analyze retention/cohorts, tenure, renewal and payment patterns, engagement levels and changes, segment differences, and possible intervention lead time. Record denominator and coverage limitations for each result.

Outputs: `docs/metric_definitions.md`, versioned SQL, analysis notebooks, and an initial findings brief. Completion requires stable definitions and traceable descriptive conclusions before model development.

### Phase 4 — Databricks, PySpark, and Delta

Use the actual size and processing needs of `user_logs` to motivate distributed processing. Bronze preserves source records and provenance; Silver validates types, grain, and approved treatments; Gold aggregates behavior at documented user/day or user/cutoff grains.

Candidate features include active days, listening volume, recency, and engagement changes over explicitly bounded windows, subject to available fields. Validate a comparable sample against the pandas/local implementation and document partitioning, execution time, and rerun behavior.

Outputs: exported/versioned notebooks or scripts, Delta layer definitions, quality checks, and Gold aggregates. Completion requires reconciled outputs and repeatable runs. Service configuration and cost assumptions remain to be selected.

### Phase 5 — Snowflake analytics warehouse

Load curated structured data and Gold behavioral aggregates into a conformed warehouse. Proposed marts include subscriber snapshots, retention cohorts, engagement trends, and transaction/renewal patterns. Define grain, keys, owner/source, refresh cadence, and time-window semantics for each.

Separate a KPI-serving snapshot from a training/prediction snapshot where their eligibility or timing differs. Reconcile warehouse measures to validated source analyses.

Outputs: warehouse DDL/transforms, mart documentation, reconciliation checks, and a runbook. Completion requires consistent definitions and a reproducible load path for BI.

### Phase 6 — Power BI executive dashboard

Design for a retention stakeholder: churn/renewal measures with explicit populations, eligible subscriber counts, cohorts, segment patterns, engagement signals, and historical context. Revenue measures are included only if transaction semantics support them; do not equate a payment field with recurring revenue without justification.

Outputs: dashboard file or supported project format, screenshots, measures, filters, data freshness label, and a concise user guide. Completion requires reconciliation of totals and verification of filter behavior. Confirm the available authoring environment before beginning; the user's current machine is a Mac.

### Phase 7 — Tableau exploration and storytelling

Use the same validated marts for deeper exploration: cohort retention, pre-churn engagement trajectories, subscription segments, and lead-time comparisons. Choose views that add analytical value alongside Power BI.

Outputs: workbook or supported project format, screenshots, and an evidence-backed narrative. Completion requires consistency with canonical metric definitions and successful interaction checks.

### Phase 8 — Predictive churn modeling

Start after descriptive analysis and point-in-time features are reliable. Establish a simple baseline, then a justified stronger model. Use chronological validation when data coverage permits, document member overlap and leakage controls, and keep future outcomes out of feature windows.

Evaluate discrimination, probability quality, calibration, and precision/recall or lift at a realistic intervention capacity. Report class prevalence and compare against baseline. Do not choose accuracy alone for an imbalanced problem. Interpret predictive associations without describing them as causal drivers.

Outputs: reproducible training/evaluation, model comparison, feature definitions, leakage checks, and a model card. Completion requires a documented holdout protocol and an honest assessment of operational usefulness.

### Phase 9 — Recommendations and experimentation

For each proposed action, document the target segment, evidence, intervention hypothesis, timing, expected mechanism, feasibility, and limitations. Candidate ideas such as renewal reminders, payment recovery, or engagement messaging remain hypotheses until supported.

Design a randomized experiment with eligibility, randomization unit, treatment/control, primary outcome, observation period, guardrails, contamination considerations, and a sample-size plan based on stated assumptions. Separate predicted churn risk from likelihood of responding to treatment.

Outputs: prioritized recommendation memo and experiment plan. Completion does not require inventing or claiming a live experiment.

### Phase 10 — Final GitHub portfolio

Polish the README around business problem → data and definitions → architecture → methods → validated findings → dashboards → modeling → recommendations → limitations. Include reproducibility steps, selected visuals, artifact links, and an honest description of implemented versus conceptual components.

Outputs: finished README, case study, architecture diagram, dashboard previews, and interview talking points. Completion requires functioning links, consistent numbers, documented environments, and a clean review for secrets or unintended datasets.

## 7. Planned repository structure

This is a target structure. Create files when their phase needs them; names beyond the exact next notebook may evolve. Existing directories and user files must be preserved.

```text
kkbox-retention-analytics/
├── README.md
├── KKBOX_MASTER_PLAN.md
├── AGENTS.md                         # local only, git-ignored (with CLAUDE.md)
├── .gitignore
├── requirements.txt                  # Or the dependency format selected later
├── data/
│   ├── raw/                          # Ignored; immutable source inputs
│   └── processed/                    # Ignored; reproducible derived data
├── docs/
│   ├── data_dictionary.md
│   ├── metric_definitions.md
│   ├── architecture.md
│   └── runbook.md
├── notebooks/
│   ├── 01_data_audit.ipynb            # Exact next deliverable
│   ├── 02_population_and_churn.ipynb
│   ├── 03_cohort_retention.ipynb
│   ├── 04_transaction_analysis.ipynb
│   ├── 05_engagement_analysis.ipynb
│   └── 06_churn_modeling.ipynb
├── sql/
│   ├── postgres/                     # DDL, staging, loading, relational models
│   ├── quality/                      # Keys, coverage, dates, reconciliation
│   ├── analysis/                     # Cohorts, transactions, engagement
│   └── snowflake/                    # Curated warehouse models and marts
├── src/                              # Reusable ingestion/transformation logic
├── databricks/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── dashboards/
│   ├── power_bi/
│   ├── tableau/
│   └── screenshots/
├── reports/
│   ├── data_audit.md
│   ├── retention_findings.md
│   ├── model_card.md
│   ├── recommendations.md
│   └── case_study.md
└── tests/                            # Meaningful transformation/quality checks
```

Each SQL model or mart must declare grain, keys, source dependencies, temporal coverage, and intended consumers. Each notebook should contain purpose, inputs, reproducible configuration, analysis, checks, conclusions, and limitations.

## 8. Progress tracker

Status vocabulary: `Complete`, `In progress`, `Next`, `Planned`, `Blocked`, `Deferred`. Mark complete only when the completion gate has supporting evidence.

| Phase | Status as of 2026-09-28 | Evidence / remaining work |
|---|---|---|
| 0 — Git and setup | Complete | Existing clone, ignore rules, charter, local commits; prior successful push |
| Project continuity | Complete | Root master plan and AGENTS.md saved; Codex local project kkbox-analytics verified to point to the existing repository on 2026-09-25 |
| 1 — Data audit | In progress | User-run full-data checks saved in notebook; notebook reorganized for review. Test-user audit and transaction coverage remain pending; clean-kernel rerun not yet verified. |
| 2 — PostgreSQL / pgAdmin | Planned | Schema, ingestion, relationships, SQL checks |
| 3 — Definitions / product analytics | Planned | Population/time contracts, cohorts and descriptive analysis |
| 4 — Databricks | Planned | Audit-driven scale decision; Bronze/Silver/Gold |
| 5 — Snowflake | Planned | Curated serving marts and reconciliation |
| 6 — Power BI | Planned | Executive dashboard and validated measures |
| 7 — Tableau | Planned | Complementary exploration/storytelling |
| 8 — Predictive modeling | Planned | Baselines, time-aware validation, leakage controls |
| 9 — Recommendations / experiments | Planned | Evidence-backed proposals and experiment design |
| 10 — Final portfolio | Planned | README, visuals, case study, reproducibility review |

### Exact next step

> **Superseded 2026-10-02:** the audit restarted on the complete dataset; see "At a glance" at the top for the current next action. The text below is the earlier (2026-09-28) state, kept for history.

**Wait for user confirmation of the reorganized `notebooks/01_data_audit.ipynb`.**

1. Review the source introduction, training/test sections, and structured table audits.
2. Obtain explicit approval before adding any analysis code. No additional checks were added during organization.
3. After confirmation, guide the user through any agreed remaining checks and a clean-kernel run in VS Code.
4. Reconcile the audit report, dictionary, and issue register with the final notebook before closing Phase 1; those companion documents still reflect initialization.

The user performs this project step by step in VS Code Jupyter. Provide guidance by default; edit or execute analysis only when explicitly requested. Do not advance to modeling or cloud work during this review.

### Open decisions and dependencies

| Item | When to resolve | Current state |
|---|---|---|
| Raw file availability, versions, sizes, and date spans | Phase 1 | Five CSV files now available. Saved notebook outputs establish observed schemas and date spans; official source/version semantics still require confirmation. |
| Official label definition and business measurement window | Phases 1–3 | Must be documented from the selected data/version |
| Relational keys, grain, deduplication and date-treatment rules | Phases 1–2 | Audit-dependent |
| Databricks and Snowflake access, compute limits, and budget | Before cloud phases | Unverified; no paid resources provisioned by this plan |
| Power BI authoring route and Tableau availability | Before dashboards | Unverified |
| Feature windows and temporal holdout feasibility | Before modeling | Data-coverage dependent |
| Final sharing format and permitted data redistribution | Before publishing | Confirm source terms; prefer code and aggregate findings |

## 9. Decision and update log

| Date | Decision | Reason / evidence |
|---|---|---|
| 2026-09-25 | Use the existing Git repository as the development workspace | Local repository and initial setup already exist |
| 2026-09-25 | Maintain this root-level master plan as canonical context | Keep accepted decisions and progress with the implementation |
| 2026-09-25 | Develop an end-to-end retention analytics case study | User's agreed portfolio and learning objective |
| 2026-09-25 | Introduce tools progressively; descriptive analysis precedes prediction | Preserve a coherent business story and verified data contracts |
| 2026-09-25 | Start with `notebooks/01_data_audit.ipynb` | Agreed next deliverable; audit work has not been claimed complete |
| 2026-10-02 | Public README uses a five-layer architecture: (1) data quality and preparation — Python/pandas/Parquet; (2) relational analytics — PostgreSQL; (3) behavioral data engineering — Databricks/PySpark; (4) cloud analytics serving — Snowflake; (5) BI and decision support — Power BI/Tableau. Fabric goes under a separate "Extension / Additional Platform Exploration" section, only after the main pipeline is complete. DuckDB, pgAdmin, Parquet, GitHub CLI, and Homebrew are supporting tools and are not featured in the architecture. The internal 10-phase roadmap is unchanged. | Keep the public story simple (raw → clean → modeled → behavioral features → warehouse → dashboard → decision). Every platform needs one-sentence rationale and a minimal demonstrable artifact; a platform without an artifact is not listed in the README or resume. |
| 2026-10-02 | Adopt a simplified six-stage roadmap (A–F) with one headline question, four collapsed questions, and per-stage time caps (~10 weeks). Tableau and Fabric become optional extensions. Cutoff and feature windows are fixed in stage A. Detailed 10-phase plan retained as internal reference. | The goal is to demonstrate capability to hiring managers; a shorter, question-driven path avoids a tool tour and avoids rework between audit and feature engineering. |
| 2026-10-05 | Record the official dataset description in `docs/source_dataset_notes.md` (documented release map, label definition, field notes). Official windows: `train` = February 2017 expirations, `train_v2` = March 2017, `sample_submission_zero` = original March test set, `sample_submission_v2` = April 2017 test (labels not public). | The user supplied the Kaggle data description. Documented claims stay labeled as documented until verified from local transactions. |
| 2026-10-05 | Remove the superseded v2-only audit scripts `src/data_audit.py`, `src/audit_keys.py` and `tests/test_data_audit.py` (never committed; a copy was kept outside the repository). The notebook uses `src/audit_checks.py` and `src/audit_display.py` only. | The old scripts cover only the v2 files, hard-code file names, and are replaced by the DuckDB checks that cover v1 and v2; keeping them would be redundant and misleading in the portfolio. |
| 2026-10-05 | `CLAUDE.md` and `AGENTS.md` stay local only: they are git-ignored and are never committed or pushed (standing instruction). The three unpushed commits of branch `phase1-data-audit` were recreated without them. | The files are private working instructions for AI assistants, not part of the portfolio. |
| 2026-10-06 | Remove `PROJECT_PLAN.md` from the repository. | It is the original charter and is superseded by this master plan; keeping both duplicated content on the public repository. It remains available in the Git history. |
| 2026-10-02 | Phase 1 audit restarts on the complete dataset (v1 and v2 files). Audit covers every file, including the 30.51 GB `user_logs.csv`, stored on an external SSD. Large CSVs are converted once to text-typed Parquet (`src/csv_to_parquet.py`) and audited with DuckDB. Earlier audit outputs (v2 files only) are not full-data evidence. | Earlier audit used only v2 files; `transactions_v2` (115 MB) vs `transactions.csv` (1.73 GB) suggests v2 is not the complete history. A full audit must cover all releases and their relationship. |

At the end of a meaningful work session, update the last-updated date, affected phase status, artifact paths, validation evidence, open blockers, decisions, and exact next action. Use the following compact entry format:

```text
Date:
Phase and status:
Changes / artifacts:
Validation performed and results:
Findings versus hypotheses:
Decisions and rationale:
Blockers / dependencies:
Next action:
Commit or pull request, if created:
```

Do not automatically mark planned tasks complete or describe an unexecuted notebook as verified. If later evidence changes the plan, record the reason and update the relevant sections rather than maintaining contradictory parallel plans.

### 2026-09-28 — Audit initialization

- Phase and status: Phase 1 in progress; dataset checks await source files.
- Changes / artifacts: `notebooks/01_data_audit.ipynb`, `requirements.txt`, `reports/data_audit.md`, `docs/data_dictionary.md`, `reports/data_quality_issues.md`.
- Validation performed and results: All three notebook code cells executed sequentially with Python 3.12.14 / pandas 2.2.3 against the empty raw directory; empty-inventory and no-profile assertions passed. This was not a Jupyter kernel execution or validation on actual KKBox records.
- Findings versus hypotheses: No source files in the repository raw directory. All record-level quality concerns remain unverified.
- Decisions and rationale: Start with a read-only inventory and a 10,000-row CSV prefix profile. Treat every prefix result as sample-only; no automatic cleaning or merging of releases.
- Blockers / dependencies: Raw-data location requested. Local default Python lacks pandas/Jupyter; validation used an existing bundled runtime. No environment was installed or changed.
- Next action: Obtain source path, inspect files/releases, run prefix profile, and implement appropriately bounded full-data checks.
- Commit or pull request: None created.

### 2026-09-28 — User-led audit and notebook organization

- Phase and status: Phase 1 in progress; organization complete, awaiting user confirmation.
- Changes / artifacts: Reorganized `notebooks/01_data_audit.ipynb` into source overview, training/test-user files, members, transactions, logs, and conclusions. Preserved all 49 nonempty code cells and their outputs unchanged; removed one empty code cell.
- Validation: JSON structure, Python syntax, cell-level name dependencies, and exact code/output preservation checked. No full-data or fresh-kernel rerun; existing outputs are user-run evidence.
- Findings: Corrected the transaction summary to 5,106 total early-expiration rows, including 5,104 cancellation rows and 2 others. Existing notebook already contains transaction missingness and binary-flag checks.
- Decisions: No additional code without approval. Test-user section is introduction/status only because no corresponding audit code exists. Official playback-bin boundaries are not inferred from field names.
- Remaining work: Test-user audit, training-user transaction coverage if approved, clean-kernel validation, and reconciliation of companion documentation. These are not claimed complete.
- Next action: Wait for user confirmation; maintain the user's step-by-step learning workflow.
- Commit or pull request: None.

### 2026-09-28 — Requested test-user audit and findings revision

- User explicitly authorized the sample-submission audit and targeted notebook edits; await approval after delivery.
- Added and sequentially executed three test-user cells: 907,471 rows, two columns, no missing/duplicate IDs, all example predictions zero. 801,490 test IDs overlap training (88.32%); overlap alone is not leakage evidence.
- Removed the requested duplicate-member preview and its stale output. Added gender NaN context and the effect of removing unmatched training users. Reorganized table findings into evidence, impact, and decisions.
- Other analysis code preserved; no full-notebook rerun. Linked reference chat could not be fetched, so its content was not incorporated.
- Test-user basic audit is now implemented; cross-table coverage and official windows remain open. Next action: wait for user approval, not further analysis.

### 2026-09-28 — Supplied field definitions and Scala reference

- Read the user-provided `WSDMChurnLabeller.scala`; did not execute it. Added notebook Section 1.2 with field definitions, NTD units, member schema discrepancy, and exact implemented label boundary (gap <30 renewal; >=30 churn).
- Documented cancellation-adjusted expiration, deterministic same-day sorting, and the difference between demonstration date constants and actual train/test windows. Supplied member `expiration_date` is absent locally; illustrative malformed years are not dataset findings.
- Validation: All notebook code cells and outputs unchanged. No label regeneration, new analysis code, or full rerun.
- Next action: Wait for user confirmation; exact local label windows remain unresolved.

### 2026-09-28 — Churn methodology documentation

- Artifacts: Added the concise README Churn Definition section and `docs/churn_definition.md`; preserved other README content.
- Evidence: Inspected the uploaded official Scala labeller and the complete competition examples supplied in the reference conversation. Documented the strict day-30 boundary, historical candidate selection, same-day ordering, cancellation adjustments, and example date corrections.
- Validation: Documentation reviewed against source functions; no Spark execution or label reconstruction. Comparison with `train_v2.is_churn` remains planned, with local release/window alignment and outcome coverage unresolved.
- Status: Definition documentation complete; Phase 3 analytics and empirical label validation remain planned. No analysis code or data changed.
- Next action: Await the user's audit review; resolve local train/test temporal contracts before any authorized label-validation work.
- Commit or push: None.

### 2026-10-02 — Public architecture and platform-artifact decision

- Date: 2026-10-02
- Phase and status: No phase change; Phase 1 remains in progress.
- Changes / artifacts: Documentation only. Added the decision-log row and a pointer under Section 5. No code, notebook, or data changed.
- Validation performed and results: None (documentation decision).
- Findings versus hypotheses: No new findings.
- Decisions and rationale: Five-layer public architecture, Fabric as a post-pipeline extension, DuckDB/pgAdmin/Parquet/GitHub CLI/Homebrew as supporting tools. Minimum demonstrable artifacts per platform:
  - Python/pandas/Parquet: audit notebook, issue register (finding → decision → treatment → validation), Parquet conversion script.
  - PostgreSQL: DDL with key/FK coverage checks, ER diagram, 3–5 analysis SQL files, source-count reconciliation.
  - Databricks/PySpark: Bronze/Silver/Gold exports, one user×cutoff Gold feature table, comparison with a pandas sample.
  - Snowflake: three marts (subscriber snapshot, cohort retention, engagement trend) with declared grain/keys/refresh, plus reconciliation SQL.
  - Power BI: `.pbix`, screenshots, measure definitions. Tableau: one workbook with 2–3 views that do not duplicate Power BI; first to cut if time is short.
  - Fabric: one Lakehouse and one notebook, only after the main pipeline is complete.
- Blockers / dependencies: Databricks, Snowflake, and Power BI environments and quotas remain unverified.
- Next action: Unchanged — wait for the user's confirmation of `notebooks/01_data_audit.ipynb`. README is not rewritten until audit findings exist.
- Commit or pull request: None.

### 2026-10-02 — Simplified roadmap adopted

- Date: 2026-10-02
- Phase and status: No phase change; stage A (Phase 1) remains in progress.
- Changes / artifacts: Added the "Simplified public roadmap" subsection to Section 3 and a decision-log row. Documentation only; no code, notebook, or data changed.
- Validation performed and results: None (documentation decision).
- Findings versus hypotheses: The claim that supplied labels cover only one or two expiration months is a hypothesis from general knowledge of the competition and the labeller design, not verified locally.
- Decisions and rationale: See decision log.
- Blockers / dependencies: Cloud environments unverified.
- Next action: Unchanged — wait for the user's confirmation of `notebooks/01_data_audit.ipynb`; then verify the expiration-window distribution of `train_v2` users from `transactions_v2` as a stage A check.
- Commit or pull request: None.

### 2026-10-02 — Full-dataset audit restart

- Date: 2026-10-02
- Phase and status: Stage A / Phase 1 in progress; audit restarts on the complete dataset.
- Changes / artifacts: Added `src/csv_to_parquet.py` (written, syntax-checked, not executed). Documentation updated. Full dataset inventory: v1 `train`, `transactions`, `user_logs`; v2 `train_v2`, `transactions_v2`, `user_logs_v2`; `members_v3`; `sample_submission_v2`, `sample_submission_zero`; `WSDMChurnLabeller.scala`. `user_logs.csv` (30.51 GB) extracted on an external SSD. Environment: 16 GB RAM, DuckDB 1.5.4, pyarrow 19.0.0 available.
- Validation performed and results: Syntax check only. No conversion or audit run yet; earlier v2-only outputs remain user-run evidence for v2 files only.
- Findings versus hypotheses: Hypothesis (unverified): v2 transactions are a short recent extract, not full history; v1 and v2 label files cover different expiration months.
- Decisions and rationale: See decision log. Raw files stay unchanged; Parquet columns are text-typed to avoid silent type coercion; paths are passed as arguments, not committed.
- Blockers / dependencies: None known.
- Next action: User runs the conversion for `user_logs.csv` and `user_logs_v2.csv` (row-count check enforced), then re-run the audit per release, check the v1/v2 relationship, and verify the label windows of `train` and `train_v2`.
- Commit or pull request: None.

### 2026-10-02 — Full-data log audit and reusable audit module

- Date: 2026-10-02
- Phase and status: Stage A / Phase 1 in progress; user logs audited on the complete dataset, other tables still to be re-run on v1 + v2.
- Changes / artifacts: `src/csv_to_parquet.py` executed by the user (row counts matched: v1 392,106,543; v2 18,396,362). New `src/audit_checks.py` (DuckDB-based reusable checks: table_summary, missingness, key_uniqueness, exact_duplicates, value_counts_pct, numeric_range, date_validity, monthly_coverage, flag_counts, coverage) and `tests/test_audit_checks.py`. Notebook section 5 (user logs) rebuilt by the user with DuckDB; the notebook has not been refactored to call `src/audit_checks.py` yet.
- Validation performed and results: 13 unit tests pass (new + existing). Regression of the new functions against the earlier v2-only notebook results: 26/26 values reproduced (e.g., train_v2 970,960 rows and 8.99% label rate; 801,490 test users in train = 88.32%; 5,106 early-expiry transactions, 5,104 cancellations; 754,551 train users with v2 logs = 77.71%). Regression script was run ad hoc and is not committed.
- Findings (full data, user logs): v1 covers 2015-01-01 to 2017-02-28 (5,234,111 users); v2 covers 2017-03-01 to 2017-03-31 (1,103,894 users); 27 consecutive months, no gaps or overlap. No duplicate (msno, date) key in either release. `msno` always 44 characters with no padding. No missing or non-numeric values in the numeric columns. `total_secs` anomalies: v1 61,493 negative, 137,007 between 1 and 7 days, 5,921 between 7 days and 1e12, 65 above 1e12 (about 0.052% of rows); v2 4,200 above one day (about 0.023%); anomalies are spread over all v1 months, not one event. Source values untouched; treatment is planned for the Silver layer (null plus flag, original kept) pending the user's decision.
- Hypotheses (unverified): v2 logs are a one-month continuation of v1; v1 and v2 label files cover different expiration months; `transactions_v2` is a short extract rather than full history.
- Decisions and rationale: DuckDB is the single audit engine (works on Parquet, CSV, and DataFrames); pandas is used for display and case analysis. Old `src/data_audit.py` and `src/audit_keys.py` are kept until the notebook uses the new module.
- Blockers / dependencies: Notebook sections 2-4 and 5.5-5.6 still use v2 files only.
- Next action: Re-run sections 2-4 for v1 + v2 via `src/audit_checks.py`; compare `train` vs `train_v2` (overlap, label changes); check training-user coverage in v1 + v2 logs; verify label windows from transactions.
- Commit or pull request: None.

### 2026-10-04 — Release relationships and notebook refactor plan

- Date: 2026-10-04
- Phase and status: Stage A / Phase 1 in progress.
- Changes / artifacts: No new code files. Drafted v1 + v2 notebook cells (shared setup, merged views `train_all` / `tx_all` / `logs_all`, section 2.7 train and test-user checks, section 4.9 transactions v1 vs v2). Nothing from 2026-10-02 or 2026-10-04 has been committed to Git yet; the first commit is planned for 2026-10-05.
- Validation performed and results: User ran the train overlap query (full data). Users present in both `train` (v1) and `train_v2` (v2): 881,701. Label transitions (v1 → v2): 0→0 824,659; 0→1 40,721; 1→0 5,269; 1→1 11,052. Derived: 4.71% of v1-retained overlap users are churn in v2; 67.7% of v1-churned overlap users are churn again in v2. Overlap is about 90.8% of `train_v2` rows. Results for sections 2.7.1, 2.7.2, 2.7.4 and 4.9 are not yet recorded.
- Findings versus hypotheses: Verified (full data): the overlap and transition counts above. Hypotheses (unverified): `train` and `train_v2` cover different expiration windows (likely February and March 2017); v1-churned users returning in v2 are re-subscribers after churn; `transactions_v2` overlaps `transactions` and needs de-duplication before merging.
- Decisions and rationale: Merge rules by table. `user_logs`: union with a `release` column (disjoint months, no duplicate keys, verified). `train`: no de-duplication; keep both observations in a long table with `release`, because they are different windows. `transactions`: decide after the section 4.9 overlap check. `members_v3`, sample submissions: not merged. Audit-phase merging uses views only; raw files and Parquet are never modified. A "Release map" table (per table: v1 range, v2 range, relationship, merge rule, evidence) will be written once in the notebook (new section 1.3), mirrored in `docs/data_dictionary.md`, with a 4–5 row version in the README Data section. Notebook workflow: replace the older inline audit code with calls to `src/audit_checks.py` (the user runs the notebook; guidance by default).
- Blockers / dependencies: Section 2.7 and 4.9 outputs pending from the user. Modeling note: about 90.8% of `train_v2` users also appear in `train`; a v1-train / v2-validation split must document this overlap and use only pre-cutoff features.
- Next action: see "At a glance".
- Commit or pull request: None.

### 2026-10-05 — Official dataset description recorded; v1 + v2 results confirmed

- Date: 2026-10-05
- Phase and status: Stage A / Phase 1 in progress.
- Changes / artifacts: Added `docs/source_dataset_notes.md` (documented release map, label definition, field notes, implications, verification list) and a pointer in `docs/data_dictionary.md`. Notebook now contains sections 2.7 (train v1 + v2 and test users) and 4.9 (transactions v1 vs v2), run by the user.
- Validation performed and results (full data, user-run): `train_v1` 992,931 rows (6.39% label rate); `train_v2` 970,960 rows (8.99%); no duplicate or missing keys; 881,701 users in both. `sample_submission_v2` 907,471 users, 88.32% in `train_v2`, 88.26% in `train_v1`; `sample_submission_zero` 970,960 users. `transactions.csv` 21,547,746 rows (2015-01-01 to 2017-02-28) and `transactions_v2.csv` 1,431,009 rows (361,187 before March 2017, 1,069,822 in March); zero rows identical across the two; 94.78% of v2 transaction users also appear in v1. `transactions.csv` has `membership_expire_date` as early as 1970-01-01 (count not yet measured). Exploratory read-only check, to be reproduced in notebook section 4.9: 7,249 (user, transaction date) keys appear in both releases, always with a different expiration date.
- Findings versus hypotheses: The February/March windows for `train`/`train_v2` and the March identity of `sample_submission_zero` are now documented by the official description (user-supplied) and consistent with local counts, but not yet verified from transactions. `user_logs_v2` is observed as March-only, whereas the description says the refreshed files contain data until 2017-03-31; the local v2 files behave as increments.
- Decisions and rationale: See decision log. Keep the label tables as observation-level (user × window); derive user-level tables separately with a stated rule. Whether to restrict to users present in both windows is deferred: default is all users per window, with overlap and non-overlap users reported separately. A February-window label is not used as a March-window feature until windows are verified.
- Verified (full data, user-run, 2026-10-05): all 970,960 `sample_submission_zero` users are in `train_v2` (100% match); the two files contain the same user set.
- Blockers / dependencies: Pending output of the extra section 4.9 cell (v2 early transaction rows, shared keys, count of pre-2015 expiration dates in `transactions.csv`).
- Next action: see "At a glance".
- Commit or pull request: None.

### 2026-10-05 (update 2) — Section 2 rewritten on v1 + v2

- Date: 2026-10-05
- Phase and status: Stage A / Phase 1 in progress. Notebook sections 1 and 2 revised; section 3 next.
- Changes / artifacts: New `src/audit_display.py` and `tests/test_audit_display.py`; `CLAUDE.md` rewritten to match the current workflow (DuckDB audit engine, new files, working rules); `requirements.txt` now lists `duckdb`. Setup cell replaced by a shared setup and file inventory; section 2 restructured into 2.1 schema, 2.2 structure and key checks, 2.3 label distribution, 2.4 v1–v2 overlap, 2.5 test rosters, 2.6 findings, with `show()` titles and tables.
- Validation performed and results: 18 unit tests pass. File inventory matches earlier row counts for all nine registered tables. Reviewed outputs (full data): `train_v1` 992,931 and `train_v2` 970,960 rows, unique and complete; label rates 6.39% and 8.99%. `sample_submission_zero` users are exactly the `train_v2` users (100% match). The saved notebook file on disk still showed the older section 2 when checked; the user is to save it.
- Findings versus hypotheses: Unchanged from the earlier entry; the label windows remain documented but not verified from transactions.
- Decisions and rationale: DuckDB computes and pandas presents (`.df()`, pivot, case studies); pandas stays visible for analysis and modeling. Legacy `raw_dir` and `train` stay until sections 3 and 5.6 are rewritten.
- Blockers / dependencies: None.
- Next action: see "At a glance".
- Commit or pull request: None (first daily commit still pending).

### 2026-10-05 (update 3) — Section 3 (members) rewritten and independently verified

- Date: 2026-10-05
- Phase and status: Stage A / Phase 1 in progress; notebook sections 1–3 revised.
- Changes / artifacts: Section 3 of `notebooks/01_data_audit.ipynb` was rewritten on DuckDB (`src/audit_checks.py`, `show()`), written by a parallel Claude session; this session reviewed it without editing the notebook. `src/audit_display.py` now shows tiny non-zero percentages as `<0.01%` (test added; 19 unit tests pass).
- Validation performed and results: All six section 3 code cells were executed headlessly and read-only against the full data without errors, and every number in the 3.7 findings table reproduced: 6,769,473 members, unique and complete `msno`; gender missing 4,429,505 (65.43%); `bd` zero 4,540,215 (67.07%), negative 274, above 100 5,377, range -7,168 to 2,016, within 1–100 2,223,607 (32.85%); 4,388,613 rows (64.83%) with both gender missing and zero age; registration dates 2004-03-26 to 2017-04-29, 154,166 (2.28%) after 2017-02-28 and 55,094 (0.81%) after 2017-03-31; one `registered_via = -1` record; member coverage `train_v1` 877,161 of 992,931 (88.34%), `train_v2` 860,967 of 970,960 (88.67%), `sub_zero` 88.67%, `sub_v2` 795,090 of 907,471 (87.62%); label rate for unmatched vs matched users 5.02% vs 6.57% (`train_v1`) and 5.35% vs 9.46% (`train_v2`); left joins preserve all label rows. Section 3 cells have no saved outputs yet (not run in the notebook kernel). Section 2 outputs in the saved notebook were checked for the transition and coverage numbers.
- Findings versus hypotheses: Verified (full data): the numbers above. Descriptive only: unmatched users have a lower label rate; this does not show that profile completeness affects churn. Open: meaning of zero age and of channel `-1`; demographic treatment rules; temporal eligibility of members.
- Decisions and rationale: Keep all labeled users with a left join; preserve missing gender as an explicit unknown group; preserve raw `bd` and define review flags before any cleaning. Use one editor at a time for the notebook to avoid conflicting edits between sessions.
- Blockers / dependencies: Cell 3 no longer defines the legacy `train` variable that the old section 5.6 uses.
- Next action: see "At a glance".
- Commit or pull request: None (first daily commit still pending).

### 2026-10-05 (update 4) — Section 4 (transactions) rewritten and independently verified

- Date: 2026-10-05
- Phase and status: Stage A / Phase 1 in progress; notebook sections 1–4 revised, section 5.5–5.6 next.
- Changes / artifacts: Section 4 of `notebooks/01_data_audit.ipynb` was rewritten on DuckDB for `transactions.csv` (v1) and `transactions_v2.csv` (v2), 4.1–4.8, by a parallel Claude session; this session reviewed it without editing the notebook. The old 4.9 cells were folded into 4.7.
- Validation performed and results (full data, read-only headless run of all seven code cells, no errors; every figure in the 4.8 table reproduced): v1 21,547,746 rows and 2,363,626 users; v2 1,431,009 rows and 1,197,050 users; no missing values. Exact duplicates: v1 3,339 excess rows, v2 0. Same user and day: 286,404 (v1) and 33,292 (v2) rows beyond the first, up to 48 and 131 rows per key. Flags binary; plan days 0–450; prices 0–2,000. Zero-day plans: v1 870,124 (4.04%), v2 2,218 (0.15%), mostly with a nonzero payment. Expiration before 2015 in v1: 9,840 rows (1,776 on 1970-01-01), none in v2. Expiration before transaction date: v1 153,660 (147,200 cancellations = 17.18% of cancellation rows; 6,460 non-cancellations), v2 5,106 (5,104 cancellations, 2 non-cancellations). Long expiry: largest gap 814 days (v1) and 7,303 days (v2, one member); 19,357 v2 rows above 1,000 days, none in v1. Case member (78 records): 75 of 77 expiry increments equal plan days. Release relationship: 0 identical rows; 94.78% of v2 users also in v1 (48.00% of v1 users in v2); of 361,187 v2 rows dated before March 2017, 9,967 share a (user, date) key with a v1 row; 7,249 keys occur in both releases (42,257 row pairs) and the expiration date differs in every pair.
- Findings versus hypotheses: Verified: the figures above. New observation: the pre-March v2 rows concentrate near the end of the v1 window (128,916 dated February 2017 and 32,871 dated January 2017, together about 44.8% of the 361,187). Hypothesis (unverified): v2 re-extracts or adds late-arriving recent history; the conflicting-key pairs may reflect same-day stacked renewals. Source-notes verification item for pre-2015 expiration dates is now measured.
- Decisions and rationale: Do not drop exact duplicates, same-user-same-day rows, early or distant expiration dates, or zero-day plans in the audit; flag them in the Silver layer. Stack the releases as `tx_all` with a `release` column; a rule for the 7,249 conflicting keys must be defined before sequences are rebuilt (not decided).
- Blockers / dependencies: Section 4 cells have no saved outputs yet (not run in the notebook kernel).
- Next action: see "At a glance".
- Commit or pull request: None (first daily commit still pending).

### 2026-10-05 (update 5) — What `transactions_v2` adds to `transactions` (exploratory, read-only)

- Date: 2026-10-05
- Phase and status: Stage A / Phase 1 in progress.
- Changes / artifacts: None in the repository. Exploratory read-only queries (not yet reproduced in the notebook) prompted by the user's observation that the monthly row counts of v2 before March 2017 are far below v1.
- Validation performed and results (full data, exploratory): The 361,187 v2 rows dated before March 2017 belong to 262,429 users, of whom 234,380 (89.3%) also appear in v1; 167,069 of them (63.7%) have no March 2017 row in v2 at all, so the earlier hypothesis that these rows re-extract history for users active in March is not supported. Relative to the same user's latest earlier v1 transaction date (using the latest expiration date on that date, so the result is reproducible), 227,254 of the 361,187 rows (62.9%) fall inside an active v1 membership period, 92,696 (25.7%) follow a v1 expiration gap, and 41,237 (11.4%) have no earlier or same-day v1 row. An earlier version of this check that picked an arbitrary v1 row when several shared a date gave slightly different, non-reproducible counts (about 62.7% and 25.9%). The pre-March v2 rows skew toward long plans (410-day plans 21% of them versus 0.37% of v1 rows) and non-cancellations (99.04% versus 96.02%). v2 was built around the later populations: all 907,470 of 907,471 `sample_submission_v2` users and 933,578 of 970,960 (96.15%) `train_v2` users have at least one v2 transaction row, while the 167,069 early-only users are mostly outside the label tables (4.35% in `train_v2`, 13.38% in `train_v1`, 15.07% in `sub_v2`).
- Findings versus hypotheses: Verified (exploratory): the counts above. Supported but unproven: `transactions_v2` is March 2017 plus a supplement of older rows that `transactions` lacks, not a plain extension; the pre-March rows are not a re-extract for March-active users. Unknown: why those rows exist (late-arriving records and stacked long-plan purchases are both candidate explanations). Monthly row counts of the two releases are not like-for-like (v1 covers 2,363,626 users; v2 covers 1,197,050).
- Decisions and rationale: Rebuilding expiration chains or user history features needs v1 and v2 together (`tx_all`); neither release alone is a complete history. The rule for conflicting (user, date) keys remains to be defined. Reproduce these diagnostics in notebook section 4.7 before citing them as audit evidence.
- Blockers / dependencies: The notebook's section 4.8 "Open" item still states the March-active re-extract hypothesis; it should be revised.
- Next action: see "At a glance".
- Commit or pull request: None.

### 2026-10-05 (update 5b) — Are the conflicting transaction keys complementary? (exploratory, read-only)

- Date: 2026-10-05
- Phase and status: Stage A / Phase 1 in progress.
- Changes / artifacts: None in the repository; exploratory queries, not yet reproduced in the notebook.
- Validation performed and results (full data, exploratory): The 7,249 (user, transaction date) keys present in both releases hold 9,711 v1 rows and 9,967 v2 rows (about 1.3–1.4 rows per key per side), so the 42,257 row pairs reported earlier are cross-combinations, not one-to-one copies. In 14,179 of 14,498 key-and-release groups (97.8%) all rows share one plan duration, amount and cancel flag, i.e. they look like repeated purchases of the same plan with different expiration dates. Sorting the rows of each key by expiration date, the expiration increment equals the plan duration for 92.3% of consecutive rows from the same release (4,779 of 5,180) and for 63.6% of consecutive rows from different releases (4,612 of 7,249).
- Per-field differences across the 42,257 v1–v2 row pairs of the shared keys: expiration date 100%; amount paid 9.12%; list price 8.96%; payment method 7.38%; plan days 6.94%; auto-renew 4.01%; cancel flag 3.96%; 37,856 pairs (89.59%) differ only in the expiration date.
- Findings versus hypotheses: Consistent with, but not proof of, v2 supplying additional links of same-day stacked purchases that v1 lacks; about 36% of cross-release adjacent pairs do not follow the plan-duration increment (possible missing rows or revised expiration dates). Whether v1 plus v2 is a complete history remains unverified.
- Decisions and rationale: Merging means stacking both releases (`tx_all`, release column kept), never overwriting or de-duplicating on user and date. The physical merged table is built in the staging/Silver step with the conflicting-key handling documented; the audit uses the view only.
- Blockers / dependencies: Reproduce these diagnostics in notebook section 4.7 before citing them as audit evidence.
- Next action: see "At a glance".
- Commit or pull request: None.

### 2026-10-05 (update 6) — Section 5 (user logs) redrafted and verified

- Date: 2026-10-05
- Phase and status: Stage A / Phase 1 in progress.
- Changes / artifacts: Drafted new cells for notebook section 5 (5.1–5.7) on `src/audit_checks.py` and `show()`, replacing the older raw-SQL and v2-only pandas cells; not yet pasted into the notebook by the user. In the same environment the system `python3` had no DuckDB; the project's Anaconda interpreter was used.
- Validation performed and results (full data, read-only headless run of all drafted cells): v1 392,106,543 rows, 5,234,111 users, 2015-01-01 to 2017-02-28; v2 18,396,362 rows, 1,103,894 users, 2017-03-01 to 2017-03-31; no missing or invalid values; (`msno`, `date`) unique in each release; 790 distinct dates in v1 and 31 in v2 with none in both, so keys cannot repeat across releases; 27 consecutive months; `msno` always 44 characters. `total_secs`: v1 61,493 negative rows (29,929 users), 137,007 rows between one and seven days, 5,921 between seven days and 1e12, 65 above 1e12; v2 4,200 rows above one day; anomalies occur in every month. User overlap: 998,583 users in both releases (90.46% of v2 users, 19.08% of v1 users). Coverage of users with at least one log row (v1 or v2): `train_v1` 87.76%, `train_v2` and `sub_zero` 88.07%, `sub_v2` 86.87%; v2 only: 74.51%, 77.71%, 77.71%, 77.16%. The v2-only figure for `train_v2` (754,551 users) reproduces the earlier v2-only result.
- Findings versus hypotheses: Verified (full data): all figures above. Open: whether users without logs are the same as users without member profiles; plausibility of extreme play counts; thresholds and treatment for `total_secs`.
- Decisions and rationale: A direct global group-by of (`msno`, `date`) over both releases exceeded the 8 GB memory limit; cross-release uniqueness is instead shown by disjoint date sets plus within-release uniqueness. Treatment of `total_secs` anomalies (flag and null in Silver, original kept) remains to be confirmed.
- Blockers / dependencies: None.
- Next action: see "At a glance".
- Commit or pull request: None.

### 2026-10-05 (update 7) — Companion documents rewritten from the full-data audit

- Date: 2026-10-05
- Phase and status: Stage A / Phase 1; the audit analysis is complete, closing items remain.
- Changes / artifacts: Rewrote `reports/data_audit.md` (scope, release map, findings by table, decisions, open items, reproduction), `reports/data_quality_issues.md` (register DQ-001 to DQ-019 with evidence, severity, risk, planned treatment, status), and `docs/data_dictionary.md` (observed schema, grain, ranges, documented definitions). Updated `CLAUDE.md`. The saved notebook (19:13) had 30 of 30 code cells executed (counts 75–104, consecutive) with no errors; the 4.8 and 5.x revisions are in it.
- Validation performed and results: Every figure in the documents was taken from the verified notebook outputs or headless full-data runs recorded in the entries above. While writing, one wording error was found and fixed (an unfinished figure for `total_secs` rows above one day: 142,993 in v1, 4,200 in v2) and one over-claim removed (identifier length and padding were checked only for user logs, not for label tables or members).
- Findings versus hypotheses: Unchanged; hypotheses are marked in the register (supplement role of the pre-March transaction rows, complementary shared keys, label windows).
- Decisions and rationale: All data-quality treatments are planned for the Silver layer and none has been applied; the register is the traceable record (finding, decision, treatment, validation).
- Blockers / dependencies: The notebook is missing the "which fields differ" cell in 4.7.1 (the 89.59% figure in 4.8 and the register lacks a notebook output) and the Release map (1.3); the last run was sequential but the kernel was not restarted.
- Next action: see "At a glance".
- Commit or pull request: None (first daily commit still pending).

### 2026-10-05 (update 8) — Notebook run confirmed; old audit scripts removed

- Date: 2026-10-05
- Phase and status: Stage A / Phase 1: the data audit is complete on the full dataset; closing items are listed below.
- Changes / artifacts: Confirmed the saved notebook (19:29): 69 cells, 31 of 31 code cells executed with counts 1 to 31 in file order (fresh kernel), no errors, Release map (1.3) present, "which fields differ" cell present with its outputs (89.59%, 37,856), no stale text. Deleted `src/data_audit.py`, `src/audit_keys.py`, `tests/test_data_audit.py`; updated `CLAUDE.md` and `reports/data_audit.md` accordingly. 17 unit tests pass.
- Validation performed and results: Notebook outputs contain every key figure recorded in the register; tests rerun after deletion.
- Findings versus hypotheses: Unchanged.
- Decisions and rationale: See decision log (old scripts removed).
- Blockers / dependencies: Before the first commit, replace the hard-coded external-drive paths in the notebook setup cell (cell 3) with environment-variable settings, remove the five raw user identifiers shown in the section 3.1 preview output (cell 21), and scrub the two absolute local paths in this plan (clone path in Section 2; interpreter path in update 6).
- Next action: see "At a glance".
- Commit or pull request: None (first daily commit pending the items above).

### 2026-10-05 (update 9) — Phase 1 audit committed on branch `phase1-data-audit`

- Date: 2026-10-05
- Phase and status: Stage A / Phase 1: audit analysis and documentation complete and committed; Stage A definitions next.
- Changes / artifacts: Created branch `phase1-data-audit` from `main` and made three commits: project plan and dataset notes; reusable DuckDB audit checks, display helper, Parquet converter, tests, requirements, example machine settings; audit notebook, audit report, issue register, data dictionary. The commits were recreated once so that `CLAUDE.md` and `AGENTS.md` (local only) are not in the history. Machine-specific paths now live in the git-ignored `local_settings.py` (an example file is committed). Commit messages carry no attribution lines (standing instruction).
- Validation performed and results: Before committing, the staged content was scanned for machine paths, 44-character user identifiers, and credential-like text (none found); the notebook was re-run top to bottom after the path and identifier fixes (31 of 31 cells executed, no errors); 17 unit tests passed. Working tree clean after the commits (data, `local_settings.py`, `.DS_Store`, caches ignored).
- Findings versus hypotheses: Unchanged.
- Decisions and rationale: Work stays on a branch until the user decides on merging; nothing was pushed to GitHub.
- Blockers / dependencies: None.
- Next action: see "At a glance".
- Commit or pull request: Branch `phase1-data-audit` with three commits, pushed to GitHub on 2026-10-05 (no pull request opened, `main` unchanged). This plan update is uncommitted and goes into the next commit.

### 2026-10-05 (update 10) — Label windows and cutoffs checked against transactions (exploratory)

- Date: 2026-10-05
- Phase and status: Stage A definitions in progress (label-window verification started); README drafted (uncommitted).
- Changes / artifacts: Drafted a new `README.md` (status table, audit findings, data and reproduction steps, repository map, limits; numbers checked: about 444 million rows audited, about 34 GB of raw data). Translated the official `WSDMChurnLabeller.scala` into read-only DuckDB queries (scratch scripts, not in the repository) to rebuild labels from `tx_v1` plus `tx_v2` and compare them with `train.csv` and `train_v2.csv`. Key reading of the labeller: the rule needs transactions after the cutoff, so the February window can only be labeled with the March rows in `transactions_v2`; `transactions.csv` alone ends on 2017-02-28.
- Validation performed and results (full data, exploratory, not yet in a notebook): (1) Labeller rule (last expiration inside the target month), cutoff at the end of the previous month, full history from 2015: February window rebuilds 879,537 users, 879,478 of them in `train.csv` (88.57% of its 992,931 users; 59 extra) with 98.36% label agreement; March window rebuilds 886,500 users, 862,158 in `train_v2.csv` (88.79% of 970,960; 24,342 extra) with 95.73% agreement. (2) Cutoff scan: coverage of the official users grows as the cutoff moves toward the end of the previous month (February window: 13.5% at 2017-01-01, 79.1% at 2017-01-25, 88.57% at 2017-01-31, 86.69% at 2017-02-01; March window: 12.58% at 2017-02-01, 78.72% at 2017-02-25, 88.79% at 2017-02-28, 88.67% at 2017-03-01); the March extras fall from 24,342 to 7,066 at a 2017-03-01 cutoff while agreement drops to 94.84%. (3) Population rule: where the labeller rule leaves about 11% of the official users unplaced (for example 92,868 `train.csv` users whose last expiration lies after February, churn label rate 6.87%, 18,490 whose last expiration lies before it), the looser rule "any transaction up to the cutoff expires in the target month" covers 99.06% of `train.csv` users (597 extra) and 98.68% of `train_v2.csv` users (33,413 extra). (4) Labels follow the rule on the rebuilt users with 95.7–98.4% agreement, not exactly.
- Findings versus hypotheses: Strongly supported (exploratory): `train.csv` is the February 2017 expiration window and `train_v2.csv` the March window, with the prediction cutoff at the end of the previous month. Hypothesis: the official training sample selects users with any expiration inside the target month, not only the last expiration as in the demonstration script; the treatment of early renewers and the 24,342 March extras is unexplained. Not an exact reproduction of the official labels.
- Decisions and rationale: Implement the labeller as tested reusable code and document the cutoff and population choices in a new notebook before using any label-derived analysis; treat the loose population rule as the working hypothesis until the unexplained groups are examined.
- Blockers / dependencies: None.
- Next action: see "At a glance".
- Commit or pull request: None (README and plan changes uncommitted; the audit branch is pushed, not merged).

### 2026-10-06 (update 11) — Cross-month analysis agreed; right-censoring of reconstructed labels

- Date: 2026-10-06
- Phase and status: Stage A definitions / start of Stage B; the goal for the next days is a presentable public repository first, refinements afterwards.
- Changes / artifacts: None in the repository. Exploratory read-only check of where rebuilt labels disagree with the official ones.
- Validation performed and results (full data, exploratory): Among users present in both the rebuilt and the official label sets, the share of users rebuilt as churn but labeled renewal by the official file rises with the expiration day in the March window (0.13% for days 1–7, 0.42% for days 8–15, 0.86% for days 16–23, 2.22% from day 24) but stays at 0.01–0.03% in the February window. Transactions end on 2017-03-31, so a March expiration late in the month can renew in April without the renewal being observable.
- Findings versus hypotheses: Consistent with right-censoring (inference, not proof): labels rebuilt from the supplied transactions are reliable only when the 30-day outcome window ends inside the data, i.e. for target months up to February 2017; the March 2017 cohort must use the official `train_v2` labels.
- Decisions and rationale: The user wants cross-month (cohort) analysis to show breadth. Plan: implement the labeller as tested reusable code, rebuild monthly cohorts after a burn-in period (history starts 2015-01-01 and plans last up to 450 days) up to February 2017, add March 2017 from the official labels, and use the cohorts for churn-over-time, cohort retention, and rolling time-ordered validation. Sequence: first publish the repository (README, merge to `main`), then build the cross-month work.
- Blockers / dependencies: None.
- Next action: see "At a glance".
- Commit or pull request: None.

### 2026-10-06 (update 12) — Label rebuild implemented and monthly cohorts computed (exploratory)

- Date: 2026-10-06
- Phase and status: Stage A definitions / start of the cross-month analysis (code written, notebook not yet written).
- Changes / artifacts: Added `src/churn_labels.py` (`month_window`, `rebuild_labels`, `rebuild_months`: the official labeller rules in DuckDB, cutoff at the end of the previous month) and `tests/test_churn_labels.py` (the three official examples from `docs/churn_definition.md`, the 29/30-day boundary, cancellations that move the expiration earlier, same-day ordering, no later transaction, history start, month windows). Removed `PROJECT_PLAN.md` from the repository earlier the same day. Code and tests are uncommitted.
- Validation performed and results: 29 unit tests pass (existing and new). On the full data the module reproduces the earlier exploratory results exactly: the February 2017 window rebuilds 879,537 users (879,478 in `train.csv`, 98.36% label agreement) and the March 2017 window 886,500 users (862,158 in `train_v2.csv`, 95.73%). Monthly cohorts for 2015-02 to 2017-03 were rebuilt (26 months, 17,869,628 user-month rows, 169 seconds). Cohort size grows from about 393 thousand users (2015-02) to about 880 thousand (2017-02); the churn label rate varies from 3.7% to 19.2%. Rebuilt rates are lower than the official ones because the rebuilt population is smaller (February 2017: 3.95% against 6.39%; March 2017: 4.93% against 8.99%), so the two must not be compared directly.
- Findings versus hypotheses: Verified (exploratory): two spike months are driven by batches of users who share an expiration day. In 2015-04, 92,575 users expire on April 30 with a 79.8% churn rate, and 15.3% of that month's candidates have a list price of zero (0.0% in March 2015). In 2016-03 several expiration days (25, 29, 30, 1, 28) show 35–50% churn. Hypothesis (not verified): promotion or free-trial style cohorts that churn at high rates; the cause is unknown.
- Decisions and rationale: Use target months 2015-07 to 2017-02 (20 months, rebuilt) plus 2017-03 (official `train_v2` labels) as the analysis cohorts; the earlier months stay in charts as a shaded burn-in period (history starts 2015-01-01 and long plans are invisible until renewed). The choice of 2015-07 is a judgment call. Report cohort mix (plan type, zero-price plans) next to churn over time.
- Blockers / dependencies: None.
- Next action: write the cohort notebook (`02_...`): monthly cohorts, churn over time, the spike investigation, comparison with the official labels, retention view; then update the README.
- Commit or pull request: None.

### 2026-10-06 (update 12b) — Why the rebuilt population and churn rate differ from the official labels (exploratory)

- Date: 2026-10-06
- Phase and status: Stage A definitions.
- Changes / artifacts: None in the repository (read-only diagnostics).
- Validation performed and results (full data, exploratory): (1) Population: the 113,453 `train.csv` users not rebuilt are 2,095 with transactions only after the cutoff, 18,490 whose last expiration lies before February (41.47% churn labels) and 92,868 whose last expiration lies after February (6.87%); together their churn label rate is 12.96% against 5.54% for the 879,478 rebuilt users in `train.csv`. For `train_v2.csv` the 108,802 users not rebuilt (2,524 / 20,813 / 85,465) have a 22.71% churn label rate against 7.26% for the 862,158 rebuilt users. The looser population rule "any transaction up to the cutoff expires in the target month" covers 99.06% (February) and 98.68% (March) of the official users. (2) Labels inside the shared users: the official file marks more users as churn than the rebuild: 14,193 in February (the rebuild says renewed) and 28,373 in March, against 199 and 8,438 in the other direction. About 70% of the February group (9,871 of 14,193) are users whose first later non-cancellation transaction was dated before their expiration (negative gap, early renewal); among all early renewers 11.00% (February) and 14.17% (March) are churn in the official file, against 0.2–2% for renewals within 0 to 29 days after expiration. Renewals with a zero payment explain only a small part (4.5% and 5.6% of those groups against 0.2% and 0.1% in the agreeing group). (3) The rebuilt churn rate of the shared users is 3.95% (February) and 4.93% (March) while the official labels of the same users give 5.54% and 7.26%.
- Findings versus hypotheses: Verified (exploratory): the numbers above. Hypotheses (unverified): the official selection includes users with any expiration in the month, not only the last one; for early renewers the official label may be measured against a later expiration, so some early renewers who then lapse are labeled churn. Neither is in the demonstration script.
- Decisions and rationale: Rebuilt rates and official rates describe different populations and label treatments and must not be compared directly. Rebuilt cohorts are used for trends across months and are described as "rebuilt with the demonstration rule"; the official labels remain the reference for the February and March 2017 windows. The early-renewer treatment is an open question to resolve before the modeling stage.
- Blockers / dependencies: None.
- Next action: see "At a glance".
- Commit or pull request: None.

### 2026-10-06 (update 13) — Cross-month cohort analysis published

- Date: 2026-10-06
- Phase and status: Stage A: audit, label check, and monthly cohorts complete; feature windows and cutoffs next.
- Changes / artifacts: `src/churn_labels.py` (label rebuild, last expirations, looser population rule), `tests/test_churn_labels.py` (31 tests together with the existing ones pass), `notebooks/02_population_and_churn.ipynb` (executed from a fresh kernel by the user, 6 of 6 code cells, no errors), `reports/figures/churn_rate_by_month.png` and `reports/figures/spike_months_by_expiration_day.png` (exported from the notebook outputs), `requirements.txt` (matplotlib, pyarrow), README sections "Churn over time" and updated status, repository map, and reproduction steps.
- Validation performed and results: Notebook outputs reproduce the exploratory figures (February 2017: 879,537 users rebuilt, 88.57% of the official users covered, 98.36% agreement; March 2017: 886,500, 88.79%, 95.73%; looser rule 99.06% and 98.68%; monthly cohorts 393 thousand to 880 thousand users with a churn label rate of 3.7% to 19.2%). One finding-table sentence quoted figures that were not visible in the outputs and was replaced by figures taken from the shown tables. Machine paths and user identifiers are absent from the notebook.
- Findings versus hypotheses: See update 12 and 12b; the campaign or trial reading of the batch cohorts and the early-renewer labeling remain hypotheses.
- Decisions and rationale: Publish the analysis with its limits stated in the README (rebuilt and official rates are different populations; labels rebuilt only up to February 2017).
- Blockers / dependencies: None.
- Next action: see "At a glance".
- Commit or pull request: Two commits on `main` (label module and tests; notebook, figures, README, plan), pushed.

### 2026-10-06 (update 14) — Prediction setup designed

- Date: 2026-10-06
- Phase and status: Stage A definitions complete (design); stage B next.
- Changes / artifacts: Added `docs/prediction_design.md` (unit of prediction, cutoff at the end of the previous month, feature windows by family, leakage controls with a purge rule, time-ordered splits, evaluation at capacity K) and updated the README status row and docs map.
- Validation performed and results (full data, exploratory, read-only): Lead time from the cutoff to the last expiration over the analysis months 2015-07 to 2017-02: 22.0% of user-months have 1–7 days, 22.0% 8–14, 22.2% 15–21, 33.8% 22–31 (churn label rate 10.42%, 6.31%, 6.31%, 6.79%; the first band includes the batch cohorts). In the February 2017 cohort (879,537 users) 68.8% have a listening log in the last 7 days before the cutoff, 77.1% in 30 and 80.5% in 90, so 19.5% have none in 90 days; churn label rate by listening days in the last 30: none 2.76%, 1–5 days 6.10%, 6–15 days 5.55%, 16–25 days 3.80%, 26–30 days 2.36%. Transaction history at the cutoff: median 15 transactions, 8.9% with a first transaction under 90 days earlier, 7.7% with at most two transactions.
- Findings versus hypotheses: Verified (exploratory): the figures above; the descriptive pattern by listening days is not a causal claim and has been checked for one cohort only. Hypothesis: users without logs form a distinct low-churn group (possibly a different user type); not investigated.
- Decisions and rationale: Features use data up to T only; all splits are by time; training months for predicting month M are M-2 or earlier (labels complete about 30 days after the end of the month); the official March 2017 file is an external check reported separately; `has_member_profile` is not a feature until shown to be knowable at T; missing behavior is flagged and never treated as zero listening.
- Blockers / dependencies: None.
- Next action: see "At a glance".
- Commit or pull request: None yet.

### 2026-10-06 (update 15) — PostgreSQL layer built and reconciled

- Date: 2026-10-06
- Phase and status: Stage B (relational analytics) started; database built, SQL analyses next.
- Changes / artifacts: `sql/postgres/` (schemas `staging` and `analytics`, text staging tables, `\copy` load, typed analytics tables with keys and indexes, `run_all.sh`), `sql/quality/01_reconcile_postgres.sql`, `docs/data_model.md` (schemas, logical ER diagram, key coverage), README status row and repository map.
- Validation performed and results (full data): all 5 row counts (staging, analytics, audit) and 12 audit figures reproduced from the typed tables, status OK; database about 9.7 GB (analytics 6,408 MB, staging 3,272 MB). Key coverage: transaction users found in members 81.95%, labeled users in members 88.84%, labeled users in transactions 100%.
- Findings versus hypotheses: Verified: the figures above. No foreign keys on `msno` because unmatched users exist; this follows the rule not to drop records for integrity.
- Decisions and rationale: two layers (raw text, typed analytics); `user_logs` stays in Parquet (about 410 million rows, PySpark in stage C) and only user-by-month summaries will be loaded.
- Blockers / dependencies: None.
- Next action: SQL analyses in `sql/analysis/` (monthly churn, cohort retention, renewal gap, plan mix).
- Commit or pull request: None yet.

### 2026-10-07 (update 16) — First SQL analysis block

- Date: 2026-10-07
- Phase and status: Stage B (relational analytics): first five SQL analyses run by the owner in pgAdmin; monthly churn and cohort retention added (CTEs, window functions).
- Changes / artifacts: `sql/analysis/01` to `05` (user history, expiring users by month, last-expiration population, official label rate with profile coverage, plan mix with auto-renew), `06_monthly_churn.sql`, `07_cohort_retention.sql`, `reports/sql_analysis.md`; the PostgreSQL layer was committed and pushed (e61c57c).
- Validation performed and results (full data): official churn label rate 6.39% (v1, 992,931 users) and 8.99% (v2, 970,960), profile missing for 11.66% and 11.33%; February 2017 last-expiration population 883,727 in SQL against 879,537 in the Python rebuild (0.48% difference); 0-day plan count 870,124 equals the audit; plan mix 87.97% 30-day, 5.07% over 30, 4.04% 0-day, 2.91% under 30; simplified SQL monthly churn 4.29% to 18.53% over 2015-07..2017-02 (2017-02: 4.45% against 3.95% in Python); 2016 cohort retention drops about 20-35 points between month 0 and month 1, then levels off near 55-66%.
- Findings versus hypotheses: Verified: the figures above. Hypothesis: the 4,190-user difference comes from ordering details (plan signature, cancellations); not isolated yet.
- Decisions and rationale: results are published as SQL files plus a text report, not screenshots; the user-history query prints no identifier.
- Blockers / dependencies: None.
- Next action: renewal-gap distribution and plan-type split of cohort retention; then stage C features.
- Commit or pull request: None yet.
