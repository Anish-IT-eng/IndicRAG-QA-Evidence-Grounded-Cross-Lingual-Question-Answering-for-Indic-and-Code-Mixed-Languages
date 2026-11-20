import json
import time
import urllib.request
import urllib.error
import sys
import os
import uuid

# Add backend to path to use conversation_store for seeding prior turns
sys.path.insert(0, os.path.abspath("backend"))
from app.query.conversation_store import save_turn

API_URL = "http://127.0.0.1:8000/query"

def send_query(payload: dict) -> dict:
    t0 = time.time()
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            data["_duration"] = time.time() - t0
            return data
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return {"status": "error", "code": e.code, "detail": err_body, "_duration": time.time() - t0}

results = {}

print("=" * 80)
print("RUNNING R2.1 FINAL VERIFICATION: 10 REGRESSION TESTS VIA LIVE HTTP API")
print("=" * 80)

# TEST 1: Fresh-session disagreement
print("\n--- Test 1: Fresh-session disagreement ---")
sess1 = f"verify_fresh_{uuid.uuid4().hex[:8]}"
res1 = send_query({
    "query": "your answer is wrong",
    "session_id": sess1,
    "sequential_fallback": True
})
t1_pass = (
    res1.get("status") == "answered" and
    res1.get("repair_action") == "no_prior_context" and
    "do not have a preceding question" in res1.get("answer", "")
)
results["test1_fresh_session"] = {
    "passed": t1_pass,
    "repair_action": res1.get("repair_action"),
    "latency": round(res1.get("_duration", 0), 3),
    "snippet": res1.get("answer", "")[:120]
}
print(f"Test 1 Passed: {t1_pass} (latency: {res1.get('_duration', 0):.3f}s)")

# TEST 2: Incorrect calendar event correction
print("\n--- Test 2: Incorrect calendar event correction ---")
sess2 = f"verify_event_corr_{uuid.uuid4().hex[:8]}"
save_turn(
    session_id=sess2,
    user_id=None,
    user_query="When will odd semester make-up examination date sheet be displayed?",
    assistant_answer="The Odd Semester Make-up Examination date sheet is displayed on 18-01-2027.",
    evidence_status="sufficient"
)
res2 = send_query({
    "query": "You gave the make-up examination date, but I asked about regular end semester examinations.",
    "session_id": sess2,
    "sequential_fallback": True
})
t2_pass = (
    res2.get("repair_action") == "calendar_schedule_repaired" and
    "10-12-2026" in res2.get("answer", "") and
    "22-12-2026" in res2.get("answer", "")
)
results["test2_incorrect_calendar_event"] = {
    "passed": t2_pass,
    "repair_action": res2.get("repair_action"),
    "latency": round(res2.get("_duration", 0), 3),
    "snippet": res2.get("answer", "")[:140]
}
print(f"Test 2 Passed: {t2_pass} (latency: {res2.get('_duration', 0):.3f}s)")

# TEST 3: Calendar date correction
print("\n--- Test 3: Calendar date correction ---")
sess3 = f"verify_date_corr_{uuid.uuid4().hex[:8]}"
save_turn(
    session_id=sess3,
    user_id=None,
    user_query="When do odd semester examinations start?",
    assistant_answer="The event starts on 25-01-2027.",
    evidence_status="sufficient"
)
res3 = send_query({
    "query": "The date is incorrect, check the schedule again.",
    "session_id": sess3,
    "sequential_fallback": True
})
t3_pass = (
    res3.get("repair_action") == "calendar_schedule_repaired" and
    "10-12-2026" in res3.get("answer", "") and
    "Thursday" in res3.get("answer", "")
)
results["test3_calendar_date_correction"] = {
    "passed": t3_pass,
    "repair_action": res3.get("repair_action"),
    "latency": round(res3.get("_duration", 0), 3),
    "snippet": res3.get("answer", "")[:140]
}
print(f"Test 3 Passed: {t3_pass} (latency: {res3.get('_duration', 0):.3f}s)")

# TEST 4: Attendance threshold disagreement
print("\n--- Test 4: Attendance threshold disagreement ---")
sess4 = f"verify_att_thresh_{uuid.uuid4().hex[:8]}"
save_turn(
    session_id=sess4,
    user_id=None,
    user_query="What is the minimum attendance requirement?",
    assistant_answer="70% minimum attendance is required in each course.",
    evidence_status="sufficient"
)
res4 = send_query({
    "query": "Attendance requirement is 75 percent, not 70 percent.",
    "session_id": sess4,
    "sequential_fallback": True
})
t4_pass = (
    res4.get("repair_action") == "factual_reconciliation" and
    "75%" in res4.get("answer", "") and
    "70%" in res4.get("answer", "")
)
results["test4_attendance_threshold"] = {
    "passed": t4_pass,
    "repair_action": res4.get("repair_action"),
    "latency": round(res4.get("_duration", 0), 3),
    "snippet": res4.get("answer", "")[:140]
}
print(f"Test 4 Passed: {t4_pass} (latency: {res4.get('_duration', 0):.3f}s)")

# TEST 5: Programme/cohort mismatch
print("\n--- Test 5: Programme/cohort mismatch ---")
sess5 = f"verify_cohort_{uuid.uuid4().hex[:8]}"
save_turn(
    session_id=sess5,
    user_id=None,
    user_query="What is the attendance requirement?",
    assistant_answer="Students must maintain 75% attendance under current regulations.",
    evidence_status="sufficient"
)
res5 = send_query({
    "query": "I am from 2017 batch, these new rules don't apply to my cohort.",
    "session_id": sess5,
    "sequential_fallback": True
})
t5_pass = (
    res5.get("repair_action") in ("cohort_realigned", "cohort_scope_clarified") and
    "2017" in res5.get("answer", "")
)
results["test5_programme_cohort_mismatch"] = {
    "passed": t5_pass,
    "repair_action": res5.get("repair_action"),
    "latency": round(res5.get("_duration", 0), 3),
    "snippet": res5.get("answer", "")[:140]
}
print(f"Test 5 Passed: {t5_pass} (latency: {res5.get('_duration', 0):.3f}s)")

# TEST 6: Medical exception disagreement
print("\n--- Test 6: Medical exception disagreement ---")
sess6 = f"verify_med_ex_{uuid.uuid4().hex[:8]}"
save_turn(
    session_id=sess6,
    user_id=None,
    user_query="What is the minimum attendance requirement to appear in examinations?",
    assistant_answer="75% minimum aggregate attendance is required to appear in examinations.",
    evidence_status="sufficient"
)
res6 = send_query({
    "query": "tumne exception miss kar diya, medical relaxation bhi hai",
    "session_id": sess6,
    "sequential_fallback": True
})
t6_pass = (
    res6.get("repair_action") == "exception_incorporated" and
    ("10%" in res6.get("answer", "") or "65%" in res6.get("answer", "") or "30.1(v)" in res6.get("answer", ""))
)
results["test6_medical_exception"] = {
    "passed": t6_pass,
    "repair_action": res6.get("repair_action"),
    "latency": round(res6.get("_duration", 0), 3),
    "snippet": res6.get("answer", "")[:140]
}
print(f"Test 6 Passed: {t6_pass} (latency: {res6.get('_duration', 0):.3f}s)")

# TEST 7: Contradictory source documents
print("\n--- Test 7: Contradictory source documents ---")
sess7 = f"verify_contra_{uuid.uuid4().hex[:8]}"
save_turn(
    session_id=sess7,
    user_id=None,
    user_query="What is the attendance rule?",
    assistant_answer="Attendance requirement is 75% under university notices.",
    evidence_status="sufficient"
)
res7 = send_query({
    "query": "Notification 307 states 75% but Ordinance Clause 30.1 states 70%",
    "session_id": sess7,
    "sequential_fallback": True
})
t7_pass = (
    res7.get("repair_action") == "factual_reconciliation" and
    "Notification 307/2022" in res7.get("answer", "") and
    "Clause 30.1" in res7.get("answer", "")
)
results["test7_contradictory_sources"] = {
    "passed": t7_pass,
    "repair_action": res7.get("repair_action"),
    "latency": round(res7.get("_duration", 0), 3),
    "snippet": res7.get("answer", "")[:140]
}
print(f"Test 7 Passed: {t7_pass} (latency: {res7.get('_duration', 0):.3f}s)")

# TEST 8: Missing evidence
print("\n--- Test 8: Missing evidence (unanswerable / clarification) ---")
sess8 = f"verify_missing_ev_{uuid.uuid4().hex[:8]}"
save_turn(
    session_id=sess8,
    user_id=None,
    user_query="What is the policy for drone flying inside hostel rooms?",
    assistant_answer="UNANSWERABLE — No verified policy exists in university records.",
    evidence_status="insufficient"
)
res8_t2 = send_query({
    "query": "your answer is wrong, check again",
    "session_id": sess8,
    "sequential_fallback": True
})
t8_pass = (
    res8_t2.get("status") in ("unanswerable", "answered") and
    ("Upload Custom PDF" in res8_t2.get("answer", "") or "UNANSWERABLE" in res8_t2.get("answer", "") or "Batch & Program" in res8_t2.get("answer", ""))
)
results["test8_missing_evidence"] = {
    "passed": t8_pass,
    "repair_action": res8_t2.get("repair_action"),
    "latency": round(res8_t2.get("_duration", 0), 3),
    "snippet": res8_t2.get("answer", "")[:140]
}
print(f"Test 8 Passed: {t8_pass} (latency: {res8_t2.get('_duration', 0):.3f}s)")

# TEST 9: Hindi and Hinglish feedback
print("\n--- Test 9: Hindi and Hinglish feedback ---")
sess9a = f"verify_hindi_{uuid.uuid4().hex[:8]}"
res9a = send_query({
    "query": "आपका उत्तर गलत है",
    "session_id": sess9a,
    "sequential_fallback": True
})
t9a_pass = (
    res9a.get("language") == "hi" and
    "सत्र (session)" in res9a.get("answer", "")
)

sess9b = f"verify_hinglish_{uuid.uuid4().hex[:8]}"
save_turn(
    session_id=sess9b,
    user_id=None,
    user_query="When are odd semester exams?",
    assistant_answer="The examinations are in January.",
    evidence_status="sufficient"
)
res9b = send_query({
    "query": "galat answer hai bhai, check karo calendar",
    "session_id": sess9b,
    "sequential_fallback": True
})
t9b_pass = (
    res9b.get("repair_action") == "calendar_schedule_repaired" and
    "10-12-2026" in res9b.get("answer", "")
)
t9_pass = t9a_pass and t9b_pass
results["test9_hindi_hinglish"] = {
    "passed": t9_pass,
    "hindi_passed": t9a_pass,
    "hinglish_passed": t9b_pass,
    "latency": round(res9a.get("_duration", 0) + res9b.get("_duration", 0), 3),
    "snippet": res9b.get("answer", "")[:140]
}
print(f"Test 9 Passed: {t9_pass} (Hindi: {t9a_pass}, Hinglish: {t9b_pass})")

# TEST 10: Cross-user session isolation
print("\n--- Test 10: Cross-user session isolation ---")
u_tag = uuid.uuid4().hex[:6]
user_a = f"user_alpha_{u_tag}"
user_b = f"user_beta_{u_tag}"
sess_a = f"sess_alpha_{u_tag}"
sess_b = f"sess_beta_{u_tag}"

save_turn(
    session_id=sess_a,
    user_id=user_a,
    user_query="What is the confidential hostel fine amount for Room 402?",
    assistant_answer="Confidential hostel fine amount is 5000 INR.",
    evidence_status="sufficient"
)

# User B in a different session sends disagreement
res10_b = send_query({
    "query": "your answer is wrong",
    "user_id": user_b,
    "session_id": sess_b,
    "sequential_fallback": True
})

# User B must NOT receive User A's confidential answer
t10_pass = (
    res10_b.get("repair_action") == "no_prior_context" and
    "Room 402" not in res10_b.get("answer", "") and
    "5000 INR" not in res10_b.get("answer", "")
)
results["test10_cross_user_isolation"] = {
    "passed": t10_pass,
    "user_b_action": res10_b.get("repair_action"),
    "latency": round(res10_b.get("_duration", 0), 3),
    "snippet": res10_b.get("answer", "")[:140]
}
print(f"Test 10 Passed: {t10_pass} (User B isolated from User A context)")

print("\n" + "=" * 80)
print("FINAL SUMMARY OF 10 REGRESSION TESTS:")
all_passed = True
for k, v in results.items():
    passed = v["passed"]
    if not passed:
        all_passed = False
    print(f"  {k:35s}: {'PASS' if passed else 'FAIL'} (repair_action: {v.get('repair_action', v.get('user_b_action'))}, latency: {v.get('latency')}s)")

print(f"\nALL 10 TESTS PASSED: {all_passed}")

with open("docs/r2_1_regression_test_results.json", "w", encoding="utf-8") as f:
    json.dump({"all_passed": all_passed, "tests": results}, f, indent=2)
print("Saved raw test results to docs/r2_1_regression_test_results.json")
