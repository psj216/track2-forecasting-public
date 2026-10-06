"""Executive summary: provider evidence, access limits and frozen source-quality rubric; no outcome inputs."""
from .core import SCORE_COLUMNS

def inventory():
    # id,family,PIT,timing,depth,relevance,access,rights,coverage,repro,prohibited,novelty-prior,risk,official URL
    data=[
    ('CME_ZQ_POLICY_PATH','A','C','HIGH',2,2,'USER_LICENSE_REQUIRED','Written historical/API and offline rights required',True,False,False,'UNKNOWN','No licensed historical settlement vintages or correction/roll evidence in this environment','https://www.cmegroup.com/datamine/datamine-api.html'),
    ('CME_SOFR_POLICY_PATH','A','C','HIGH',1,2,'USER_LICENSE_REQUIRED','CME historical/offline license required',False,False,False,'UNKNOWN','SOFR futures launched 2018-05-07; no standalone 2015/16 coverage','https://www.cmegroup.com/media-room/press-releases/2018/5/08/cme_group_announcesfirsttradesofnewsofrfutures.html'),
    ('USD_OIS_POLICY_PATH','A','D','HIGH',2,2,'USER_LICENSE_REQUIRED','Vendor entitlement and offline-use terms unverified',True,False,False,'UNKNOWN','No acquired timestamped historical curve vintages','https://www.lseg.com/en/data-catalogue/forex-and-money-market'),
    ('CME_FEDWATCH_HISTORY','A','D','UNUSABLE',1,2,'USER_LICENSE_REQUIRED','History/model-output redistribution unverified',False,False,False,'UNKNOWN','Current display is not proven historical probability archive','https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html'),
    ('ATLANTA_MPT_SOFR','F','C','MEDIUM',0,2,'ACCESSIBLE_WITH_LIMITATIONS','Personal and educational use only; contest/offline permission unproven',False,True,True,'UNKNOWN','Actual downloadable history begins 2023-03-29; current model vintage and educational-only license','https://www.atlantafed.org/research-and-data/data/market-probability-tracker'),
    ('UST_CURVE_SPOT','B','C','MEDIUM',2,2,'ACCESSIBLE_PUBLIC','Official historical benchmark; original cache not recovered',True,True,False,'REDUNDANT','Lagged spot-yield history already used; current FRED/H15 vintage','https://www.federalreserve.gov/releases/h15/'),
    ('NEAR_TERM_FORWARD_SPREAD','B','C','MEDIUM',2,2,'ACCESSIBLE_PUBLIC','Derived from public fitted Treasury yields',True,True,False,'REDUNDANT','No distinct forward contract; derived curve vintage/correction caveats','https://www.federalreserve.gov/data/yield-curve-tables/'),
    ('ACM_TERM_PREMIUM','B','D','MEDIUM',2,2,'ACCESSIBLE_WITH_LIMITATIONS','NY Fed attribution/third-party terms apply',True,True,False,'LOW','Current historical model estimates do not establish original as-of model vintages','https://www.newyorkfed.org/research/data_indicators/term-premia-tabs'),
    ('SPD_POLICY_DISTRIBUTION','C','B','LOW',2,2,'ACCESSIBLE_PUBLIC','NY Fed attribution conditions',True,True,False,'UNKNOWN','Untested representation must be independently extracted/frozen; same already exposed survey family','https://www.newyorkfed.org/markets/primarydealer_survey_questions.html'),
    ('FOMC_SEP_POLICY_PATH','C','B','LOW',2,2,'ACCESSIBLE_PUBLIC','Board-authored content generally public domain; retain attribution',True,True,False,'UNKNOWN','Quarterly released policy projections; originals may be replaced; not a daily surprise source','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'),
    ('CFTC_TFF_TREASURY','D','C','MEDIUM',2,2,'ACCESSIBLE_WITH_LIMITATIONS','Government report generally public domain',True,True,False,'UNKNOWN','Report date is not publication date; 2023 cyber delays and prior release calendars/vintages unverified','https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalViewable/index.htm'),
    ('NYFED_DEALER_POSITIONS','D','D','MEDIUM',2,2,'ACCESSIBLE_WITH_LIMITATIONS','NY Fed attribution conditions',True,True,False,'UNKNOWN','Provider explicitly says historical data may reflect revisions since prior publication','https://www.newyorkfed.org/markets/counterparties/primary-dealers-statistics'),
    ('NYFED_ONRRP','E','C','MEDIUM',2,1,'ACCESSIBLE_WITH_LIMITATIONS','NY Fed terms permit use subject to attribution and third-party conditions',True,True,False,'UNKNOWN','Historical lastUpdated later than observation dates; original version is not recovered','https://www.newyorkfed.org/markets/rrp_faq.html'),
    ('H41_RESERVES','E','B','MEDIUM',2,1,'ACCESSIBLE_PUBLIC','Board-authored content generally public domain',True,True,False,'UNKNOWN','Weekly original-date sample; corrections/timing ambiguity inactive; macro direction mapping weak','https://www.federalreserve.gov/releases/H41/default.htm'),
    ('EFFR_FUNDING_STRESS','E','C','MEDIUM',2,1,'ACCESSIBLE_PUBLIC','NY Fed terms/attribution',True,True,False,'LOW','Realized overnight rate is not policy-path expectation; corrections may change history','https://www.newyorkfed.org/markets/reference-rates/effr'),
    ('RATE_OPTION_SKEW','F','D','UNUSABLE',1,2,'USER_LICENSE_REQUIRED','Historical contract/options license and derived-distribution permission required',False,False,False,'UNKNOWN','No acquired comparable 2015/16 option surface vintages or usable rights','https://www.cmegroup.com/market-data/license-data/market-data-policy-education-center.html'),
    ('MACRO_CONSENSUS_NOWCAST','G','D','LOW',2,1,'UNKNOWN','Source-specific terms not yet verified',True,False,False,'LOW','Do not recycle failed ECB/SLOOS quarterly information under a new name','https://www.federalreserve.gov/monetarypolicy/fomc_projectionsfaqs.htm'),
    ]
    out=[]
    for name,family,pit,timing,depth,relevance,access,rights,coverage,repro,prohibited,novel,risk,url in data:
        r=dict(source=name,family=family,PIT=pit,Timing=timing,Novelty=novel,access=access,rights_status=rights,coverage_pass=coverage,relevance_pass=relevance==2,reproducible=repro,primary_prohibited=prohibited,risk=risk,documentation=url,frequency={'HIGH':'daily/intraday','MEDIUM':'daily/weekly','LOW':'monthly/quarterly','UNUSABLE':'unverified'}[timing],provider=url.split('/')[2])
        r.update(dict(pit={'A':2,'B':2,'C':1,'D':0}[pit],timing={'HIGH':2,'MEDIUM':1,'LOW':0,'UNUSABLE':0}[timing],depth=depth,relevance=relevance,novelty={'HIGH':2,'MEDIUM':1,'LOW':0,'REDUNDANT':0,'UNKNOWN':0}[novel],persistence=0,alignment=0,readability=2 if name in ['ATLANTA_MPT_SOFR','NYFED_ONRRP','UST_CURVE_SPOT'] else 1,reproducibility=2 if repro and pit=='B' else 1 if repro else 0,rights=2 if access=='ACCESSIBLE_PUBLIC' else 1 if access=='ACCESSIBLE_WITH_LIMITATIONS' and not prohibited else 0))
        out.append(r)
    return out

SPEC={
 'executive_summary':'Source discovery against frozen SPD direction only; no future UST outcomes, no forecast model or new CRPS.',
 'parent_RESULT_SHA':'16ef4d87f15151796b072e2a6f658ec076171bda',
 'numeric_cutoff':'2024-12-18',
 'asof_cutoff':'previous repository weekday 16:00 America/New_York; original dated sources conservatively activate publication-date EOD; next BD EOD for MPT; never response/survey/observation time alone',
 'alignment':'only latest known as-of state; fixed economic sign; no optimized lags; all frozen SPD asset/horizon cells retained',
 'recipes':{'FOMC_SEP_POLICY_PATH':'NCY median minus CY median at RELEASE calendar year, same fixed state until next original SEP; no mechanically retargeted January rollover','H41_RESERVES':'negative Wednesday reserve balance change vs latest verified original release at 21BD earlier; missing if that exact scheduled predecessor is not acquired','NYFED_ONRRP':'negative total accepted change vs21BD earlier; current-vintage-only, never before max(original operation day,lastUpdated)EOD; older late updates cannot replace newer observations','ATLANTA_MPT_SOFR':'mean rate second-nearest future quarter minus nearest future quarter; conservative nextBD EOD; PIT-C','PRICE_21BD':'own-asset 21BD yield change from bounded current FRED DGS2/DGS5; comparison proxy, not exact original cache'},
 'persistence':'weekday lag1/5/21; gaps remain missing; daily expansion only for COMPLETE release intervals, no fabricated hold across unknown weekly updates; source-state statistics, not alpha',
 'persistence_score':{'2':'>=60 observed contiguous BD; lag5 autocorrelation>=0.8; unchanged direction>=0.9','1':'>=20 observedBD; lag5 autocorrelation>=0.5','0':'otherwise/missing'},
 'useful_alignment':'at least24 origins, release-balanced sign agreement>=0.55 AND Spearman>=0.10; diagnostic, not future-target evidence',
 'alignment_score':{'2':'useful alignment','1':'>=12 origins and release-balanced Spearman>0','0':'otherwise/missing'},
 'redundancy_features':['DGS2/5/10 levels','own 5/21/63 weekday changes for each yield','2s5s','2s10s'],
 'redundancy_classification':{'HIGH':'source-state in-sample price projection R2<0.4','MEDIUM':'0.4<=R2<0.8','LOW':'0.8<=R2<0.95','REDUNDANT':'R2>=0.95 or price-derived by construction','UNKNOWN':'no adequate acquired state sample'},
 'novelty_limitation':'Exact prior raw price-state cache not available. Current official DGS proxy, in-sample redundancy with smallN; no claim of superiority to full original price-state features.',
 'score_components_0_to_2':SCORE_COLUMNS,'SPD_alignment_maximum':2,
 'hard_gates':['PIT A/B','timing notUNUSABLE','2015/2016 through2024 historical coverage','directUST2Y5Y relevance','reproducible actual access or acquired originals','rights not prohibited'],
 'selection':'highest score among hard-gate, useful-alignment, HIGH/MEDIUM novelty passing sources; alphabetical tie break. Exactly one audit focus; eligible forecasting primary null if none, rather than forcing a winner.',
 'model_executions':0,'new_CRPS_executions':0,'independent_validation':'NOT_AVAILABLE',
 'ranking_firewall':'only explicit metadata/diagnostic allowlists, ignore future_truth/return/CRPS columns; never read private forecasting label or CRPS files',
 'next_experiment':'draft only, conditional on source-readiness and remote frozen PRE; not executed here'
}
