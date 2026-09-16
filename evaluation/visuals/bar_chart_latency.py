import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


df = pd.read_csv('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/model_summary.csv')
df = df.sort_values('avg_latency_ms').reset_index(drop=True)

fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(df['model'], df['avg_latency_ms'], color='steelblue')
ax.set_title('Average Latency by Model')
ax.set_xlabel('Model')
ax.set_ylabel('Latency (ms)')
ax.tick_params(axis='x', rotation=45)
for i, v in enumerate(df['avg_latency_ms']):
    ax.text(i, v + 500, f'{v:.2f}', ha='center', va='bottom', fontsize=8)
fig.tight_layout()
fig.savefig('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/visuals/bar_chart_latency.png', dpi=200)
plt.close(fig)
print('Saved: bar_chart_latency.png')
