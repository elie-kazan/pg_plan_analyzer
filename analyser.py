import json

with open('/home/bo/Desktop/pg/pg_plan_analyser/index_tips_big_table.json') as f:
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

    # work_mem
    if node.get("Sort Method") == "external merge":
    	sort_kb = node.get("Sort Space Used",0)
    	required_mb = sort_kb / 1024

    	print(f"{indent}  ⚠ Disk sort detected,Required approx: {required_mb:.0f} MB")

    #go through the workers and get the info
    Workers = node.get("Workers")
    if Workers:
        print(f"{indent}  Number of workers: {len(Workers):.0f} ")

    shared_hit = node.get("Shared Hit Blocks",0)
    shared_read = node.get("Shared Read Blocks",0)

    shared_hit_percentage = (shared_hit / (shared_hit + shared_read))*100

    print(f"{indent}  Shared hit percentage : {shared_hit_percentage:.2f} %")

    #check how many rows are removed by filter
    if node.get("Rows Removed by Filter",0)!= 0:
        row_removed = node.get("Rows Removed by Filter",0)
        if node.get("Actual Loops",0) != 0:
            actual_loops = node.get("Actual Loops",0)
            row_removed = row_removed * actual_loops
            row_returned_removed_ratio = (actual_rows/row_removed) * 100
            print(f"{indent}  row_returned_removed_ratio : {row_returned_removed_ratio:.5f} %")
            

    


    
        




    print()

    # Visit children
    for child in node.get("Plans", []):
        walk(child, depth + 1)


# -------- RUN ANALYSIS --------
print("=== PLAN TREE ===\n")
walk(plan)