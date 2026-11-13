# Executed verification report

Release review: 6 November 2026 (Asia/Jakarta). These checks concern the independent website and its data adapter. Research experiments were not rerun.

| Check | Result | Evidence / scope |
| --- | --- | --- |
| TypeScript | PASS | typecheck.log; strict compiler check |
| ESLint | PASS | lint.log |
| Next.js production build | PASS | build.log; includes /api/data and /api/boundary |
| Python pipeline | PASS, 26 tests | pytest.log; isolated TEST_FIXTURE_NOT_RESEARCH_DATA |
| API contract / reconciliation | PASS, 28 assertions | api.log; real route handler in-process, not a second HTTP server |
| Snapshot checksums and totals | PASS | snapshot-verify.log; daily/monthly/annual counts equal retained rows |
| Original source preservation | PASS, 133 files | ORIGINAL_INTEGRITY.json compared with pre-website hashes |
| Actual research reconciliation | PASS | RECONCILIATION.json; 154,184 detections; 3,678 clusters; 74,383 noise |
| UI filters | PASS | Browser changed 2026 date range to 20,252 detections; region, satellite, confidence controls exercised |
| Invalid UI filter | PASS | Confidence 101 produced explicit validation error; reset recovered |
| Empty state | PASS | Reset snapshot pointer; KPI dashes and no observation layer; rollback restored data |
| Loading state | PASS observed | Initial page/map loading skeletons and map update indicator observed |
| Import dialog keyboard | PASS | Opened with Enter, closed with Escape |
| Historical comparison | PASS | January 1–October 30 shared window for 2025/2026; coverage caveat visible |
| Cluster explorer | PASS | Original counts shown; selecting noise changed map count to 74,383 |
| Prediction gate | PASS | No classifier or fictitious metrics shown |
| Transparency / identity | PASS | Literal versions, provisional status, 13-file raw audit separately from one processed input; identity checked |
| SVG map fallback | PASS | Actual polygon/grid rendered; zoom and attribute popup exercised |
| CSV export in browser | PASS | Jambi filter downloaded 21,600 real rows; export checked against region |
| Responsive layout | PASS in frames | 390/768 CSS-pixel iframes; content widths 375/753 after scrollbars; no page overflow. Mobile menu opened/navigated/closed |
| Desktop overflow | PASS | Browser page width and content width matched |
| Reduced motion | IMPLEMENTED / partial verification | MotionConfig and CSS rule checked; OS/browser preference toggling not exercised |
| MapLibre WebGL2 rendering | NOT VERIFIED HERE | Cloud browser lacks WebGL2, confirmed GPUInitializationError. Reduced map remained usable; density disabled |
| Native Windows | NOT RUN | Installation guide supplied; native bindings must be installed on Windows |
| Vercel deployment | NOT RUN | Local production build passed; native binding, bundle limits and serverless behaviour require target preview test |
| New classifier training / metrics | NOT RUN by design | Original label/coverage limitation preserved |

Browser checks were performed across the working sessions; screenshots show actual imported observations. The tests assert data-contract and UI behaviour, not scientific validity of unobserved non-fire labels. No claim of perfect accessibility, operational monitoring, model performance, or guaranteed grade is made.

The import test suite covers schema errors, duplicate policies, invalid fields, cutoff accounting, missing optional attributes, ZIP/mapping, boundaries, checksum corruption, atomic activation, expected-count mismatch, artifact joins and prediction gating. The API suite also covers parameter-bound filters, map caps, export limits and matched-year counts.
