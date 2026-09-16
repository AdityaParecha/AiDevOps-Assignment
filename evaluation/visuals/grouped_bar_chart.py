import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


df = pd.read_csv('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/model_summary.csv')
models = df['model']
x = np.arange(len(models))
width = 0.22

fig, ax = plt.subplots(figsize=(14, 8))
ax.bar(x - width, df['avg_latency_ms'], width, label='Latency')
ax.bar(x, df['avg_generation_time_ms'], width, label='Generation Time')
ax.bar(x + width, df['avg_output_tokens'], width, label='Output Tokens')

ax.set_xticks(x)
ax.set_xticklabels(models, rotation=45, ha='right')
ax.set_title('Grouped Bar Chart: Key Metrics by Model')
ax.set_ylabel('Value')
ax.legend()
fig.tight_layout()
fig.savefig('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/visuals/grouped_bar_chart.png', dpi=200)
plt.close(fig)
print('Saved: grouped_bar_chart.png')
