# Usability Study – System Usability Scale (SUS)

**Owner:** Nguyễn Vi Kiên · **When:** Week 7 · **Participants:** 10–15 HCMUT students · **Reference:** J. Brooke, "SUS: A 'quick and dirty' usability scale," in *Usability Evaluation in Industry*, Taylor & Francis, 1996, pp. 189–194.

## 1. Questionnaire (standard SUS wording)

Response scale for every item: **1 = Strongly disagree, 2, 3, 4, 5 = Strongly agree**. Participants answer every item, and choose 3 if they are unsure. In the Vietnamese translation, "system" is translated as "hệ thống" and an English original is provided alongside.

| # | Statement | 1 | 2 | 3 | 4 | 5 |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | I think that I would like to use this system frequently. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 2 | I found the system unnecessarily complex. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 | I thought the system was easy to use. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4 | I think that I would need the support of a technical person to be able to use this system. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 | I found the various functions in this system were well integrated. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 6 | I thought there was too much inconsistency in this system. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 7 | I would imagine that most people would learn to use this system very quickly. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 8 | I found the system very cumbersome to use. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 9 | I felt very confident using the system. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 10 | I needed to learn a lot of things before I could get going with this system. | ☐ | ☐ | ☐ | ☐ | ☐ |

## 2. Scoring method

1. For **odd** items (1, 3, 5, 7, 9): contribution = response − 1.
2. For **even** items (2, 4, 6, 8, 10): contribution = 5 − response.
3. SUS score = (sum of the 10 contributions) × 2.5, giving a range of 0–100.
4. Report the mean, standard deviation, median, minimum, maximum and a 95 % confidence interval (t-distribution, n − 1 degrees of freedom).
5. Interpretation: the SUS score is **not a percentage**. The commonly cited average across published studies is about 68, so we use **≥ 68** as our target (criterion K5). Individual items should not be interpreted on their own.

Worked example: responses (4, 2, 5, 1, 4, 2, 5, 2, 4, 1) give contributions (3, 3, 4, 4, 3, 3, 4, 3, 3, 4), a sum of 34, and a SUS score of 34 × 2.5 = **85.0**.

## 3. Test protocol

**Participants.** 10–15 HCMUT students recruited voluntarily (class groups and friends of the team, excluding team members). Mix: at least 5 from the Faculty of CSE and at least 3 from other faculties; years 1–4 and graduate students. No incentives that could bias the answers.

**Ethics and consent.** Participation is voluntary and anonymous. Participants can stop at any time. We record only the participant code (P01…), faculty, year of study, and self-rated search experience (1–5). We collect no names, student IDs, screen recordings or query logs. Verbal consent is recorded on the session sheet.

**Setup.** One team laptop running `streamlit run src/app.py` (v1.0.0 build) in Chrome, with the index pre-built. Each session is moderated by Kiên, with one note-taker (rotating among team members). Sessions take 20–25 minutes, either in person or by screen-share.

**Script.**

1. Welcome and consent (2 min): "We are testing the system, not you."
2. Background questions (1 min).
3. Tasks (10–12 min). Think aloud. The moderator does not help unless the participant is stuck for more than 2 minutes, and records any assistance.
4. SUS questionnaire (3 min), completed immediately after the tasks and before any discussion.
5. Debrief (3 min): "What was most useful? What was most confusing? What would you change?"

**Tasks.**

| # | Task given to participant | Success criterion | Measures |
| :---: | :--- | :--- | :--- |
| T1 | "Find papers about translating between languages that have very little training data." | Opens a relevant result in the top 5 | Completion, time, number of queries |
| T2 | "Show only papers from 2024 or later in category cs.CL." | Correct filters applied | Completion, errors |
| T3 | "Read the full abstract of the most relevant paper and open its PDF." | Abstract expanded; arXiv PDF opened | Completion, time |
| T4 | "Copy the IEEE citation for that paper." | IEEE citation in the clipboard | Completion |
| T5 | "Find other papers similar to this one." | Uses Find similar / Similar tab | Completion, time |
| T6 | "Find what the percentage score means." | Locates the explanation in the About tab | Completion |

## 4. Results (to be filled in after the study)

### 4.1 Per-participant data

| Participant | Faculty | Year | Search exp. (1–5) | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | Q9 | Q10 | SUS | Tasks completed (/6) |
| :--- | :--- | :---: | :---: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| P01 | | | | | | | | | | | | | | | |
| P02 | | | | | | | | | | | | | | | |
| P03 | | | | | | | | | | | | | | | |
| P04 | | | | | | | | | | | | | | | |
| P05 | | | | | | | | | | | | | | | |
| P06 | | | | | | | | | | | | | | | |
| P07 | | | | | | | | | | | | | | | |
| P08 | | | | | | | | | | | | | | | |
| P09 | | | | | | | | | | | | | | | |
| P10 | | | | | | | | | | | | | | | |
| P11 | | | | | | | | | | | | | | | |
| P12 | | | | | | | | | | | | | | | |
| P13 | | | | | | | | | | | | | | | |
| P14 | | | | | | | | | | | | | | | |
| P15 | | | | | | | | | | | | | | | |

### 4.2 Summary

| Statistic | Value |
| :--- | :--- |
| n | |
| Mean SUS | |
| Standard deviation | |
| Median | |
| Min / Max | |
| 95 % CI | |
| Target ≥ 68 met? | |

### 4.3 Task metrics

| Task | Completion rate | Mean time (s) | Assists | Main issues observed |
| :--- | :---: | :---: | :---: | :--- |
| T1 | | | | |
| T2 | | | | |
| T3 | | | | |
| T4 | | | | |
| T5 | | | | |
| T6 | | | | |

### 4.4 Qualitative findings and resulting changes

| Finding | Frequency (n) | Severity | Change made / issue # |
| :--- | :---: | :---: | :--- |
| | | | |
