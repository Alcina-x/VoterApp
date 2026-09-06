# System FAQ

## Purpose and scope

VoteAssist AI is an academic election-operations demonstration. It helps an officer explore a deterministic, read-only synthetic dataset and understand simulated workflow metrics. It is not an election management system, voter-registration system, legal adviser, or source of official results.

The dataset contains exactly 25,000 synthetic voter records and 50 synthetic polling stations. It is generated with random seed 42, so repeated runs produce the same records and metrics. The application is not connected to government systems, does not contain real personal information, cannot identify how a person voted, and must not be used to make eligibility, turnout, fraud, or misconduct determinations.

## What the assistant can answer

Ask about a voter ID such as `VOTER001000`, a station such as `PS-014`, dashboard totals, processed and pending counts, hourly processing activity, station comparisons, queue and processing times, anomaly flags, age or gender groups, districts, constituencies, simulated procedures, or the capabilities of the assistant.

## Data definitions

- **Processed** means a generated workflow event was marked `PROCESSING_COMPLETED`.
- **Pending** means the generated workflow has not completed.
- **Queue time** is a synthetic number of minutes before processing.
- **Processing time** is a synthetic duration for the workflow.
- **Anomaly** means a generated value differs from the synthetic baseline, such as an unusually short processing time, unusually long processing time, or abnormal queue time.
- **Processing rate** is processed records divided by registered synthetic records.

## Safety and limitations

An anomaly is a review signal, not proof of wrongdoing. Do not infer a person’s eligibility, identity, political preference, or real-world status from any response. Do not create, edit, or delete records through the assistant. Use the simulated manual-review procedure when a record appears missing or inconsistent, preserve the original details, and escalate to an authorised supervisor.

## Technical notes

The browser uses a protected API with a short-lived demo session token. Dashboard and assistant answers are generated from deterministic in-memory data and local procedure documents. The report builder is descriptive only; it does not certify results.
