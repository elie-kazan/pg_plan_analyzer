import json

with open('/home/bo/Desktop/fuck/pg_plan_analyser/clean.json') as f:
	data = json.load(f)

root = data[0]               # PostgreSQL wraps it in a list
plan = root["Plan"]          # Actual root node
execution_time = root.get("Execution Time", 0)

print("\n=== QUERY SUMMARY ===")
print(f"Execution time: {execution_time:.2f} ms\n")


# -------- WALK FUNCTION --------
def walk(node, depth=0):
    indent = "  " * depth

    node_type = node.get("Node Type", "Unknown")
    actual_time = node.get("Actual Total Time", 0)
    actual_rows = node.get("Actual Rows", 0)
    plan_rows = node.get("Plan Rows", 0)

    print(f"{indent}{node_type}")
    print(f"{indent}  Time: {actual_time} ms")
    print(f"{indent}  Rows: {actual_rows}")

    # Detect estimation error
    if plan_rows and actual_rows:
        ratio = actual_rows / plan_rows
        if ratio > 5 or ratio < 0.2:
            print(f"{indent}  ⚠ Bad row estimation (ratio={ratio:.2f})")

    # Detect disk spill
    if node.get("Temp Written Blocks", 0) > 0:
        print(f"{indent}  ⚠ Disk spill detected")

    print()

    # Visit children
    for child in node.get("Plans", []):
        walk(child, depth + 1)


# -------- RUN ANALYSIS --------
print("=== PLAN TREE ===\n")
walk(plan)