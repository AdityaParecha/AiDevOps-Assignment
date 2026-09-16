import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


df = pd.read_csv('/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/model_summary.csv')
for col in ['avg_latency_ms', 'avg_generation_time_ms', 'avg_output_tokens']:
    plt.figure(figsize=(12, 6))
    plt.plot(df['model'], df[col], marker='o', linewidth=2)
    plt.title(f'Multi-line Chart: {col}')
    plt.xlabel('Model')
    plt.ylabel(col)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'/Users/jhankar/Documents/AI_DEVEOPS/AiDevOps-Assignment/evaluation/visuals/{col}_multiline.png', dpi=200)
    plt.close()
print('Saved: multiline plot files')
