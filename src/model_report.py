"""Figures from the saved model results (`reports/model_results/*.csv`, written by `src/run_experiments.py`)."""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

RESULTS = Path(__file__).resolve().parent.parent / 'reports' / 'model_results'
FIGURES = Path(__file__).resolve().parent.parent / 'reports' / 'figures'
STYLE = {'gradient boosting': ('#1b6ca8', '-', 'o'), 'logistic regression': ('#5ba3d9', '--', 's'),
         'rule: no auto-renew': ('#d98c1b', '-', '^'), 'rule: few transactions': ('#999999', ':', 'v')}
PANELS = [('2017-01', 'Test: January 2017 (rebuilt labels)'), ('2017-02', 'Test: February 2017 (rebuilt labels)'),
          ('2017-03', 'External: March 2017 (official labels)')]


def recall_at_capacity(results=None, path=None):
    """Share of the churners reached (recall) by contacting the top 5%, 10%, 20% of users, by model."""
    results = results if results is not None else pd.read_csv(RESULTS / 'results.csv')
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    for ax, (month, title) in zip(axes, PANELS):
        data = results[results.month == month]
        for model, (color, line, marker) in STYLE.items():
            part = data[data.model == model].sort_values('capacity')
            ax.plot(100 * part.capacity, 100 * part.recall, color=color, linestyle=line, marker=marker, label=model)
        ax.plot([5, 10, 20], [5, 10, 20], color='black', linestyle='--', linewidth=1, label='random list')
        ax.set_title(title, fontsize=10)
        ax.set_xlabel('Users contacted (% of the month\'s expiring users)')
        ax.set_xticks([5, 10, 20])
        ax.grid(alpha=0.3)
    axes[0].set_ylabel('Churners reached (%)')
    axes[0].legend(fontsize=8, loc='lower right')
    fig.tight_layout()
    path = Path(path) if path else FIGURES / 'recall_at_capacity.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


if __name__ == '__main__':
    print(recall_at_capacity())
