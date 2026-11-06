# 3-minute demo script

Run the real data first: `python -m scripts.build_snapshot --districts rajshahi`, then start both servers. Say only what the screen shows.

| Time | Do | Say |
| --- | --- | --- |
| 0:00 | Stage 01, select Rajshahi | "Farmers still follow calendar dates, but the rains have moved. BoponX turns NASA data into a decision." |
| 0:30 | Show the globe, NASA layers, the fusion numbers | "Recent NASA POWER data through <data_through>, and EONET hazards. These are visual and context layers." |
| 1:00 | Stage 02, the shift card | Read the **actual** advisory sentence, its 95% interval and p-value. If there is no reliable shift, say that. Point at the `STABLE` or `REVIEW` badge. |
| 1:40 | Open the sensitivity pills and the year dots | "Every dot is one year computed from NASA POWER daily rainfall. We re-ran it with other definitions." |
| 2:00 | Copy the SMS | "One SMS segment in English and Bangla, with the DAE helpline." |
| 2:20 | What-if sliders, strategies A/B/C | "We compare three strategies and do not rank them until local rules are approved." |
| 2:45 | Stage 03, print the A4 plan | "A 90-day plan a farmer can carry." |

**Offline fallback (60 s):** start with `OFFLINE=1`. The snapshot supplies the same real data. If a district has no snapshot the card says `UNAVAILABLE` and shows no numbers. That is intended.
