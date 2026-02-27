import json
import sys
from pyvis.network import Network
import re

if len(sys.argv) < 2:
    print("Usage : python3 analyse.py <json_file>")
    sys.exit(1)

filename = sys.argv[1]


with open(filename) as f:
    data = json.load(f)

root = data[0]               # PostgreSQL wraps plan in a list
plan = root["Plan"]
execution_time = root.get("Execution Time", 0)


def extract_columns(condition):
    if not condition:
        return []

    # Match simple column names before operators
    # Example: column = value
    pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*(=|>|<|>=|<=|<>|!=)'
    matches = re.findall(pattern, condition)

    return list(set([m[0] for m in matches]))


def detect_warnings(node, execution_time):
    warnings = []

    actual_rows = node.get("Actual Rows", 0)
    plan_rows = node.get("Plan Rows", 0)

    # Row estimation mismatch
    if plan_rows and actual_rows:
        ratio = actual_rows / plan_rows
        if ratio > 5 or ratio < 0.2:
            warnings.append(f"Bad row estimation (ratio={ratio:.2f})")

    # Disk spill (temp blocks)
    if node.get("Temp Written Blocks", 0) > 0:
        warnings.append("Disk spill detected")

    # External merge sort
    if node.get("Sort Method") == "external merge":
        sort_kb = node.get("Sort Space Used", 0)
        required_mb = sort_kb / 1024
        warnings.append(f"Disk sort (~{required_mb:.0f} MB work_mem needed)")

    # Hash spill
    if node.get("Hash Batches", 1) > 1:
        warnings.append("Hash spill (increase work_mem)")

    # Dangerous nested loop
    if node.get("Node Type") == "Nested Loop":
        if actual_rows > 10000:
            warnings.append("Nested Loop on large dataset")

    # Slow node relative to total query time
    actual_time = node.get("Actual Total Time", 0)
    if execution_time > 0:
        if actual_time > execution_time * 0.6:
            warnings.append("Very expensive node")

    # Index suggestion (your logic improved)
    rows_removed = node.get("Rows Removed by Filter", 0)
    actual_loops = node.get("Actual Loops", 1)
    table_name = node.get("Relation Name")
    filter_condition = node.get("Filter")
    columns = extract_columns(filter_condition)

    if rows_removed > 0 and table_name:
        rows_removed_total = rows_removed * actual_loops

        if rows_removed_total > 0:
            ratio = (actual_rows / rows_removed_total) * 100

            if ratio < 15 and (rows_removed_total + actual_rows) > 100000:
                warnings.append(
                    f"Consider index on {table_name}({', '.join(columns)})"
                )

    return warnings

# ---------------------------
# GRAPH BUILDER
# ---------------------------
def build_graph(plan, execution_time):
    net = Network(
        directed=True,
        height="900px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black"
    )

    # 🔥 IMPORTANT: Enable hierarchical layout
    net.set_options("""
    {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed",
          "levelSeparation": 150,
          "nodeSpacing": 200,
          "treeSpacing": 300
        }
      },
      "physics": {
        "enabled": false
      },
      "interaction": {
         "hover": true
      },
      "edges": {
        "arrows": {
          "to": { "enabled": true }
        }
      }
    }
    """)

    def add_nodes(node, parent=None, level=0):
        node_id = id(node)

        node_type = node.get("Node Type", "Unknown")
        actual_time = node.get("Actual Total Time", 0)
        actual_rows = node.get("Actual Rows", 0)

        warnings = detect_warnings(node, execution_time)

        # color logic
        color = "#b3e6b3"  # light green
        if execution_time > 0:
            if actual_time > execution_time * 0.3:
                color = "#ffcc80"  # orange
            if actual_time > execution_time * 0.6:
                color = "#ff6666"  # red

        if warnings:
            color = "#ff4d4d"

        tooltip = f"""
        
        {node_type}\n
        Time: {actual_time:.2f} ms\n
        Rows: {actual_rows}
        
        """

        if warnings:
            tooltip += "Warnings:" + " ".join(warnings)

        net.add_node(
            node_id,
            label=f"{node_type}\n{actual_rows} rows",
            title=tooltip,
            color=color,
            shape="box",
            level=level
        )

        if parent:
            net.add_edge(parent, node_id)

        for child in node.get("Plans", []):
            add_nodes(child, node_id, level + 1)

    add_nodes(plan)

    net.write_html("plan.html")
    print("Graph written to plan.html")

print("\nGenerating interactive graph → plan.html")
build_graph(plan, execution_time)