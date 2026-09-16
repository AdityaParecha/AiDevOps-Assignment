import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Use raw per-row results for distribution; fallback to summary if needed
raw = pd.read_csv('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/results_final.csv')
if 'latency_ms' not in raw.columns:
    raw = pd.read_csv('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/results.csv')

fig, ax = plt.subplots(figsize=(12, 7))
raw.boxplot(column='latency_ms', by='model', ax=ax, grid=False)
ax.set_title('Box Plot: Latency Distribution by Model')
ax.set_xlabel('Model')
ax.set_ylabel('Latency (ms)')
plt.suptitle('')
fig.tight_layout()
fig.savefig('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/visuals/box_plot_latency.png', dpi=200)
plt.close(fig)
print('Saved: box_plot_latency.png')
