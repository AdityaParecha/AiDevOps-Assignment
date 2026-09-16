import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


df = pd.read_csv('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/model_summary.csv')
fig, ax = plt.subplots(figsize=(10, 7))
size_scale = df['avg_total_tokens'] / 10
ax.scatter(df['avg_latency_ms'], df['avg_retrieval_recall'], s=size_scale, alpha=0.6, c='green', edgecolors='black')
for _, row in df.iterrows():
    ax.text(row['avg_latency_ms'] + 200, row['avg_retrieval_recall'] + 0.01, row['model'], fontsize=8)
ax.set_title('Bubble Chart: Latency vs Recall (Bubble = Total Tokens)')
ax.set_xlabel('Average Latency (ms)')
ax.set_ylabel('Average Retrieval Recall')
fig.tight_layout()
fig.savefig('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/visuals/bubble_chart.png', dpi=200)
plt.close(fig)
print('Saved: bubble_chart.png')
