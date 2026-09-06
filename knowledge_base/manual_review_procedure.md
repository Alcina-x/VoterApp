# Simulated Manual Review

## When to use it

Use simulated manual review when an exact synthetic voter ID cannot be found, a returned record appears inconsistent, an event is missing, or an anomaly needs contextual review. The assistant cannot resolve identity, eligibility, registration, or ballot questions.

## Steps

1. Confirm the exact `VOTER######` identifier and repeat the search.
2. Record the station, status, queue time, processing time, anomaly type, and relevant event timestamps.
3. Preserve the original synthetic event details; do not overwrite or manufacture values.
4. Describe the discrepancy in neutral language.
5. Route the case to an authorised simulated supervisor for review.
6. Close the case only after the supervisor confirms the simulated disposition.

## Anomaly guidance

The current demonstration can flag unusually short processing, unusually long processing, or abnormal queue time. Compare the value with the displayed synthetic baseline and inspect related station metrics. These patterns may be intentional generated test data. They are not evidence of fraud, misconduct, or an invalid vote.

## Prohibited actions

Do not create a missing voter, change a processing status, delete an event, infer a real-world identity, or make an eligibility or outcome decision. Do not expose demo credentials or session tokens in a case note.
