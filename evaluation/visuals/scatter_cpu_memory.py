import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


df = pd.read_csv('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/model_summary.csv')
fig, ax = plt.subplots(figsize=(10, 7))
ax.scatter(df['avg_cpu_peak_pct'], df['avg_memory_peak_pct'], s=120, c='royalblue', edgecolors='black')
for _, row in df.iterrows():
    ax.text(row['avg_cpu_peak_pct'] + 0.5, row['avg_memory_peak_pct'] + 0.5, row['model'], fontsize=8)
ax.set_title('Scatter Plot: CPU vs Memory Usage')
ax.set_xlabel('Avg CPU Peak (%)')
ax.set_ylabel('Avg Memory Peak (%)')
fig.tight_layout()
fig.savefig('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/visuals/scatter_cpu_memory.png', dpi=200)
plt.close(fig)
print('Saved: scatter_cpu_memory.png')
