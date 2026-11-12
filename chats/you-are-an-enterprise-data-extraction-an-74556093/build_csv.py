import csv

HEADER = ["Record_ID","Customer_Name","Contact_Info","Date_Standardized","Source_Channel","Primary_Category","Secondary_Category","Sentiment","Urgency_Level","Action_Required"]

VALID_PRIMARY = {"Billing","Bug","Feature_Request","Account_Auth","Logistics","Cancellation","Praise","General_Query"}
VALID_SECONDARY = VALID_PRIMARY | {"None"}
VALID_SENT = {"Positive","Neutral","Negative","Mixed"}
VALID_URG = {"Critical","High","Medium","Low"}
VALID_CHAN = {"Email","Chat","Phone","Social","SMS","Form"}

ROWS = """
REC-1001|Mark Johnson|mark.j88@gmail.com; ORD-9921|2026-11-02|Chat|Logistics|Cancellation|Negative|High|Trace order and confirm shipment
REC-1002|Kavita Sharma|k.sharma@techcorp.in; +91-9876543210|2026-11-03|Email|Bug|Billing|Negative|Critical|Escalate API outage and fix overcharge
REC-1003|Unknown|+14158902311|2026-11-04|SMS|Cancellation|Account_Auth|Neutral|High|Confirm opt-out and deletion request
REC-1004|Alex|@alex_dev_99|2026-11-04|Social|Praise|Feature_Request|Positive|Low|Thank user and log dark mode request
REC-1005|Mrs. Gable|555-0192; 77410|2026-11-05|Phone|Logistics|Billing|Negative|High|Process full refund for damaged order
REC-1006|Unknown|anon_user44@proton.me|2026-11-05|Form|Account_Auth|Billing|Negative|Critical|Reinstate suspended paid account urgently
REC-1007|Diego M.|None|2026-11-06|Chat|General_Query|None|Neutral|Low|Send team invite instructions
REC-1008|Rachel Zane|rachel.zane@pearson.com; INV-2026-88|2026-11-06|Email|Billing|General_Query|Neutral|High|Send W-9 and SOC2 documents
REC-1009|Tina|@fitness_with_tina|2026-11-07|Social|Praise|Bug|Mixed|Low|Log iOS profile photo rotation bug
REC-1010|Arthur Pendelton|+44 20 7946 0991|2026-11-07|Phone|Billing|None|Neutral|Medium|Investigate VIP50 discount code failure
REC-1011|Nina|@nina_k|2026-11-08|Chat|Bug|None|Neutral|Medium|Reproduce dashboard filter freeze
REC-1012|Robert Miller|bob.builder@construct.co; card ending 4412|2026-11-08|Email|Billing|None|Negative|Critical|Reverse duplicate charges immediately
REC-1013|Sneha Rao|sneha.rao@blr.org|2026-11-08|Form|Feature_Request|Billing|Positive|Low|Log UPI and RuPay request
REC-1014|Unknown|+1-202-555-0144; 55120|2026-11-09|SMS|Logistics|None|Negative|High|Open missing delivery investigation
REC-1015|Unknown|None|2026-11-09|Chat|General_Query|None|Neutral|Low|Share free trial and plan details
REC-1016|Liam Vance|ceo@startupx.io; AC-909|2026-11-09|Email|Cancellation|Billing|Neutral|High|Cancel Pro plan before renewal
REC-1017|Joe|@gamer_joe_22|2026-11-10|Social|Account_Auth|None|Negative|Critical|Fix 2FA SMS delivery and restore access
REC-1018|David Wallace|dwallace@dunder.com|2026-11-10|Phone|General_Query|Billing|Neutral|Low|Route 250-seat quote to sales
REC-1019|Hannah Abbott|None|2026-11-10|Form|Bug|None|Negative|Medium|Fix corrupted Excel export file
REC-1020|Priya Nair|priya.nair@kerala.in; 99812|2026-11-10|Email|Billing|Cancellation|Neutral|Medium|Switch plan to monthly and refund
"""