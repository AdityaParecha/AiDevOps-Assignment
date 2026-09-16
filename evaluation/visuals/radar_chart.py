import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


df = pd.read_csv('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/model_summary.csv')

metrics = ['avg_latency_ms', 'avg_retrieval_recall', 'avg_output_tokens', 'avg_cpu_peak_pct', 'avg_memory_peak_pct']
labels = ['Latency', 'Recall', 'Tokens', 'CPU', 'Memory']

# Normalize values to 0-1 scale for radar plot
normalized = []
for metric in metrics:
    max_val = df[metric].max()
    normalized.append((df[metric] / max_val).to_dict())

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
angles += angles[:1]

for _, row in df.iterrows():
    vals = [row['avg_latency_ms'], row['avg_retrieval_recall'], row['avg_output_tokens'], row['avg_cpu_peak_pct'], row['avg_memory_peak_pct']]
    max_vals = [df['avg_latency_ms'].max(), df['avg_retrieval_recall'].max(), df['avg_output_tokens'].max(), df['avg_cpu_peak_pct'].max(), df['avg_memory_peak_pct'].max()]
    vals = [v / m for v, m in zip(vals, max_vals)]
    vals += vals[:1]
    ax.plot(angles, vals, linewidth=1.5, label=row['model'])
    ax.fill(angles, vals, alpha=0.08)

ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels)
ax.set_ylim(0, 1)
ax.set_title('Radar Chart: Model Comparison')
ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1))
fig.tight_layout()
fig.savefig('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/visuals/radar_chart.png', dpi=200)
plt.close(fig)
print('Saved: radar_chart.png')
