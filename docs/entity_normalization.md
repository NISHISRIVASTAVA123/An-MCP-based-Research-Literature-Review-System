# Entity Normalization and Synonym Resolution

## 1. Motivation and Conservative Resolution

In academic research, scientific terms frequently appear in varying surface forms:
- "CNN", "ConvNet", "Convolutional Neural Network", "convolutional neural networks"
- "f1-score", "f-measure", "F1", "macro-F1"
- "LIAR dataset", "LIAR benchmark", "liar"

However, overly aggressive or naive fuzzy matching presents severe scientific hazards. Merging distinct benchmark datasets (such as `GLUE` and `SuperGLUE`) or distinct model variants (such as `GPT-3` and `GPT-4`) produces false cross-paper syntheses and distorts downstream research gap assessments.

Therefore, our framework enforces **Conservative Entity Resolution**:
1. Merging occurs only under high-confidence rule-based mappings or human validation.
2. Datasets require explicit identifier checks or exact dictionary equivalence; loose fuzzy clustering across datasets is strictly prohibited.
3. Ambiguous aliases are recorded in an **Unverified Alias Queue** rather than guessed.
4. Human domain experts can review and override any alias mapping non-destructively.

---

## 2. Normalization Engine Architecture

```
Raw Surface String
       │
       ▼
[ Token Cleaning & Whitespace Normalization ]
       │
       ▼
[ Database Alias Registry Lookup ] ──(Found?)──► Return Verified Canonical
       │ (Not Found)
       ▼
[ Curated Domain Dictionaries ] ─────(Match?)──► Upsert Alias & Return (Conf: 1.0)
       │ (Not Found)
       ▼
[ Token Stemming / Suffix Normalization ] (Match?)──► Upsert Alias & Return (Conf: 0.90)
       │ (Not Found)
       ▼
[ Conservative Fallback ] ──────────► Register as 'unverified_alias' (Conf: 0.60, Verified: False)
```

---

## 3. Resolution Tiers and Confidence Scoring

| Resolution Method | Confidence | Is Verified | Behavior |
|---|---|---|---|
| `manual_user_override` | **1.0** | `True` | Set directly by human researcher via API or dashboard; takes immediate precedence over automated rules. |
| `exact_rule` | **1.0** | `True` | Direct match in curated method, model family, metric, or dataset dictionary. |
| `stemmed_rule` | **0.90** | `True` | Matched after removing plural suffixes (`s`, `es`, `ies`) or verbal suffixes (`ed`, `ing`) without dropping token length below threshold. |
| `unverified_alias` | **0.60** | `False` | Conservative fallback creating entity under its clean surface form and logging an unverified alias record for human inspection. |

---

## 4. Curated Domain Dictionaries

### 4.1 Methodology Dictionary (`METHOD_DICTIONARY`)
- Maps common abbreviations, capitalization variants, and synonyms to canonical scientific methodology names.
- Examples:
  - `cnn`, `convnet`, `convolutional network` -> **Convolutional Neural Network**
  - `transformer`, `transformers`, `transformer architecture` -> **Transformer**
  - `bert`, `roberta`, `gpt` -> Canonical representations
  - `shap`, `shapley values` -> **SHAP**
  - `lime`, `local interpretable model-agnostic explanations` -> **LIME**
  - `rf`, `random forests` -> **Random Forest**
  - `rag` -> **Retrieval-Augmented Generation**

### 4.2 Model Families Dictionary (`MODEL_FAMILIES`)
- Distinguishes model architectures from general methodologies.
- Groups versioned instances to canonical family names (e.g. `llama-2`, `llama` -> **LLaMA**; `gpt-3`, `gpt-4` -> **GPT**; `resnet` -> **ResNet**).

### 4.3 Evaluation Metrics Dictionary (`METRIC_DICTIONARY`)
- Unifies evaluation metric names and reporting conventions.
- Examples:
  - `f1`, `f1-score`, `f-measure`, `f_score` -> **F1-Score**
  - `acc`, `accuracy`, `top-1 accuracy` -> **Accuracy**
  - `auc`, `roc-auc`, `roc_auc`, `auc-roc` -> **AUC-ROC**
  - `bleu`, `bleu-4` -> **BLEU**
  - `rouge`, `rouge-l` -> **ROUGE**

### 4.4 Benchmark Dataset Dictionary (`DATASET_DICTIONARY`)
- Standardizes major academic benchmark datasets without cross-dataset conflation.
- Examples:
  - `liar`, `liar dataset` -> **LIAR**
  - `fakenewsnet`, `fake news net` -> **FakeNewsNet**
  - `politifact` -> **PolitiFact**
  - `gossipcop` -> **GossipCop**
  - `glue`, `glue benchmark` -> **GLUE** (kept strictly distinct from `superglue`)

---

## 5. Manual Resolution Workflow & API

When automated extractors encounter an ambiguous or novel domain term, the system registers the alias with `is_verified = False`.

Researchers can resolve this via the REST API:

```http
POST /api/evidence-graph/entity-resolution
Content-Type: application/json

{
  "entity_type": "METHOD",
  "surface_form": "lime feature weightings",
  "canonical_name": "LIME",
  "override_notes": "Expert synonym resolution mapping token attribution to LIME"
}
```

**Response**:
```json
{
  "id": "alias-5b72e...",
  "raw_string": "lime feature weightings",
  "normalized_name": "LIME",
  "entity_type": "method",
  "resolution_method": "manual_user_override",
  "confidence": 1.0,
  "is_verified": true,
  "created_at": "2026-11-24T11:17:08.123456Z"
}
```

All subsequent graph synchronization runs immediately apply this canonical mapping.
