from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "model_summary.csv"
OUTPUT_DIR = Path(__file__).resolve().parent


def load_data():
    df = pd.read_csv(CSV_PATH)
    return df.sort_values("avg_latency_ms", ascending=True).reset_index(drop=True)


def save_bar_chart(df, metric, title, ylabel, color="steelblue", filename=None):
    if filename is None:
        filename = metric + ".png"

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(df["model"], df[metric], color=color)
    ax.set_title(title)
    ax.set_xlabel("Model")
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=45)

    for bar, val in zip(bars, df[metric]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + max(df[metric].max() * 0.01, 0.5),
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / filename, dpi=200)
    plt.close(fig)


def save_dashboard(df):
    charts = [
        ("avg_latency_ms", "Average Latency (ms)", "latency_by_model.png", "steelblue"),
        ("avg_generation_time_ms", "Average Generation Time (ms)", "generation_time_by_model.png", "darkorange"),
        ("avg_output_tokens", "Average Output Tokens", "output_tokens_by_model.png", "forestgreen"),
        ("avg_total_tokens", "Average Total Tokens", "total_tokens_by_model.png", "mediumorchid"),
        ("avg_cpu_peak_pct", "Average CPU Peak (%)", "cpu_peak_by_model.png", "crimson"),
        ("avg_memory_peak_pct", "Average Memory Peak (%)", "memory_peak_by_model.png", "teal"),
        ("blank_answers", "Blank Answers", "blank_answers_by_model.png", "goldenrod"),
        ("errors", "Errors", "errors_by_model.png", "darkred"),
    ]

    for metric, title, filename, color in charts:
        save_bar_chart(df, metric, title, title, color=color, filename=filename)

    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    axes = axes.flatten()

    for ax, (metric, title, _, color) in zip(axes, charts):
        ax.bar(df["model"], df[metric], color=color)
        ax.set_title(title)
        ax.set_xlabel("Model")
        ax.set_ylabel(title.split("(")[0].strip())
        ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "model_metrics_dashboard.png", dpi=200)
    plt.close(fig)


def main():
    df = load_data()
    save_dashboard(df)

    save_bar_chart(df, "avg_latency_ms", "Average Latency by Model", "Latency (ms)", color="steelblue", filename="avg_latency_ms.png")
    save_bar_chart(df, "avg_generation_time_ms", "Average Generation Time by Model", "Generation Time (ms)", color="darkorange", filename="avg_generation_time_ms.png")
    save_bar_chart(df, "avg_output_tokens", "Average Output Tokens by Model", "Tokens", color="forestgreen", filename="avg_output_tokens.png")
    save_bar_chart(df, "avg_total_tokens", "Average Total Tokens by Model", "Tokens", color="mediumorchid", filename="avg_total_tokens.png")
    save_bar_chart(df, "avg_retrieval_recall", "Average Retrieval Recall by Model", "Recall", color="royalblue", filename="avg_retrieval_recall.png")
    save_bar_chart(df, "avg_cpu_peak_pct", "Average CPU Peak by Model", "CPU Peak (%)", color="crimson", filename="avg_cpu_peak_pct.png")
    save_bar_chart(df, "avg_memory_peak_pct", "Average Memory Peak by Model", "Memory Peak (%)", color="teal", filename="avg_memory_peak_pct.png")
    save_bar_chart(df, "blank_answers", "Blank Answers by Model", "Blank Answers", color="goldenrod", filename="blank_answers.png")
    save_bar_chart(df, "errors", "Error Count by Model", "Errors", color="darkred", filename="errors.png")

    print(f"Graphs generated in: {OUTPUT_DIR}")
    print("Created files:")
    for path in sorted(OUTPUT_DIR.glob("*.png")):
        print(f" - {path.name}")


if __name__ == "__main__":
    main()
