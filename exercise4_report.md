# Exercise 4 – Analyse the Results

## 1. Evaluation scope

The evaluation contains **225 model-question runs**: 9 models × 25 questions.

The question set contains:
- 20 answerable DevOps/RAG questions
- 5 deliberately unanswerable questions (Q21–Q25)

The five unanswerable questions ask for an exact Kubernetes version, pod memory limit, cloud provider, database engine, and administrator name. These details are intentionally absent from the supplied knowledge base.

## 2. Method used for quality analysis

The existing CSV did not contain completed manual quality fields, so this analysis uses a **source-grounded rubric** over the generated answers.

For Q01–Q20, each answer was scored against the core concepts required by the supplied knowledge-base content. Partial concept coverage receives a partial score.

For Q21–Q25, a response receives full credit when it correctly refuses to invent information that is not present in the knowledge base.

This is a correctness/source-grounding rubric; it should **not** be described as a formal claim-level hallucination detector.

## 3. Model comparison

| Model | Quality (%) | Completion (%) | Avg latency (ms) | Avg total tokens | CPU peak (%) | Memory peak (%) | Retrieval recall | Blank answers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| granite4.2:latest | 98.0 | 100.0 | 41164.37 | 1049.84 | 47.26 | 73.28 | 0.85 | 0 |\n| rnj-1:latest | 95.3 | 100.0 | 7488.89 | 477.00 | 50.77 | 87.08 | 0.85 | 0 |\n| qwen3:latest | 95.2 | 100.0 | 19754.51 | 671.12 | 48.28 | 79.51 | 0.85 | 0 |\n| qwen3.5:4b-q8_0 | 93.0 | 96.0 | 78504.65 | 1768.04 | 48.54 | 78.61 | 0.85 | 1 |\n| mistral:latest | 89.9 | 100.0 | 5020.85 | 539.76 | 58.78 | 95.20 | 0.85 | 0 |\n| dolphin3:latest | 87.5 | 100.0 | 4858.95 | 441.00 | 56.03 | 90.71 | 0.85 | 0 |\n| hermes3:latest | 85.7 | 100.0 | 5525.36 | 457.28 | 46.62 | 91.38 | 0.85 | 0 |\n| gemma3:1b | 70.1 | 100.0 | 1169.98 | 423.92 | 30.45 | 73.48 | 0.85 | 0 |\n| qwen3.5:0.8b | 33.3 | 40.0 | 28861.61 | 3649.56 | 20.63 | 79.32 | 0.85 | 15 |\n
## 4. Findings

### Accuracy / response quality

**granite4.2:latest** achieved the highest rubric-based quality score at **98.0%**.

The next strongest models were:
- rnj-1:latest: **95.3%**
- qwen3:latest: **95.2%**
- qwen3.5:4b-q8_0: **93.0%**

The weakest result was qwen3.5:0.8b at **33.3%**, largely because it produced **15 blank answers out of 25**.

### Retrieval-based responses

Average retrieval recall is **0.85 for every model** in the supplied model summary. This is expected because all models use the same RAG retrieval pipeline and the same retrieved context for each question.

Therefore, **retrieval quality does not distinguish the LLMs in this experiment**. Differences in final answers are primarily attributable to generation/response quality rather than a different retrieval result.

### Code test-pass rate

A code test-pass rate is **not applicable** to this particular 25-question dataset. None of the questions is an executable coding task with a test suite.

It would be incorrect to invent a code pass-rate comparison.

### Latency

The fastest model was **gemma3:1b** at **1169.98 ms average latency**.

For comparison:
- gemma3:1b: **1169.98 ms**
- dolphin3:latest: **4858.95 ms**
- mistral:latest: **5020.85 ms**
- hermes3:latest: **5525.36 ms**
- rnj-1:latest: **7488.89 ms**
- qwen3:latest: **19754.51 ms**
- qwen3.5:0.8b: **28861.61 ms**
- granite4.2:latest: **41164.37 ms**
- qwen3.5:4b-q8_0: **78504.65 ms**

Thus gemma3:1b is approximately **67× faster than qwen3.5:4b-q8_0** on average.

### Computational resources

The lowest recorded average peak CPU usage was **qwen3.5:0.8b at 20.63%**.

The lowest recorded average peak memory usage was **granite4.2:latest at 73.28%**.

However, low resource consumption alone does not imply better quality. qwen3.5:0.8b demonstrates this clearly: it has low CPU usage (**20.63%**) but only **40% answer completion** and the lowest quality score.

## 5. Quality–latency–resource trade-off

The most accurate model is **not automatically the most efficient model**.

**granite4.2:latest** has the highest quality score (**98.0%**) but requires about **41.16 seconds average latency**.

**gemma3:1b** has a lower quality score (**70.1%**) but averages only **1.17 seconds latency**, with **30.45% CPU peak** and **73.48% memory peak**.

This is a clear quantitative quality–latency trade-off.

A particularly interesting middle ground is **rnj-1:latest**: its quality (**95.3%**) is close to the top model, while its average latency (**7.49 s**) is far below granite4.2:latest (**41.16 s**).

**mistral:latest** and **dolphin3:latest** provide another practical middle tier, with roughly 5-second average latency and quality scores of **89.9%** and **87.5%**, respectively.

## 6. Hallucination / unanswerable-question behaviour

The dataset includes five questions whose answers are intentionally absent from the knowledge base. Correct behaviour is to explicitly say that the information is unavailable rather than inventing a value.

All models except qwen3.5:0.8b correctly refused all five unanswerable questions. qwen3.5:0.8b produced **one blank response (Q24)** and therefore had **80% refusal/completion coverage** on the unanswerable set.

A true claim-level hallucination percentage cannot be calculated from the existing CSV because the fields `total_factual_claims`, `unsupported_claims`, and `hallucination_rate_pct` were not populated. The unanswerable-question result is therefore the defensible quantitative hallucination proxy available from this dataset.

## 7. Overall conclusion

The results show a strong **quality–latency–resource trade-off** rather than one universally best model.

- **Best quality:** granite4.2:latest (**98.0%**), but it is very slow (**41.16 s** average).
- **Best raw speed / lightweight option:** gemma3:1b (**1.17 s**, **30.45% CPU peak**, **73.48% memory peak**), but its quality score is substantially lower (**70.1%**).
- **Strong quality/latency compromise:** rnj-1:latest (**95.3% quality**, **7.49 s latency**).
- **Practical middle tier:** mistral:latest and dolphin3:latest, both around 5 seconds average latency.
- **Poor efficiency:** qwen3.5:4b-q8_0, with **78.50 s average latency**, despite high quality.
- **Weakest overall:** qwen3.5:0.8b, because of **15 blank answers**, only **40% answer completion**, and the lowest quality score.

Therefore, the most accurate model is **not the most efficient**. The best model depends on the application's priority: maximum answer quality, minimum latency, or a balanced quality/resource trade-off.
