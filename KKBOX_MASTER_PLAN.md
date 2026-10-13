# KKBox Retention Analytics — Master Plan

Last updated: 2026-10-13  
Project owner: Casey Mei  
Repository: [`kcaseymei/kkbox-retention-analytics`](https://github.com/kcaseymei/kkbox-retention-analytics)  
Canonical location: `KKBOX_MASTER_PLAN.md` at the repository root

This is the project's source of truth for scope, status, decisions, and the next action. It was condensed on 2026-10-13: the long dated entries with every validation figure are in the Git history of this file; the figures that matter live in the reports and notebooks linked below.

## At a glance (updated 2026-10-13)

**Headline question:** Which behavioral signals appear before a KKBox subscriber churns, how early do they appear, and whom should be prioritized for intervention at a limited operational capacity?

| Stage | Work | Status |
|---|---|---|
| A. Audit and definitions | Full-dataset audit (v1 + v2), issue register, churn definition, label rebuild, monthly cohorts, prediction design | **Complete** |
| B. Relational analytics | PostgreSQL, metric definitions, cohort and renewal SQL | **Complete** (database, 9 SQL analyses, report) |
| C. Behavioral features | `user_logs` to user × cutoff features | **Built with DuckDB** (21 months, leakage-checked); Databricks/PySpark version planned |
| D. Serving and BI | Snowflake marts built with dbt, Power BI dashboard (Tableau, Streamlit optional) | **dbt project built and tested locally** on DuckDB; Snowflake and the dashboard next |
| E. Prediction and prioritization | Baseline plus one stronger model, top-k evaluation | **Complete (first pass)** |
| F. Recommendations and write-up | Intervention and experiment design, case study | Planned |

**Where the project stands**
- **Data:** two releases, about 444 million rows audited; 19 data-quality items in `reports/data_quality_issues.md`; churn labels rebuilt from transactions (98.4% agreement with the official February 2017 labels on shared users), reliable up to 2017-02 because renewals after 2017-03-31 are invisible.
- **Relational layer:** PostgreSQL (`staging` and `analytics`), reconciled with the audit; nine SQL analyses; data model in `docs/data_model.md`.
- **Features:** 63-column monthly feature table (31 listening, 20 subscription, 7 profile) for 21 target months, four leakage checks passed; definitions in `docs/feature_dictionary.md`.
- **Models:** on held-out months 2017-01 and 2017-02, contacting 10% of the expiring users reaches 71.9% and 68.1% of the churners with gradient boosting, against 52.5% and 54.2% for the rule "last transaction has auto-renew off" and 10% at random. With the official labels the lead over that rule shrinks (60.8% against 52.6% in February; a tie at 10% capacity in March 2017, where 11.2% of the official users fall outside the population the model was built for). Listening features add about 1 point on top of the subscription record. Details: `reports/model_results.md`, `docs/model_card.md`.
- **dbt:** 6 models and 38 data tests (36 pass, 2 warn by design: users without a member profile are kept, not dropped).

**Open questions:** early-renewal labeling in the official files (supported hypothesis, agreement 99.25% in February, about 6,500 disagreements unexplained); why the official sample includes users outside the last-expiration rule; the cause of the batch cohorts and of the March 2016 spike (17.97%); why users with no listening have a low churn label rate; the `total_secs` threshold; whether the two transaction releases overlap harmfully (7,249 shared user-date keys); whether the member profile (a 2017-11 snapshot) is safe to use.

**Next action:** (1) stage F: recommendations and an experiment design that separates risk from response to treatment; (2) quantify the transaction overlap and decide the label target (rebuilt or official-style); (3) stage D: Snowflake target and dashboard (needs an account the owner creates), then the Databricks/PySpark version of the log features. Optional, dropped first if time is short: a Streamlit app on aggregated tables, and the lead-time experiment (`docs/lead_time_experiment_design.md`, draft, not approved).

## 1. Purpose and positioning

Build an **end-to-end subscription retention case study**, from raw data to a defensible business decision. Kaggle provides the data (WSDM – KKBox's Churn Prediction Challenge, https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge); the portfolio adds subscriber behavior, retention measurement, analytical engineering, prediction, and intervention design. It should show the ability to clarify an ambiguous problem, test data quality, define trustworthy metrics, build reproducible transformations, and propose testable actions; model performance is one component.

Historical associations do not establish causal impact. No retention lift or financial return is claimed without observed experimental evidence; any scenario estimate states its assumptions.

**Questions (collapsed from eight to four):** (1) what churn looks like and who is higher risk; (2) which transaction and listening signals precede churn; (3) how early the signals appear and what top-k prioritization achieves; (4) which interventions to test and how to measure them.

**Roadmap:** six public stages A–F over ten internal phases (Section 5). The README presents five layers: Python/pandas/Parquet, PostgreSQL, Databricks/PySpark, Snowflake, Power BI/Tableau; Fabric is an optional extension. A platform without a demonstrable artifact is not listed in the README or resume. Cutoff and feature windows are fixed in stage A; the cutoff is the as-of date (data before it builds features, data after it only decides the label).

**Optional extensions** (dropped first if time is short): a Streamlit app with a capacity slider on aggregated tables only (no user identifiers); a lead-time experiment that moves the prediction cutoff back by 7 to 180 days with population and labels held fixed.

## 2. Working principles

- Introduce each tool when a concrete requirement needs it; start locally, add cloud platforms after the data and analytical contracts are understood.
- Define population, time windows, table grain, and metric denominators before publishing comparisons (`docs/metric_definitions.md`).
- Preserve raw inputs; record each quality issue as finding → decision → treatment → validation.
- Label full-data checks versus samples, documented claims versus verified findings, hypotheses versus findings, and planned work versus implemented work.
- Keep notebooks reproducible, reused logic in `src/` with tests, SQL readable and versioned.
- Keep raw and processed data, credentials, and machine-specific configuration out of Git.

## 3. Architecture and tool responsibilities

| Layer | Responsibility | Output | State |
|---|---|---|---|
| Python / pandas / DuckDB / Parquet | Audit the 410-million-row listening logs on a laptop, labels, features, models | Audit notebooks, `src/` modules, tests | Done |
| PostgreSQL (+ pgAdmin client) | Relational storage and SQL analysis of members, labels, transactions | DDL, load scripts, reconciliation, SQL analyses | Done |
| dbt | Staging and mart models with data tests, documentation, lineage | `dbt/` project | Local (DuckDB) |
| Databricks / PySpark / Delta | Distributed version of the log aggregation, compared with the local result | Notebooks, Gold aggregates | Planned |
| Snowflake | Cloud serving layer for the dbt marts | Marts, reconciliation | Planned |
| Power BI / Tableau | Executive monitoring; complementary exploration | Dashboard and measure documentation | Planned |
| Predictive modeling | Risk prioritization using only information available at the cutoff | Evaluation, model card | Done (first pass) |
| Recommendations | Intervention hypotheses and experiment specification | Memo and experiment plan | Planned |

Systems exchange data through explicit curated exports with row counts and date coverage recorded. No real-time orchestration or production deployment is implied.

## 4. Phases and completion gates

A phase is complete only when its gate has supporting evidence.

| Phase | Deliverables | Completion gate |
|---|---|---|
| 0 Git and setup | Repository, ignore rules | Pushed |
| 1 Data audit | Audit notebook, data dictionary, issue register | Full-data checks reproduced; issues recorded with treatments |
| 2 PostgreSQL | DDL, repeatable load, data model, SQL checks | Counts reconciled to the source; join strategy without unexplained row multiplication |
| 3 Definitions and descriptive analysis | Churn definition, metric definitions, cohorts, SQL analyses | Stable definitions and traceable descriptive conclusions |
| 4 Databricks / PySpark | Bronze/Silver/Gold notebooks, quality checks, aggregates | Outputs reconciled with the local result; repeatable runs |
| 5 Snowflake | dbt marts, documentation, reconciliation checks, runbook | Consistent definitions and a reproducible load path |
| 6 Power BI | Executive dashboard with documented measures | Measures reconcile to validated analyses |
| 7 Tableau | One focused exploratory workbook (not a duplicate dashboard) | Views add analytical value beyond Power BI |
| 8 Predictive modeling | Time-ordered evaluation, baselines, a stronger model, calibration, model card | Documented holdout protocol and an honest assessment of operational usefulness |
| 9 Recommendations and experiments | Prioritized proposals; randomized experiment design (eligibility, randomization unit, outcome, guardrails, sample size); risk kept separate from response to treatment | No claim of a live experiment |
| 10 Final portfolio | README, visuals, case study, reproducibility review | A reader can reproduce the main results |

## 5. Progress tracker (as of 2026-10-13)

| Phase | Status | Evidence / remaining work |
|---|---|---|
| 0 Git and setup | Complete | Repository public, ignore rules in place |
| 1 Data audit | Complete | Full-data audit of both releases; DQ-001 to DQ-019; a restart-and-run-all of notebook 01 is not recorded |
| 2 PostgreSQL | Complete | Reconciled with the audit; no foreign keys by design |
| 3 Definitions / descriptive analysis | Complete | `docs/churn_definition.md`, `docs/metric_definitions.md`; early-renewal labeling is a supported hypothesis |
| 4 Databricks | In progress | Features built locally with DuckDB; PySpark version and comparison not done |
| 5 Snowflake | In progress | dbt project works locally; Snowflake target not set up |
| 6 Power BI | Planned | Power BI Desktop is Windows-only; Tableau or Streamlit may replace it |
| 7 Tableau | Planned | |
| 8 Predictive modeling | Complete (first pass) | Open: early-renewer labeling, March population mismatch, release overlap |
| 9 Recommendations / experiments | Planned | |
| 10 Final portfolio | Planned | README kept current; case-study write-up pending |

**Open dependencies:** a Snowflake account and its time-limited trial (start only when ready; credentials come from environment variables and are never committed); a BI route that works on the owner's machine; confirmation of the source terms before publishing anything beyond code and aggregate findings.

## 6. Decision log

| Date | Decision | Reason |
|---|---|---|
| 2026-09-25 | The existing Git repository is the workspace; this root plan is the canonical context | Keep decisions and progress with the implementation |
| 2026-09-25 | Introduce tools progressively; descriptive analysis precedes prediction | A coherent business story and verified data contracts first |
| 2026-10-02 | Public five-layer architecture and a simplified six-stage roadmap with one headline question; Tableau and Fabric optional | A short, question-driven path shows capability better than a tool tour |
| 2026-10-02 | Restart the audit on the complete dataset (v1 and v2); convert the 30.5 GB logs once to text-typed Parquet and audit with DuckDB | The first audit covered v2 files only, and v2 is not a complete history |
| 2026-10-05 | Record the official dataset description in `docs/source_dataset_notes.md` | Documented claims stay labeled as documented until verified |
| 2026-10-05 | `CLAUDE.md` and `AGENTS.md` stay local only (git-ignored) | Private working instructions, not part of the portfolio |
| 2026-10-06 | Remove the superseded `PROJECT_PLAN.md` | This plan replaces it; the file stays in the Git history |
| 2026-10-06 | Rebuilt labels are used only up to 2017-02; March 2017 uses the official labels | Renewals after 2017-03-31 are invisible (right censoring) |
| 2026-10-06 | Prediction unit is a user in a target month; cutoff is the last day of the previous month; time-ordered splits with a purge rule | Prevent leakage between months |
| 2026-10-06 | No foreign keys on `msno` in PostgreSQL; unmatched users are kept | Records are not dropped to force integrity |
| 2026-10-10 | Add dbt to stage D and a Streamlit app as optional; no stack claim before artifacts exist | Show tested, versioned modeling; keep the public story honest |
| 2026-10-12 | Keep models trained on rebuilt labels and report both label sets side by side (option A); rebuilding all months with the official-style rule is deferred | The official-style rule is a supported hypothesis that cannot be verified for March |
| 2026-10-12 | dbt only transforms; log scans and feature building stay in `src/` | Each tool does what it is good at |
| 2026-10-13 | Condense this plan; keep full history in Git | The long log made the public plan hard to read |

## 7. Update log

At the end of a meaningful work session, update the last-updated date, affected statuses, artifact paths, validation evidence, blockers, decisions, and the next action. Add a milestone row below and, when the evidence needs more than a row, a short entry in this format:

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

Do not mark planned tasks complete or describe an unexecuted notebook as verified; if evidence changes the plan, update the relevant sections instead of keeping contradictory plans.

### Milestones

| Date | Milestone | Key evidence | Documented in |
|---|---|---|---|
| 2026-09-28 | Audit initialized; official Scala labeller read | Rule: renewal gap < 30 days is renewal; cancellation is not churn by itself | `docs/churn_definition.md` |
| 2026-10-02 to 05 | Full-data audit of v1 and v2, reusable DuckDB checks | Labels 992,931 / 970,960; members 6,769,473; transactions 21,547,746 + 1,431,009; logs 392,106,543 + 18,396,362; 19 data-quality items | `reports/data_audit.md`, `reports/data_quality_issues.md`, notebook 01 |
| 2026-10-05 | Release relationships | `transactions_v2` adds 361,187 pre-March rows and shares 7,249 user-date keys with v1 (hypothesis: complementary) | `reports/data_audit.md` |
| 2026-10-05 to 06 | Label windows and cutoffs verified; labels rebuilt | Cutoff = last day of the previous month fits best; 98.4% / 95.7% agreement (Feb / Mar 2017); 25 monthly cohorts, churn 3.7% to 19.2%; batch expiry dates drive spikes | `src/churn_labels.py`, notebook 02 |
| 2026-10-06 | Population and rate differences explained | The rule "any expiration in the month" covers 99.06% / 98.68% of the official users; early renewers are labeled churn 11% to 14% of the time | notebook 02, `docs/churn_definition.md` |
| 2026-10-06 | Prediction setup designed | Unit, cutoff, feature windows, purge rule, splits, evaluation at K = 5/10/20% | `docs/prediction_design.md` |
| 2026-10-06 | PostgreSQL built and reconciled | About 9.7 GB; key coverage 81.95% (transactions to members), 88.84% (labels to members), 100% (labels to transactions) | `sql/postgres/`, `docs/data_model.md` |
| 2026-10-07 to 10 | Nine SQL analyses; stage B complete | Official label rates 6.39% / 8.99%; monthly churn 4.29% to 18.53%; 88.6% of renewals within a week of expiry; 30-day-plan retention 100% to 70.6% after one month | `reports/sql_analysis.md` |
| 2026-10-10 | dbt added to stage D; Streamlit app optional | | Section 1 |
| 2026-10-11 to 12 | Monthly feature table and leakage checks | 63 columns, 21 months; 0 changed values when post-cutoff data is removed; highest single-feature AUC 0.77 | notebook 03, `docs/feature_dictionary.md` |
| 2026-10-12 to 13 | Stage E: baselines, models, independent review, ablation, model card | Recall at 10% capacity 71.9% / 68.1% (gradient boosting) against 52.5% / 54.2% (auto-renew rule); review led to five fixes | `reports/model_results.md`, `docs/model_card.md`, notebook 04 |
| 2026-10-12 | Rebuilt versus official labels investigated | The supplied script uses January history only and does not explain the files; ignoring early renewals raises February agreement from 98.36% to 99.25%; recall at 10%: 68.1% (rebuilt labels) to 60.8% (official, February) to 55.3% (March, inside the rebuilt population) to 44.9% (March, all users) | `docs/churn_definition.md`, `reports/model_results.md` |
| 2026-10-12 | Metric definitions written; lead-time experiment recorded as a stretch goal | | `docs/metric_definitions.md` |
| 2026-10-12 | dbt project built and tested locally | 6 models; 38 tests, 36 pass and 2 warn by design; marts reproduce the earlier results; 65 columns documented | `dbt/README.md` |
| 2026-10-13 | Plan condensed; README brought up to date | | this file |
