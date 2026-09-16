# Model Evaluation Visuals

This folder contains charts generated from the model evaluation summary.

## Files and what they represent

- latency_by_model.png — Average latency for each model
- latency_trend_line.png — Line view of latency values across models
- generation_time_by_model.png — Average generation time per model
- output_tokens_by_model.png — Average output token count per model
- total_tokens_by_model.png — Average total token count per model
- retrieval_recall_by_model.png — Average retrieval recall per model
- cpu_peak_by_model.png — Average CPU peak usage per model
- memory_peak_by_model.png — Average memory peak usage per model
- blank_answers_by_model.png — Blank answer count per model
- errors_by_model.png — Error count per model
- cpu_vs_memory_scatter.png — Scatter plot of CPU vs memory usage
- radar_model_profile.png — Radar chart comparing key metrics in one shape
- latency_boxplot_by_model.png — Box plot of latency distribution per model
- latency_violin_by_model.png — Violin plot of latency distribution per model
- latency_vs_recall_bubble.png — Bubble chart for latency vs recall with bubble size based on tokens
- grouped_metrics_by_model.png — Grouped bar chart comparing multiple metrics side-by-side
- token_composition_stacked_bar.png — Stacked bar chart showing token composition
- combined_model_dashboard.png — Combined dashboard of major charts
- model_metrics_dashboard.png — Multi-chart summary dashboard

## Data source
The charts are generated from:

- evaluation/model_summary.csv

## Notes
The naming is metric-specific so it is easier to identify the visualization in reports and presentations.
