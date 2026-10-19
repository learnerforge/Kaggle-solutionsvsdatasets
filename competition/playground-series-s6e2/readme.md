# Predicting Heart Disease (`playground-series-s6e2`)

> Kaggle: https://www.kaggle.com/competitions/playground-series-s6e2

## 1. Problem and metric

_One paragraph: what the competition asks, what the target is, and why the metric matters._

- **Task:** _binary / multiclass / regression_
- **Target column:** `Heart Disease`
- **Metric:** `roc_auc`
- **Higher is better:** _yes / no_
- **Score gate (rule R5):** `_not set_` — the competition counts as
  solved only when the measured OOF score meets this target.

## 2. Solution algorithm

_Document the final approach: features, folds, models, ensemble, decision rule._

| Stage | Choice | Why |
| --- | --- | --- |
| Folds | _StratifiedKFold(5)_ | _keeps class balance across folds_ |
| Features | _to be documented_ | _domain reasoning, not a list_ |
| Models | _LightGBM / XGBoost / CatBoost_ | _measured, not asserted_ |
| Ensemble | _rank-mean / hill-climb fitted on OOF_ | _honest, out-of-sample selection_ |

## 3. Score matching

Copied from `train/metrics.json` — never edited by hand (rule R4).

| Metric | OOF mean | OOF std | Folds | Public LB | Gap (LB − OOF) | Target | Reached |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `roc_auc` | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ | `_not set_` | _pending_ |

> The CV-vs-leaderboard gap is the number that matters. A large negative gap
> means the validation split is not representative — duplicates, group leakage
> or distribution shift — so diagnose before adding models (rule R5).

## 4. What was tried and rejected

| Idea | Score | Verdict |
| --- | --- | --- |
| _baseline LightGBM + 5-fold CV_ | _pending_ | _keep until beaten with evidence_ |

## 5. Next steps

1. _Ranked, specific, with an expected effect — not "tune hyperparameters"._

---

_Maintained by the engine. Source of truth: `train/metrics.json`,
`train/report.md`, and the executed notebook copy in `train/`._
