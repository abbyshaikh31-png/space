#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build + validate customers.csv (REC-1001 .. REC-1060) from the raw dump."""
import csv, re, sys

HEADER = ["Record_ID","Customer_Name","Contact_Info","Date_Standardized","Source_Channel",
          "Primary_Category","Secondary_Category","Sentiment","Urgency_Level","Action_Required"]

ROWS = [
("REC-1001","Mark Johnson","mark.j88@gmail.com; ORD-9921","2026-11-02","Chat","Logistics","Cancellation","Negative","Medium","Trace order ORD-9921 and update"),
("REC-1002","Kavita Sharma","k.sharma@techcorp.in; +91-9876543210","2026-11-03","Email","Bug","Billing","Negative","Critical","Restore webhook and refund overcharge"),
("REC-1003","Unknown","+14158902311","2026-11-04","SMS","Cancellation","Account_Auth","Neutral","Medium","Confirm opt-out and account deletion"),
("REC-1004","alex_dev_99","None","2026-11-04","Social","Praise","Feature_Request","Positive","Low","Thank user and log dark mode"),
("REC-1005","Mrs. Gable","555-0192; Order 77410","2026-11-05","Phone","Logistics","Billing","Negative","High","Approve refund for water-damaged headphones"),
("REC-1006","Unknown","anon_user44@proton.me","2026-11-05","Form","Account_Auth","Billing","Negative","Critical","Lift suspension and restore paid access"),
("REC-1007","Diego M.","None","2026-11-06","Chat","General_Query","None","Neutral","Low","Send guide on adding team members"),
("REC-1008","Rachel Zane","rachel.zane@pearson.com; INV-2026-88","2026-11-06","Email","Billing","General_Query","Neutral","High","Send W-9 and SOC2 documents"),
("REC-1009","fitness_with_tina","None","2026-11-07","Social","Bug","Praise","Mixed","Low","Fix iOS profile photo rotation bug"),
("REC-1010","Arthur Pendelton","+44 20 7946 0991","2026-11-07","Phone","Billing","None","Negative","Medium","Call back and honor VIP50 code"),
("REC-1011","nina_k","None","2026-11-08","Social","Bug","None","Negative","Medium","Reproduce dashboard filter freezing issue"),
("REC-1012","Robert Miller","bob.builder@construct.co; card ending 4412","2026-11-08","Email","Billing","None","Negative","Critical","Reverse duplicate charges and escalate legal"),
("REC-1013","Sneha Rao","sneha.rao@blr.org","2026-11-08","Form","Feature_Request","None","Positive","Low","Log UPI and RuPay payment request"),
("REC-1014","Unknown","+1-202-555-0144; Order 55120","2026-11-09","SMS","Logistics","None","Negative","High","Open carrier trace for missing parcel"),
("REC-1015","Visitor8821","None","2026-11-09","Chat","General_Query","None","Neutral","Low","Explain free trial and pricing"),
("REC-1016","Liam Vance","ceo@startupx.io; AC-909","2026-11-09","Email","Cancellation","Billing","Mixed","High","Cancel Pro plan before the 15th"),
("REC-1017","gamer_joe_22","None","2026-11-10","Social","Account_Auth","Bug","Negative","Critical","Restore 2FA access for locked account"),
("REC-1018","David Wallace","dwallace@dunder.com","2026-11-10","Phone","General_Query","Billing","Neutral","Low","Route to sales for volume pricing"),
("REC-1019","Hannah Abbott","None","2026-11-10","Form","Bug","None","Negative","Medium","Fix corrupt Excel export on macOS"),
("REC-1020","Priya Nair","priya.nair@kerala.in; Order 99812","2026-11-10","Email","Billing","None","Neutral","Medium","Switch billing tier and refund difference"),
]
]<]minimax[>[