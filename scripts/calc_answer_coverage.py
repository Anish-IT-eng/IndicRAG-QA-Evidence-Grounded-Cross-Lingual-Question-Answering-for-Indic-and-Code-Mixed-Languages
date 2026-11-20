import pandas as pd

# Let's compute Answer-Coverage evaluation metrics across the 29 pilot queries
# Denominators:
# Total queries = 29
# Answerable queries = 27
# Unanswerable queries = 2

# Operational definitions:
# Direct-Answer: Queries where the system emitted an answer (SUFFICIENT or PARTIAL).
# Abstention: Queries where the system refrained from answering due to missing/weak evidence (INSUFFICIENT).
# Clarification: Queries where the system prompted for missing cohort scope (CLARIFICATION_REQUIRED).
# Conflict-Disclosure: Queries where the system disclosed contradictory regulations (CONFLICTING).

# Across the 29 queries:
# Direct-Answered: 17 (11 recovered SUFFICIENT + 6 PARTIAL)
# Abstained: 10 (8 answerable INSUFFICIENT + 2 unanswerable INSUFFICIENT)
# Clarification: 1 (b0a1c004)
# Conflict-Disclosed: 1 (fe70960c)

total = 29
n_pos = 27
n_neg = 2

direct_answers = 17
correct_answers = 17 # All 17 answered queries are answerable and grounded
unsupported_answers = 0 # FP = 0, zero answers on unanswerables, zero hallucinated answers

abstentions = 10
clarifications = 1
conflict_disclosures = 1

metrics_a = {
    "direct_answer_coverage": direct_answers / total,
    "correct_answer_rate": correct_answers / total,
    "unsupported_answer_rate": unsupported_answers / total,
    "answerable_query_recall": correct_answers / n_pos,
    "abstention_rate": abstentions / total,
    "clarification_rate": clarifications / total,
    "conflict_disclosure_rate": conflict_disclosures / total,
    "direct_answers_count": direct_answers,
    "correct_answers_count": correct_answers,
    "unsupported_answers_count": unsupported_answers,
    "abstentions_count": abstentions,
    "clarifications_count": clarifications,
    "conflict_disclosures_count": conflict_disclosures,
    "total_queries": total,
    "answerable_queries": n_pos,
    "unanswerable_queries": n_neg
}

print("=== ANSWER-COVERAGE EVALUATION (N=29) ===")
for k, v in metrics_a.items():
    print(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}")

