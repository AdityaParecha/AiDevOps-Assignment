import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


df = pd.read_csv('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/model_summary.csv')
models = df['model']

fig, axes = plt.subplots(2, 4, figsize=(20, 12))
axes = axes.flatten()

metrics = [
    ('avg_latency_ms', 'Average Latency (ms)', 'steelblue'),
    ('avg_generation_time_ms', 'Generation Time (ms)', 'darkorange'),
    ('avg_output_tokens', 'Output Tokens', 'forestgreen'),
    ('avg_retrieval_recall', 'Recall', 'royalblue'),
    ('avg_cpu_peak_pct', 'CPU Peak (%)', 'crimson'),
    ('avg_memory_peak_pct', 'Memory Peak (%)', 'teal'),
    ('blank_answers', 'Blank Answers', 'goldenrod'),
    ('errors', 'Errors', 'darkred'),
]

for ax, (metric, title, color) in zip(axes, metrics):
    ax.bar(models, df[metric], color=color)
    ax.set_title(title)
    ax.set_xlabel('Model')
    ax.set_ylabel(title)
    ax.tick_params(axis='x', rotation=45)

fig.tight_layout()
fig.savefig('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/visuals/combined_dashboard.png', dpi=200)
plt.close(fig)
print('Saved: combined_dashboard.png')
