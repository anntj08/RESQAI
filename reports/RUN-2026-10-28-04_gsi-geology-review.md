# Run Report RUN-2026-10-28-04 — GSI 1:50,000 geology for Wayanad: availability re-check

**Date:** 2026-10-28 · **Session goal:** investigate the missing GSI 1:50,000 geology dataset
for Wayanad using official GSI / Kerala-government sources; establish product, coverage,
access, format/scale/terms, and suitability — no modelling, no changes to Phase 4/5 outputs.
**Starting state:** commit `63bbaae` (Phase 5 baseline complete and verified), tree clean.
**End state:** this run's commit (see §6); `GEO-02` remains **`ACCESS_RESTRICTED`** with a
re-confirmed, evidence-dated limitation record; no data downloaded; tree clean; nothing pushed.

## 1. What was run, in order

| # | Command / file | Purpose | Result |
|---|---|---|---|
| 1 | read `AGENTS.md`, `reports/README.md` | conventions | run-report + verification-vocabulary rules loaded |
| 2 | review `docs/data_manifest.csv` (GEO-01/02, P3-06), `docs/data_sources.md` §1.4, `docs/DATA_READINESS_REPORT.md` §14, `docs/PHASE5_PROGRESS.md`, Phase-1 probe scripts | establish the prior record | GEO-02 = ACCESS_RESTRICTED (Bhukosh TCP refusals; Bhusanket 499); only 1:50K geology on disk = map plates in held PDFs 14767/14768/14999 |
| 3 | web search (official sources only) | identify the product | GSI 2019 policy §7.1 + NGDR brochure confirm the product; KSDMA hosts GSI-2022 LSZ shapefiles (susceptibility, not geology) |
| 4 | `python scripts/probe_gsi_geology_50k.py` | fresh reachability evidence | bhukosh **443 connect timeout** (2 URLs); bhusanket root 200, ArcGIS services dir 200 (v11.2); www.gsi.gov.in 200; NGDR hostnames failed DNS; KSDMA 200 → `data/interim/gsi_geology/probe_results.json` |
| 5 | folder enumeration on bhusanket ArcGIS | look for geology services | folders GSI/Hosted/Susceptibility/Sector_Map/Utilities contain **only landslide + dashboard services; no geology** |
| 6 | `python scripts/probe_ngdr_geodata.py` | NGDR anonymous access test | root/login 200; `/api/datasets` → **401**; geoserver/arcgis paths 404 or redirect to login → `ngdr_probe.json` |
| 7 | `python scripts/probe_ngdr_guest_services.py` + `probe_ngdr_guest_assets.py` | guest-viewer service endpoints | 20 bundles fetched (vendor JS only); **0 anonymous service endpoints** → `ngdr_guest_services.json`, `ngdr_asset_endpoints.json` |
| 8 | `python scripts/fetch_gsi_policy_docs.py` | capture official terms/product evidence | policy PDF 609,660 B sha256 `5ca1cd39…f175c3`; NGDR brochure 5,149,164 B sha256 `05cfe121…2016743`; §7.1 text extracted → `policy_2019_section71.txt` |
| 9 | manifest `GEO-02` row update; `data_sources.md` §1.4 re-check block; `DATA_READINESS_REPORT.md` §14 note | record confirmed facts | done; status field unchanged |
| 10 | p2/p3/p4 consistency checkers + `git diff --check` | regression | pass / 470+ / pass / clean (§4) |
| 11 | commit | capture | see §6 |

## 2. Measured values (do not re-derive; every value traceable to a file)

**The product (from official documents, on disk):**

* GSI **Data Sharing and Accessibility Policy 2019**, §7.1 (verbatim, `data/interim/gsi_geology/policy_2019_section71.txt`): compiled 1:50K (or 1:63,360) mapping "to bring it to a uniform scale and prepare **seamless lithology and structure** unifying the legend across India"; §7.1.2 access as **WMS/WFS/equivalent map services**; §7.1.3 "**maximum of 29 layers** as per the 1:50K geodatabase will be placed in public domain", GIS-format retrieval via **BHUKOSH**; §7.1.4 "**free of charge to registered users** of GSI portal"; Annexure IV = online undertaking/NDA for unrestricted-area downloads.
* NGDR brochure (Ministry of Mines, `data/raw/geology/gsi_policy/NGDR_brochure_mines_gov_in.pdf`): "**Standard Geological Map (1:50K) — Area: 32.7 lakh sq km (TS: 5087)**"; tier table: guest/random user = **VISUALIZATION**; "Any Registered User" = **VISUALIZATION & DOWNLOAD**.

**Reachability today (probe JSONs):**

* `bhukosh.gsi.gov.in` — **connect timeout on 443** (`/` 42.2 s, `/Bhukosh/Public` 42.1 s); also unreachable via the fetch-service network path. Phase-1 finding re-confirmed on 2026-10-28.
* `bhusanket.gsi.gov.in` — root 200; ArcGIS REST v11.2 services directory open (Phase-1 "499 Token Required" no longer observed): folders `GSI` (4 landslide services), `Hosted` (1 dashboard FeatureServer), `Susceptibility`/`Sector_Map`/`Utilities` (0 services). **No geology service exists on Bhusanket.**
* `www.geodataindia.gov.in` (NGDR; GSI nodal, BISAG-N integrator) — root/login 200; anonymous `/api/datasets` → **401**; `/geoserver/rest/layers.json` → 404; guest viewer HTML+bundles contain **no anonymous service endpoints** (20 bundles scanned, all vendor libraries).
* `www.gsi.gov.in` 200 (OCBIS landing page); `ngdr.gsi.gov.in` / `ngdr-gsi.gov.in` — DNS does not resolve (wrong hostnames); KSDMA `sdma.kerala.gov.in` 200.

**Adjacent official products, distinct from geology (documented, NOT downloaded):**

* KSDMA hazard-maps page (fetched 2026-10-28) hosts "**Landslide Susceptibility zones of District of Kerala (GSI, 2022) — Shape files**", including `https://sdma.kerala.gov.in/wp-content/uploads/2025/08/Wayanad.zip`. This is GSI NLSM **susceptibility** (1:50K macro-scale), **not a geological map**. URL recorded from the official page only; download was out of scope for this run.
* On-disk 1:50K geological information remains the **map plates inside held GSI report PDFs** (14767, 14768, 14999; TS 49M/14, 58A/3, 58A/1-11, 49M/13) — reference only, not analysis-ready.

## 3. Bugs caught and fixes

| # | Where | What | Fix |
|---|---|---|---|
| 1 | inline `python -c` under PowerShell | quote escaping broke the parser ("Missing type name after '['") | rewrote the probe as `scripts/probe_ngdr_guest_assets.py` (repo convention: no complex inline python) |
| 2 | guest-viewer endpoint hunt | naive regex over HTML found 1 candidate; the SPA loads service URLs at runtime | fetched 20 JS bundles and scanned them; result recorded as a genuine negative (no anonymous endpoints); vendor bundles then deleted, HTML + JSON evidence kept |
| 3 | pypdf on the policy PDF | benign "Ignoring wrong pointing object" warnings during text extraction | ignored — extraction succeeded (944 chars of §7.1) |

## 4. Verification and gates

| Suite | Result |
|---|---|
| `p2_check_consistency.py` | pass (manifest keeps GEO-02 present; 16 columns; unique ids) |
| `p3_check_consistency.py` | **470/470** (incl. its `DATA_READINESS_REPORT.md` needles, unchanged by the additive edit) |
| `p4_check_consistency.py` | **116/116** (manifest row count unchanged — no rows added — so the "43 datasets" pin holds; needle-scoped Phase 4 docs untouched this run) |
| `git diff --check` | clean |

## 5. Outputs produced or changed

* `docs/data_manifest.csv` — **GEO-02 row updated in place**: dataset_name now the identified product ("GSI Standard Geological Map 1:50,000 (compiled lithology + structure)"), source_url lists both portals, spatial_extent/scale/format set from official documents, limitations re-dated with today's probe evidence. `validation_status` **stays `ACCESS_RESTRICTED`**; `local_path` stays `(not downloaded)`; no rows added (row count pinned by the p4 checker).
* `docs/data_sources.md` §1.4 — dated re-check block: product identification, terms, reachability, coverage verdict, distinct-adjacent-products warning.
* `docs/DATA_READINESS_REPORT.md` §14 — one parenthetical pointer to the re-check; verdict text unchanged.
* `scripts/probe_gsi_geology_50k.py`, `probe_ngdr_geodata.py`, `probe_ngdr_guest_services.py`, `probe_ngdr_guest_assets.py`, `fetch_gsi_policy_docs.py` — re-runnable probes/evidence fetchers.
* `data/interim/gsi_geology/` — `probe_results.json`, `ngdr_probe.json`, `ngdr_guest_services.json`, `ngdr_asset_endpoints.json`, `policy_2019_section71.txt`, `ngdr_assets/guestuser.html` (all committed; ~180 KB).
* `data/raw/geology/gsi_policy/` — the two official PDFs, **unchanged originals** (gitignored as raw; sha256 recorded here and in the manifest): `Data_Dissemination_policy_2019.pdf` (609,660 B, sha256 `5ca1cd3938dc3271c8be58a9449c8b685f14972de296ab9d0c8da24819f175c3`), `NGDR_brochure_mines_gov_in.pdf` (5,149,164 B, sha256 `05cfe121715312fe9d5bf1310d7d1ac90710822f3eee19fd71002dcf42016743`).

**Explicitly NOT done:** no Wayanad geology file downloaded (none accessible); no clipping/resampling/merging into the predictor stack; no model, map, or Phase 4/5 output touched.

## 6. Current project state

Phase 5 baseline complete and verified (unchanged). Geology evidence chain now: GLiM 1:3.75 M
(`GEO-01`, VERIFIED) remains the only usable vector geology; GSI 1:50,000 (`GEO-02`) is
**identified at product level from official documents but ACCESS_RESTRICTED in practice**
(Bhukosh down; NGDR download registered-users-only). The manifest limitation record carries
the 2026-10-28 re-check evidence. **Commit of this run: `f2ab289`** (work + this report;
a one-line follow-up pins the hash).

## 7. Next-step handoff (prompt material)

* **Decisions the user must make:**
  1. Whether **the user (not the agent) registers** a free account on Bhukosh/NGDR —
     registration requires personal details, a mobile OTP and a photograph upload, which an
     agent cannot and should not do. With credentials, the next run could (a) confirm the
     Wayanad toposheet coverage at file level, (b) download the 1:50K geology subset under
     the Annexure IV undertaking, and (c) validate it toward `VERIFIED`.
  2. Alternatively, whether to commission **digitisation of the 1:50K geological map plates**
     already inside held PDFs (14767/14768/14999) — manual work, clearly outside agent scope.
  3. Whether to download the KSDMA-hosted **GSI 2022 Wayanad LSZ shapefile** (susceptibility,
     not geology) as a comparison product — separate decision, must never enter the predictor
     stack as "geology".
* **What the next step must do / must not do:** must keep GLiM (GEO-01/P3-06) and any future
  GSI 1:50K strictly distinct; must re-run the probes first (endpoints changed between
  2026-10-25 and 2026-10-28 — Bhusanket opened up); must not treat tile names, the guest
  viewer, or previews as coverage proof. Must not retrain or alter Phase 5 outputs when the
  geology question resumes.
* **Quick commands:** `python scripts/probe_gsi_geology_50k.py` ·
  `python scripts/probe_ngdr_geodata.py` · `python scripts/probe_ngdr_guest_assets.py` ·
  `python scripts/fetch_gsi_policy_docs.py` · p2/p3/p4 checkers.
* **Do not re-derive (quote as-is):** policy §7.1 quotes; brochure "Standard Geological Map
  (1:50K) — Area: 32.7 lakh sq km (TS: 5087)"; bhukosh 443-timeout re-confirmation;
  Bhusanket folder inventory (no geology); NGDR anonymous 401 + guest=VISUALIZATION-only;
  both PDF sha256 values; KSDMA `Wayanad.zip` URL as susceptibility-only.
