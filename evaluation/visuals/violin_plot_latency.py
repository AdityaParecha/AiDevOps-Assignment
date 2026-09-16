import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

raw = pd.read_csv('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/results_final.csv')
if 'latency_ms' not in raw.columns:
    raw = pd.read_csv('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/results.csv')

fig, ax = plt.subplots(figsize=(12, 7))
parts = ax.violinplot([raw[raw['model'] == m]['latency_ms'].dropna() for m in raw['model'].unique()], showmeans=True)
ax.set_xticks(range(1, len(raw['model'].unique()) + 1))
ax.set_xticklabels(raw['model'].unique(), rotation=45, ha='right')
ax.set_title('Violin Plot: Latency Distribution by Model')
ax.set_xlabel('Model')
ax.set_ylabel('Latency (ms)')
fig.tight_layout()
fig.savefig('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/visuals/violin_plot_latency.png', dpi=200)
plt.close(fig)
print('Saved: violin_plot_latency.png')
