import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


df = pd.read_csv('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/model_summary.csv')
models = df['model']
x = np.arange(len(models))

fig, ax = plt.subplots(figsize=(14, 8))
ax.bar(x, df['avg_output_tokens'], label='Output Tokens', color='steelblue')
ax.bar(x, df['avg_total_tokens'] - df['avg_output_tokens'], bottom=df['avg_output_tokens'], label='Prompt/Other Tokens', color='orange')
ax.set_xticks(x)
ax.set_xticklabels(models, rotation=45, ha='right')
ax.set_title('Stacked Bar Chart: Token Composition by Model')
ax.set_ylabel('Tokens')
ax.legend()
fig.tight_layout()
fig.savefig('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/visuals/stacked_bar_chart.png', dpi=200)
plt.close(fig)
print('Saved: stacked_bar_chart.png')
