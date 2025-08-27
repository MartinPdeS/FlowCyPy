import svgwrite

# Define SVG canvas dimensions
width = 1200
height = 400
dwg = svgwrite.Drawing("flowcy_py_gantt.svg", size=(width, height))

# Define margins and chart area
margin_left = 150
margin_top = 50
chart_width = 1000
chart_height = 300

# Define project tasks: (Task Name, Start Month, Duration in Months)
tasks = [
    ("Literature Review & Requirements", 0, 2),
    ("Simulation Platform Design", 2, 2),
    ("Module Implementation", 4, 4),
    ("Synthetic Data Generation", 8, 1),
    ("AI/ML Model Training & Benchmarking", 9, 1),
    ("Validation and Testing", 10, 1),
    ("Optimization and Integration", 11, 1),
    ("Documentation & Dissemination", 12, 1),
]

# Total timeline in months (0 to 13 for a 13-month span)
total_time = 13
scale_x = chart_width / total_time
task_height = 30
task_gap = 15

# Draw timeline axis with month markers
for month in range(total_time + 1):
    x = margin_left + month * scale_x
    # Vertical grid line
    dwg.add(
        dwg.line(
            start=(x, margin_top - 10),
            end=(x, margin_top + chart_height),
            stroke="lightgray",
            stroke_width=1,
        )
    )
    # Month label (displayed as Month 1, Month 2, etc.)
    dwg.add(
        dwg.text(
            f"Month {month+1}",
            insert=(x, margin_top - 15),
            font_size="12px",
            fill="black",
            text_anchor="middle",
        )
    )

# Draw tasks as horizontal bars
for i, (name, start, duration) in enumerate(tasks):
    y = margin_top + i * (task_height + task_gap)
    x = margin_left + start * scale_x
    task_width = duration * scale_x
    # Draw the task bar
    dwg.add(
        dwg.rect(
            insert=(x, y),
            size=(task_width, task_height),
            fill="lightblue",
            stroke="black",
            stroke_width=1,
        )
    )
    # Center the task name inside the bar
    dwg.add(
        dwg.text(
            name,
            insert=(x + task_width / 2, y + task_height / 2 + 5),
            font_size="14px",
            fill="black",
            text_anchor="middle",
        )
    )

# Draw the outer border for the chart area
dwg.add(
    dwg.rect(
        insert=(margin_left, margin_top),
        size=(chart_width, chart_height),
        fill="none",
        stroke="black",
        stroke_width=1,
    )
)

# Save the SVG file
dwg.save()
