# Enterprise Data Extraction & Classification

## Deliverable
`customer_records.csv` — 12 clean customer records extracted from an unstructured multi-channel support dump.

## Header
```
Record_ID,Customer_Name,Contact_Info,Date_Standardized,Source_Channel,Primary_Category,Secondary_Category,Sentiment,Urgency_Level,Action_Required
```

## Validation
- 10 columns on every row (header + 12 data rows)
- Record_IDs sequential REC-1001 → REC-1012
- All dates ISO `YYYY-MM-DD` (year defaulted to 2026 where omitted)
- Controlled vocabularies enforced for channel, categories, sentiment, urgency
- `Action_Required` = 3–6 words on every row
- Fields containing commas double-quoted; file re-parses cleanly via `csv` module

## SHA-256
`bd9696aa4f8100a5cbee22583b1dd7ece80d7b37feca71680db82f5bd02e5c5e`

## Rebuild
`python3 build_csv.py`
