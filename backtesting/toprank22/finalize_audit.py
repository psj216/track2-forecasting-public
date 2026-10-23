"""Finish data-gated research truthfully; never fabricate model weights or performance."""
import gzip,hashlib,json,pathlib,collections
r=pathlib.Path(__file__).resolve().parents[2];p=r/'backtesting/toprank22/results';d=json.loads((p/'data-inventory.json').read_text());docs=json.loads((p/'document-manifest.json').read_text())
fed=[x for x in docs if len(x['timestamps'])==1 and any('federalreserve.gov' in u for u in x['source_urls'])]
pre='817bd6bc1b71c314999a4f4cebbd535d9dba6be5';parent='122ad52b3ba28bca06f480b723a0e82502bc77d4'
def put(name,obj):(r/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
blocks=[{'gate':'M_MARKET_HISTORICAL_AVAILABILITY','status':'INCOMPLETE','evidence':'Current ECB history and Treasury2026 table retrieved. Current retrieval is not original per-origin vintage authentication; local raw panels have no per-observation availability/vintage columns. Monthly ALFRED vintages exist by card and must NOT be described as missing or as corrupt.'}, {'gate':'B_POLICY_TEXT_TRAINING_JOIN','status':'INCOMPLETE','evidence':f'{len(fed)} unique-byte Fed-domain header candidates have unambiguous index dates,2007-2024; they are source-screen candidates, not fully verified independent releases or a trained dataset. Official corpus2025/2026 text count is zero; one2025statement was acquired. Full chronological text-change/outcome alignment and lawful multi-agency coverage remain unbuilt.'}, {'gate':'C_SCHEDULE_KNOWN_AT_ORIGIN','status':'PARTIAL','evidence':'Original Fed2024-08-09 announcement of2025/2026 tentative meetings retrieved. This proves that schedule was published then; it does not recover the complete schedule-publication/change history across training years. Current calendar alone is insufficient.'}, {'gate':'EVALUATION_INDEPENDENCE','status':'UNKNOWN','evidence':'2001-2024 histories exposed;2025ECB96-card cohort already exposed.2026data exist but have not been authenticated as an untouched, PIT-supported paired evaluation. Lack of independent data alone would limit promotion, not prohibit exploratory fitting; the combined training-join prerequisites also remain incomplete.'}]
readiness={**d,'classification':'DATA_BLOCKED','scope':'Readiness for the requested full A+B+C engine; not a claim that public data do not exist or every possible smaller study is impossible','fed_header_screen_candidates':len(fed),'training_rows_certified':None,'training_rows_actually_used':0,'trained_weights_exist':False,'gates':blocks,'raw_conflicts_interpretation':'1541 differing panel/asset/date values:1045macro_monthly,496rates_daily. These are cross-card differences, not proven data errors. Original metadata describes card-specific ALFRED macro vintages and an example-panel provenance contradiction; no arbitrary deduplication was done.','timestamp_conflicts_interpretation':'3identical text bodies have differing index dates; conservative later timestamps are documented for Beige Books. Not proof of future leakage.','source_url_count_scope':'246 counts URLs in first1500 characters only. It is NOT total provenance coverage: manifests and LANDMARKS.md also hold URLs.','source_probes':json.loads((p/'source-probes.json').read_text())+json.loads((p/'source-probes-followup.json').read_text())}
put('TOPRANK22-DATA-READINESS.json',readiness)
(r/'TOPRANK22-PIT-AUDIT.md').write_text('''# PIT audit — data gate not passed
Actual data inventory and bounded primary-source acquisitions were executed. This is not an access-denied or empty-data result.
126official cards,128distinct panel byte hashes,3,639,108rows across overlapping files and179,547distinct panel/asset/date keys were enumerated. Repeated copies are not independent observations.1139document references reduce to822distinct text byte hashes, not necessarily822distinct economic events. All index timestamps inspected are date-only. Dates alone can support conservative next-business-day activation, but do not prove original contents, revisions or complete publication coverage.

## Important corrections to the initial mechanical audit
1541different values at equal panel/asset/date are cross-card differences, not1541errors.1045are macro_monthly, whose card-specific ALFRED vintages are documented;496are rates_daily and were not adjudicated. Do not merge copies by choosing the newest or averaging them. The original example panel has an acknowledged source-label contradiction. Three identical document bodies have multiple index dates; official provenance explicitly permits later conservative Beige Book dates. Do not call those proven leakage.
The246URL count is header-only. Manifest source fields and LANDMARKS.md carry further sources.79Fed-domain header candidates are a conservative screen, not the complete eligible corpus. No raw-body learning was done.

## Official provenance limitations
At pinned official3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56,data/PROVENANCE.md documents unresolved retrieval URLs for649files in the original set, reuse terms for369files, unsettled rights for8regional-Fed files,5unverified early-EM panels and private factor-library rights. These counts describe that document's original corpus and must not be silently combined with today's deduplicated822. Public-domain US government subsets are usable candidates; unresolved foreign/corporate works were not copied to the new branch or trained on.

## New acquisitions
Fed calendar, Jan29,2025statement, current ECB history, Treasury2026table and original Aug9,2024Fed schedule announcement acquired with byte hashes. The first Treasury request used an incorrect path and returned404; the corrected official /resource-center/data-chart-center path returned200. This is not an unavailable-source finding. The old file receipts/alpha19-newdata/ust.csv is HTML, not a training CSV; never parse it as numeric data.
The Aug9,2024announcement supports2025/2026tentative dates, not a complete training-era schedule-availability ledger. The current ECB snapshot reaches2026; existence is not proof of untouched OOS or first-publication vintages. ECB's published framework permits correction/republication; current download is not automatically an original snapshot. Currency quote direction remains separate by panel; no unverified H.10/ECB ticker merge or FX conversion was performed.

## Stop interpretation
A fully validated market/text/schedule training join and chronological evaluation was NOT established. Training samples used=0; certified eligible count=UNKNOWN, not an assertion of zero possible samples. A narrower US-only/date-lagged/current-vintage exploratory study could potentially be designed, but it was not substituted for the requested full engine or used to bypass the registered data gate. DATA_BLOCKED applies to this execution's readiness, not a theorem of unavailable or useless information.
No model was trained; no future labels were used for forecasts; absence of a trained model cannot be described as a successful PIT leakage test. Independence remains UNKNOWN.
''')
(r/'TOPRANK22-RESEARCH-NOVELTY.md').write_text('''# Research novelty audit
Planned ECP-JOINT differs structurally from FF03 by directly learning conditional mean/scale/factor dependence and generating Student-t paths, instead of postprocessing FF03 or retrieving bootstrap starts. However, architecture novelty is not new information: market-price features, text changes and event uncertainty have appeared separately in prior work. No learned improvement is established here.
Recovered history reviewed: ALPHA-STRATEGY-RESET-05; NEW-INFORMATION-SEARCH-02; PRICE-STATE-INFORMATION-AUDIT-03; LOCATION01–04; EXPECTATION01; SURPRISE01; R17-RESEARCH-HISTORY and REPORT; ALPHA18; ALPHA19; MOONSHOT20; ALPHA21PRE69b01f1bea05c8500d317fecf3e99fd89d452dfd. Exact report hashes preserved in history-manifest.json. No prior experiment rerun.
V6event heads had3/205activations and release false; V7event memory ratios>1. V8/V9numerical result receipts were not recovered by prior audit: user-reported failure is not manufactured into verified scores. V10independent-data gate failed. V11–13joint results were exposed/mixed with parity gaps. THESIS/ORIGIN/SURPRISE/EXPECTATION/LOCATIONprimary mappings did not establish transferable alpha. Secondary text Ridge lead was exposed, not a candidate. PRICE-state lost to simpler controls. R17calendar-only variance interval crossed1; marginal worsened. ALPHA18age placebo nearly matched gain. ALPHA19failed material/improvement/independence promotion. MOONSHOT20is technically valid and performance unverified. ALPHA21is a PRE for prequential calibration, not an executed successful study.
TOPRANK22would need a lawful chronology-complete event response dataset and full-vs-no-event ablation to distinguish its information contribution. Neither renaming Ridge nor adding a Student-t distribution repairs missing evidence. Novelty of a trained engine remains NOT_TESTED because the data gate did not pass.
''')
(r/'TOPRANK22-ARCHITECTURE.md').write_text('''# Architecture status: PLANNED_NOT_IMPLEMENTED
Requested model: TOPRANK22-ECP-JOINT, hierarchical regularized conditional factor model +Student-t innovations+event-state mixture. A:past-only market features. B:supervised released-policy information and changes. C:schedule information demonstrably published before origin. Joint paths across assets and1–4BD horizons. Monthly:unmodified FF03 safety module.
No forecasting source, feature schema, hyperparameter lock, fitted scalers, factor loadings, Student-t degrees-of-freedom choice, model weights or ablation engine were created. Only executable data/source auditing code exists. Inventing arbitrary coefficients after a failed data gate would not satisfy the request.
''')
for name in ['TRAINING-RECEIPT','MODEL-MANIFEST','EVALUATION','ABLATION','CONTRACT-GATE','DOCKER-RECEIPT']:
 obj={'status':'NOT_RUN','reason':'DATA_READINESS_GATE_NOT_PASSED','classification':'DATA_BLOCKED','new_forecasting_engine_implemented':False,'training_rows_used':0,'model_weights':None,'new_candidate_score':None,'paired_ff03_score':None,'independent_alpha':'UNKNOWN','promotion':False}
 if name=='MODEL-MANIFEST':obj.update(model_name='TOPRANK22-ECP-JOINT',architecture_status='PLANNED_ONLY',image_id=None,registry_manifest_digest=None)
 if name=='EVALUATION':obj.update(historical_ff03_2025_ecb_score=0.9418927387445168,historical_score_scope='Already-exposed ALPHA19 research cohort; NOT a TOPRANK22 paired baseline or authenticated Final score',absolute_improvement=None,relative_improvement=None,components=None)
 put('TOPRANK22-'+name+'.json',obj)
(r/'TOPRANK22-ROBUSTNESS.md').write_text('''# Robustness NOT_RUN
No forecasts or evaluation were produced. No origin-block interval, quarter/year/asset removal, event ablation, worst-case loss or coverage can be claimed. All such metrics remain NULL. No synthetic outcome was used to certify performance. No threshold was relaxed and no favorable subset selected.
''')
(r/'TOPRANK22-FINAL-CANDIDATE-DECISION.md').write_text('''# DATA_BLOCKED
Phase1stopped because the requested joint market/policy/schedule training data and defensible evaluation were not established. This is NOT NO_ALPHA or REGRESSION: neither has been measured. Public source access works after explicit user authorization; the blocker is research readiness.
No new forecasting engine, learned weights, candidate predictions or Docker image. No0.85/0.80/0.70/0.60achievement. No change to FF03or any protected branch/image/archive/tag. Original FF03remains selected technical candidate. Actual registry publication, Team Key, packing and submission remain NOT_RUN.
Exact next action: continue the separate original FF03release preparation. Do not allocate more Final-deadline work to this incomplete data pipeline or automatically start another model. Any later resumption must start from the uncompleted authenticated chronological training join, not rerun the inventory or invent a performance result.
''')
(r/'TOPRANK22-REPORT.md').write_text('''# TOP-RANK-22 — 최종 결과: DATA_BLOCKED
새 모델 개발은 완료되지 않았다. 데이터 조사·공식 자료 수집·PIT/권리/노출 감사와 결과 저장을 수행했고,Phase1데이터 게이트에서 종료했다. 접근 승인은 해결됐고 실제 외부 다운로드도 성공했다. 데이터가 세상에 없다는 뜻이 아니라,요청한 엔진을 정당하게 학습·검증할 연결 자료가 이번 실행에서 성립하지 않았다는 뜻이다.

1. 새로운 예측 엔진 구현:아니오. 실제 구현은 audit_data.py/probe_sources.py와 감사 산출물 처리 코드다.
2. FF03과 구조적 차이:직접 조건부 factor/Student-t/event-state모델을 계획했지만 구현·학습하지 않았으므로 실제 모델 차이는 없음.
3. 새로 학습한 정보:없음.
4. 미래 예측 기여:미평가.
5. PIT 유출 제거:입증하지 못함. 카드별 빈티지·date-only시간·과거 일정 발표 이력을 분리해 미해결로 기록.
6. 학습 데이터:공식126카드,128패널 해시,겹치는 파일 합계3,639,108행,179,547panel/asset/date키,822텍스트 해시를 조사. 실제 학습 사용0행. 인증된 학습행 수는UNKNOWN이며822개를 독립 이벤트 수로 주장하지 않음.
7. 독립 평가:없음.2001–2024노출,2025ECB재사용,2026은자료 존재만 확인됐고 독립 PIT평가 미구축.
8. FF03정규화 손실:이번paired평가 없음.기존0.94189274는ALPHA19의2025ECB연구수치.
9. TOPRANK22손실:NULL/NOT_RUN.
10. 절대·상대 개선:NULL.
11. CRPS/Joint/Tail변화:NULL.
12. 자산·연도·사건 집중:미평가.
13. 이벤트 제거 ablation:미실행.
14. 최악 회귀:미측정.
15. FF03보다 우월:입증 없음.
16. 목표0.85/0.80/0.70/0.60:어느 것도 달성했다고 주장할 수 없음.
17. Final기술 적격성:TOPRANK22는아니오.
18. 독립 Docker:만들지 않음.승격 전 불필요한 빌드 금지 준수.
19. FF03보존:원격 안전 ref71c6ab1aa349a3cea01ca61e2b1a5f999c6b3006확인;기존 이미지·archive접근/수정 없음.
20. Final후보:기존 FF03유지.
21. Branch:track2/top-rank-22-event-conditioned-probabilistic-engine. Parent122ad52b3ba28bca06f480b723a0e82502bc77d4. PRE817bd6bc1b71c314999a4f4cebbd535d9dba6be5. RESULT는본 보고서 포함 커밋이며원격 ref로별도확인.
22. 다음 작업:새 연구를연쇄진행하지 않고 기존FF03배포·제출준비 경로 유지.이번 작업에서는공개Registry·키·ZIP·제출미수행.

## 실제 확인과 해석 한계
동일키값차이1541개는오류판정이아니다.1045macro월별차이는문서상ALFRED빈티지를고려해야하며496rates차이도임의통합하지 않았다.문서timestamp차이3건도보수적늦은날짜일수있다.기계적감사에서URL246개는본문앞1500자만집계했으므로전체출처보유량이아니다.
공식PROVENANCE는원래자료의출처URL·이용권리·일부패널생성근거공백을인정한다.불명확한외국기관/기업원문을새Git에복제하거나학습하지 않았다.79개Fed헤더후보는전체학습집합이나원문검증완료표본이아니다.
Fed공식발표문,ECB현재전체환율이력,Treasury2026표,2024년에발표한2025/26예정일원문을실제로확보했다.최초Treasury404는잘못된URL경로때문이었고수정주소200확인으로해결했다.이를데이터접근불가능이라고보고하지않는다.현재snapshot과날짜절단만으로과거빈티지진본성·독립성을인증할수없다.
최신공식SHA3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56,최대48카드/3x16/실패8.0.확인시점issue4최신공지는CodaBench장애이며마감연장을추정하지않음.가중치0.5/0.3/0.2,M0기대오차분모,single-cell재분배,clip8변경없음.최신Monthly문서의관측월/발표일/빈티지구분유지.
''')
(r/'RECOVERY.md').write_text(f'''# TOPRANK22 recovery
Parent:{parent}. PRE:{pre}. Branch:track2/top-rank-22-event-conditioned-probabilistic-engine.
Final classification DATA_BLOCKED at data-readiness stage. Inventory and source probes completed; do not repeat. User explicitly approved scope after an initial automated scope rejection; public acquisitions then succeeded. No model/code/weights/evaluation/Docker exists. Exact next action:existing FF03release path; no automatic additional research.
Executable audit under backtesting/toprank22; raw external temporary files are not guaranteed durable. Public original URLs and byte hashes in source receipts support recovery; changed future bytes cannot be called the identical snapshot. Official corpus pinned3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56; inherited ECB archive93bac351c4a60e612e641150f2392db9f85fe497336ee9d71c4d241f70063eda. No restricted documents or secrets copied into this branch. Compressed manifests are gzip JSON with mtime0. Source audit output is not a forecast.
''')
put('STATUS.json',{'stage':'RESULT_DATA_GATE_STOP','classification':'DATA_BLOCKED','branch':'track2/top-rank-22-event-conditioned-probabilistic-engine','parent':parent,'pre':pre,'result_sha':'ENCLOSING_COMMIT_VERIFIED_EXTERNALLY','scope_authorization':'USER_EXPLICITLY_APPROVED_AFTER_INITIAL_AUTO_REVIEW_REJECTION','completed':['recovery','official_rules','history_review','actual_data_inventory','public_source_acquisition','pit_rights_exposure_audit','report'],'not_run':['forecast_engine','training','evaluation','ablation','robustness','candidate_Docker'],'selected_candidate':'ORIGINAL_FF03','registry_push':'NOT_RUN','team_key':'NOT_ACCESSED','final_zip':'NOT_CREATED','codabench':'NOT_SUBMITTED','next_action':'Existing FF03 release preparation; no automatic further model research','updated':'2026-10-23 Asia/Seoul'})
# Compact lossless manifests, preserving exact bytes and hashes; avoid printing document text.
manifest=[]
for f in sorted(p.glob('*.json')):
 raw=f.read_bytes();z=p/(f.name+'.gz');z.write_bytes(gzip.compress(raw,mtime=0));manifest.append({'file':z.name,'compressed_sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),'uncompressed_bytes':len(raw)})
(p/'compression-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('DATA_BLOCKED report/status files written; actual training remains NOT_RUN')
