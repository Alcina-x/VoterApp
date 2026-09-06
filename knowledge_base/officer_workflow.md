# Simulated Officer Workflow

## Recommended workflow

1. Sign in with an authorised demonstration account.
2. Start on the dashboard to review total records, processing rate, pending volume, anomaly count, hourly activity, and station performance.
3. Search by the exact synthetic voter ID or by a name fragment. Confirm the returned ID, station, status, and event details before drawing conclusions.
4. Open a station view to compare registered, processed, pending, queue-time, processing-time, and anomaly metrics.
5. Use the anomaly queue to understand why a generated record was flagged. A flag is a prompt for review, not a finding.
6. Use the assistant for read-only questions about records, analytics, and procedures.
7. Generate a report only when a current descriptive snapshot is needed.

## Search and interpretation

Voter IDs use the format `VOTER` followed by six digits. Polling stations use the format `PS-001` through `PS-050`. A processed record means only that the generated workflow completed. A pending record has not completed in the simulation. Neither status represents a real ballot, legal eligibility, registration decision, or election outcome.

When a search returns no record, verify spelling and the six-digit ID, search again, and route the case to simulated manual review. Never invent a record or infer missing data.

## Assistant question examples

- “Has VOTER001000 been processed?”
- “How is PS-014 performing?”
- “Which stations have the highest processing rate?”
- “How many records are pending?”
- “Show the hourly processing trend.”
- “Break down records by age group.”
- “What does an anomaly flag mean?”
- “What can you help me with?”
