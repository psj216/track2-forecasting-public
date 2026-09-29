# V12-JOINT-NATIVE — Joint Market State Transition Forecast Engine

## Executive summary (read this first)

The complete V12 date-native joint model was trained and evaluated before repairs. Two focused repairs brought its 24-case local relative loss from 1.437 to 0.933 versus V5.1. The post-fit nine-case result is still 1.077, joint loss is 1.151, and F1 remains vulnerable. This is a reused, revised-history research proxy, not independent out-of-sample evidence or a forecast of the official 0.9541 score. The frozen V11 control was not changed. No Docker image was built and no CodaBench submission was made. READY_FOR_ONE_SHOT_SUBMISSION = NO.

## 1. 연구 경계와 V11 실패 진단

공식 기준은 V5.1 Development **0.9541**. V11 최종 로컬 상대 손실은 전체 **1.073**, 학습 이후 9건 **1.308**, joint 중앙값 **1.997**, F1 **1.311**이었다. V11의 14,678개 예제는 자산별 행이었고 cross-asset feature는 fit 시 사실상 0이었다. 사후 공분산 결합은 미래 시장 전체를 학습하지 못했다. V11 코드는 수정하지 않았으며 그 artifact SHA-256은 `403da1a9717f798187251f46983b4c445388da21bf28b4417c6103ba9c27436b`로 유지됐다. 브랜치는 `track2/v12-joint-native`; `main`은 변경하지 않았다.

## 2. Joint dataset과 feature

한 행은 **한 날짜의 시장 전체**다. `X[origin, asset, 19 local features]`, `G[origin, 21 global features]`, `Y[origin, 5 horizon, asset]`, `mask[origin, horizon, asset]`와 실제 target end 날짜를 보존한다. 5/21/63/126/189영업일이다. EUR처럼 기간이 짧은 자산, 관측치가 없는 날짜와 horizon은 0으로 채운 label을 학습하지 않고 **mask=False**로 제외한다.

| 항목 | 실제 집계 |
|---|---:|
| Joint 날짜 origin | **950** |
| Fit / post-fit origin | **414 / 536** |
| 자산 / horizon | **25 / 5** |
| 관측된 target cell / fit target cell | **52,453 / 38,134** |
| 실제 cross-asset feature가 0이 아닌 origin | **950** |
| Fit calendar years | **8** |
| 189BD 기준 거친 effective episode 상한 대용치 | 약 **11.0** |
| Long expert 학습 cell | **14,506** |

이 11.0은 `414 / (189/5)`라는 overlap 할인 근사치일 뿐 독립 OOS 수가 아니다. 평가 단위는 여전히 서로 겹친다. Daily 원점 stride는 5영업일. Fit label은 2008-12-31까지 끝나야 하고 post-fit 원점은 2009-10-01부터다. 자산의 명시적 공식 **target**으로 등장한 가장 이른 as-of 전에 종료한 label만 사용했다. Target이 아닌 panel 출현은 입력 context로만 사용하며, target 여부를 모르는 자산은 최초 panel 출현일을 보수적인 label 한계로 사용한다. 현재 역사 파일의 당시 빈티지는 검증되지 않았다.

Local feature에는 1/5/20/60/120/252 momentum, 252/504 trend, 252/504 level z-score, 20/120/252 volatility, drawdown·range·skew·kurtosis·regime duration proxy가 들어간다. Global feature에는 breadth, cross momentum/vol dispersion, 평균 및 장기 correlation, PCA concentration, FX breadth/USD direction, 2Y·10Y·2s10s slope·curve change, MKT/MOM/SMB/HML/BAB/QMJ 상태와 asset coverage가 들어간다. 명시적 USD 시계열이나 검증된 carry를 따로 학습하지 않았다. **CPI/UNRATE의 historical point-in-time vintage와 release time이 없으므로 strict joint 학습 feature와 label에서 제외했다.** 카드 target이 월별 macro라면 그 카드가 제공한 과거 prefix는 예측 입력으로 쓰지만 학습된 macro decoder가 없는 상태임을 `unsupported_assets`에 표시한다. 이는 strict PIT 인증이 아니다.

## 3. Latent state, transition, long-horizon expert

Train 날짜의 masked 21BD joint tensor에서 pairwise covariance를 identity로 shrink한 뒤 상위 **5개 PCA factor**를 고정했다. 이들은 학습 시 관측된 공동 움직임의 **57.16%**를 설명한다. 경제적 이름은 global breadth/rates/USD·FX/factor/stress global feature에 붙어 있다. PCA 축 자체를 검증된 경제적 `GLOBAL RISK` 요인이라고 단정하지 않는다.

공통 market state feature는 관측 가능한 각 자산의 local mean·dispersion, global vector, availability coverage와 log horizon을 합친다. 미래 PCA 첫 축의 훈련 구간 quantile로 5개 ordinal state를 만들고 정규화 multinomial softmax로 `p(state|current joint state,h)`를 학습했다. Low-rank ridge가 factor location을 학습한다. Five-state 학습 target count는 **240/459/599/459/240**이다. State label은 미래 outcome에 근거한 **학습 목표**이며 inference의 regime feature로 미래 값을 읽지 않는다. 직접 asset별 mean head를 먼저 묶는 V11 구조와 다르다.

126BD 이상에는 자산군 공통 long expert가 252/504 level deviation, 504 trend와 regime duration proxy에서 joint decoder residual을 예측한다. 특정 family·unit ID·card name 조건은 없다. 단 이 expert가 UNRATE처럼 학습에 포함되지 않은 자산의 장기 동학을 배웠다고 주장하지 않는다.

## 4. Covariance, residual과 world generator

각 학습 상태의 미래 latent residual covariance를 추정해 diagonal과 eigenvalue floor로 shrink하고 PSD를 강제한다. Extreme state는 사전 지정된 대칭 분산 prior를 갖는다. Decoder는 PCA loading과 자산별 masked residual variance를 사용한다. Student-t radial residual의 df는 훈련 tensor의 초과첨도에서 한 번 산출해 freeze한다. Stress를 상시 10% sleeve로 넣지 않고 미래 state draw에서 발생시킨다.

한 draw의 공유 uniform percentile이 5/21/63/126/189 상태 표본을 연결하고, 각 구간은 같은 latent factor path와 해당 state covariance를 따른다. Asset-specific residual도 같은 경로에 더한 뒤 cumulative asset path에서 요청한 business-day horizon을 읽는다. **자산이나 horizon 셀을 독립 생성해 합성하지 않는다.** V12 standalone을 먼저 완성했고, 그 다음에만 사전 고정한 전체 draw 혼합 **100% V12, 85/15, 70/30**을 계산했다. V11은 혼합 source가 아닌 control이다.

## 5. 누수 및 walk-forward 감사

Feature extractor는 as-of 뒤 panel을 절단하고, `target_end`가 fold fit 경계를 넘는 cell을 purge한다. Normalization, PCA loading, state quantile과 모델 계수는 각 fold의 train 날짜에서만 fit한다. Runtime은 JSON artifact를 로드하고 예측만 하며 fitting package와 인터넷이 필요 없다. Unit ID/card name embedding, official Development 점수 최적화, 공식 card target outcome 재구성은 하지 않았다. Monthly macro의 strict 빈티지 미확보는 해결하지 못했다.

Expanding calendar fold는 2003-12 → 2004-10~2005-06, 2005-12 → 2006-10~2007-06, 2008-12 → 2009-10~2010-09로 구성했다. 각 fold는 train label 종료일을 purge했고 2,000 draw를 public scoring primitive로 평가했다. 서로 다른 target type의 joint standardized tensor라서 비교 대상은 **zero-state 단위분산 Gaussian diagnostic**이지 V5.1 공식 점수가 아니다.

| Fold | Fit origin | 평가 origin | Calendar years | Gaussian 대비 상대 손실 |
|---|---:|---:|---:|---:|
| 1 | 156 | 10 | 2 | 1.097 |
| 2 | 260 | 10 | 2 | 0.992 |
| 3 | 414 | 9 | 2 | 1.340 |

Fold마다 데이터 소스와 시장 시기가 겹치며 빈티지도 current history다. V10-LEDGER의 독립 OOS 결손은 유지된다. 위 fold 결과는 첫 FULL 엔진의 개발 진단이고, 수리 후 새로운 독립 검증으로 재사용하지 않는다.

## 6. 첫 FULL, 두 번의 수리 및 세 모델 비교

V11과 **같은 24개 pre-card pseudo-origin**, family별 6건, calendar year 6개, 매번 **2,000 draw**. 9건·2년만 fit 이후 rolling이고 15건·4년은 fit 시기 진단이다. Case별 composite 상대 손실의 기하평균이며 component 수치는 case별 상대 손실의 중앙값이다. 이 둘은 수학적으로 바로 가산되지 않는다. 1 미만이면 해당 비교에서 더 낫다.

| 단계/모델 | V5.1 대비 전체 | Marginal | Joint | Tail | Post-fit 9건 | F1 |
|---|---:|---:|---:|---:|---:|---:|
| V5.1 control | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| V11 frozen control | 1.073 | 1.041 | 1.022 | 1.075 | 1.308 | 1.311 |
| V12 첫 FULL | 1.437 | 1.311 | 0.931 | 1.042 | 2.657 | 1.691 |
| Repair 1 후 | 1.215 | 0.959 | 0.947 | 1.005 | 2.126 | 1.493 |
| **V12 최종 standalone** | **0.933** | **0.903** | **1.151** | **0.829** | **1.077** | **1.041** |
| V12 85% + V5.1 15% | 0.941 | 0.922 | 1.150 | 0.868 | 1.072 | 1.037 |
| V12 70% + V5.1 30% | 0.947 | 0.940 | 1.091 | 0.898 | 1.058 | 1.024 |

최종 V12는 같은 case별로 V11 대비 전체 **0.873**이나, V5.1 대비 학습 이후 9건은 **1.077**로 열세다. 로컬 0.933을 공식 0.9541에 곱해 official score를 추정하지 않는다. 이 집계는 official 제출 결과가 아니다.

**Repair 1 — 관측 coverage에 맞는 state calibration.** 첫 실행에서 희소한 카드 입력에도 classifier가 극단 상태를 과신하고 V5.1 대비 중심이 여러 표준편차 이동했다. 훈련 데이터의 joint coverage 하위 10%를 기준으로 입력 coverage와 OOD를 재고, 지원이 약하면 학습 state prior와 중심 0 쪽으로 이동시켰다. 전체 1.437 → 1.215.

**Repair 2 — purged 학습시기 방향성 신뢰도.** 2005년까지 끝난 label로 일단 학습하고 2006-10~2008-03의 joint target **380개**에서 예상 latent location과 실제 이동의 신뢰도 기울기를 측정했다. 음수라 clip된 신뢰도는 **0.0**. 따라서 최종 artifact에서 unsupported directional state location만 제거하고 **state probability·conditional covariance·tail·joint path는 유지**했다. 전체 1.215 → 0.933, post-fit 2.126 → 1.077. 이 역시 기존 역사에서 고른 수리로 독립적 일반화 증거가 아니다.

**세 번째 수리는 사용하지 않았다.** 가장 큰 잔여 joint 손실은 월별 UNRATE의 145/165BD horizon과 F1 일부 장기 case에 집중한다. UNRATE의 빈티지가 없고 해당 자산은 학습 decoder에 없으므로 결과에 맞춰 임의 macro target label을 추가하거나 family별 fallback 숫자를 찾을 근거가 없다.

## 7. 최종 breakdown과 실패 구조

| 구분 | Cases | V5.1 대비 전체 | 비고 |
|---|---:|---:|---|
| F1 | 6 | **1.041** | joint 중앙값 **1.626**; worst long monthly 구조 **3.100** |
| F2 | 6 | 0.832 | 일부 fit 시기 비중 큼 |
| F3 | 6 | 0.892 | joint 개선 사례와 악화 사례 혼재 |
| F4 | 6 | 0.980 | 21BD stress 취약 |
| Single / multi | 13 / 11 | 0.900 / 0.973 | multi joint 중앙값 **1.151** |
| Normal / trend | 15 / 9 | 0.942 / 0.918 | stress로 분류된 case **0**; stress 성능 판정 불가 |
| 5 / 21 / 63 / 126 / 189 canonical max-horizon 근접 구간 | 0 / 5 / 10 / 4 / 5 | N/A / 1.054 / 0.945 / 0.645 / 1.081 | 최대 horizon의 가장 가까운 정규 구간으로 묶은 case 집계; 정확한 horizon별 cell score가 아님 |

최종 최악 10% 경계는 **1.275**, win rate는 **13/24**. Post-fit win은 **3/9**이고 joint 중앙값은 **1.520**이다. 특히 F1 월별 한 자산·두 horizon, 다른 F1 189BD 두 cell, F4 21BD 한 cell이 나쁘다. F1 한 case의 3.100은 빈티지 검증 없는 월별 target 구조에서 발생했으며 미래 관측값이나 card별 label은 공개 report에 싣지 않았다.

## 8. Artifact, 재현과 검증

최종 artifact: `qfbench2_track_forecasting/v12/artifacts.json`, schema v1, SHA-256 `72fc4fab0457bee1caecd2eb8a4c80af7dc9469b403d0a1cf2e67f4c327d63d3`. 여기에는 normalization, PCA loadings, 5-state logits/location, 5개 PSD covariance, asset decoder, long expert, Student-t df, OOF location reliability가 freeze되어 있다. 초기 두 단계의 artifact도 public Git 밖 private scratch에 snapshot을 남겼다. Raw label, origin별 진단 및 realized outcome은 repo에 저장하지 않았다. 집계는 `backtesting/v12_joint/`에 있다.

8개 자동 테스트가 미래 panel 불변성, 날짜 정렬과 실제 cross feature, target mask, PSD, horizon dependence, tensor shape, seed 결정성, runtime no-fit 및 whole-world source를 확인했다. F1 두 구조(일간 factor 및 월별 UNRATE), F2, F3(10 assets × 2 horizons), F4 각각 **2,000 draw**를 host에서 실행해 출력 행·asset·horizon·유한성을 확인했다. `Dockerfile.v12`는 linux/amd64 빌드 후보 **소스**이며 이 환경에는 Docker/Podman host가 없어 실제 build, network-none container smoke, anonymous pull은 검증하지 못했다.

## 9. 판정과 다음 조건

**READY_FOR_ONE_SHOT_SUBMISSION = NO.** V12는 V11보다 낫고 24건 전체는 V5.1보다 나아졌지만, 학습 이후 rolling은 V5.1보다 나쁘고 joint 및 F1 장기 문제가 남았다. 가장 취약한 월별 macro에는 검증된 당시 빈티지와 release calendar가 없다. 5BD와 stress case의 local proxy 증거도 없다. 남은 1회의 수리 허용량은 부실한 역사 label을 보완해주지 않는다. 공식 제출, Development 점수 튜닝, Docker image push는 하지 않았다.
