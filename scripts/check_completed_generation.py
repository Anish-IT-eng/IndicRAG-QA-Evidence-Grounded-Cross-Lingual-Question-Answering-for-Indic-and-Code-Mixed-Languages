import csv

completed_qids = set()
try:
    with open("backend/data/experiments/m9/answer_generation_results.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            completed_qids.add(row["query_id"])
except Exception as e:
    print("Error reading CSV:", e)

print(f"Total completed queries in CSV: {len(completed_qids)}")
print("Completed IDs sample:", sorted(list(completed_qids))[:10], "...", sorted(list(completed_qids))[-5:])
