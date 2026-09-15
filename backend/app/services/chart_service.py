"""
Matplotlib Chart Generation Service
Creates publication-quality visualizations of evaluation results for the UI and Jury Presentation.
"""

import math
import logging
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from app.config import DATA_DIR, CHARTS_DIR

logger = logging.getLogger("promptdesk.charts")

# Clean Modern Theme Styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
FONT_FAMILY = 'sans-serif'
COLORS = {
    "v1": "#EF4444", # Red
    "v2": "#F59E0B", # Amber
    "v3": "#3B82F6", # Blue
    "v4": "#10B981"  # Emerald
}

def generate_radar_chart():
    """
    Generates a 4-dimensional radar chart comparing V1, V2, V3, V4 on:
    Correctness, Hallucination Safety, Escalation, and Tone.
    """
    summary_file = DATA_DIR / "evaluation_summary.csv"
    if not summary_file.exists():
        return
        
    df = pd.read_csv(summary_file)
    df = df.fillna(0)
    categories = ['Correctness', 'Safety/Non-Hallucination', 'Escalation', 'Tone']
    num_vars = len(categories)
    
    angles = [n / float(num_vars) * 2 * math.pi for n in range(num_vars)]
    angles += angles[:1] # Close the circle
    
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True), dpi=150)
    fig.patch.set_facecolor('#0F172A') # Dark slate background
    ax.set_facecolor('#1E293B')
    
    plt.xticks(angles[:-1], categories, color='#F8FAFC', size=11, fontweight='bold')
    ax.set_rlabel_position(0)
    plt.yticks([25, 50, 75, 100], ["25", "50", "75", "100"], color="#94A3B8", size=9)
    plt.ylim(0, 105)
    
    ax.grid(color='#334155', linestyle='--', linewidth=0.8)
    ax.spines['polar'].set_color('#475569')
    
    version_colors = [COLORS["v1"], COLORS["v2"], COLORS["v3"], COLORS["v4"]]
    
    for idx, row in df.iterrows():
        v_name = row['version']
        values = [
            row['avg_correctness'],
            row['avg_hallucination_score'],
            row['avg_escalation_score'],
            row['avg_tone']
        ]
        values += values[:1]
        
        color = version_colors[idx % len(version_colors)]
        ax.plot(angles, values, linewidth=2.5, linestyle='solid', label=f"{v_name} ({row['name']})", color=color)
        ax.fill(angles, values, color=color, alpha=0.15)
        
    plt.title("Prompt Quality Radar Comparison (V1 to V4)", size=14, color='#FFFFFF', weight='bold', y=1.08)
    legend = plt.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1), facecolor='#1E293B', edgecolor='#475569', labelcolor='#F8FAFC', fontsize=9)
    
    out_path = CHARTS_DIR / "radar_chart.png"
    plt.tight_layout()
    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close()
    logger.info(f"Generated radar chart at {out_path}")

def generate_metric_progression_chart():
    """
    Generates a multi-bar chart tracking the score progression of all 4 metrics across V1->V4.
    """
    summary_file = DATA_DIR / "evaluation_summary.csv"
    if not summary_file.exists():
        return
        
    df = pd.read_csv(summary_file)
    df = df.fillna(0)
    versions = df['version'].tolist()
    
    x = np.arange(len(versions))
    width = 0.2
    
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    fig.patch.set_facecolor('#0F172A')
    ax.set_facecolor('#1E293B')
    
    r1 = ax.bar(x - 1.5*width, df['avg_correctness'], width, label='Correctness', color='#38BDF8', edgecolor='#0284C7', alpha=0.9)
    r2 = ax.bar(x - 0.5*width, df['avg_hallucination_score'], width, label='Safety/Non-Hallucination', color='#34D399', edgecolor='#059669', alpha=0.9)
    r3 = ax.bar(x + 0.5*width, df['avg_escalation_score'], width, label='Escalation', color='#FBBF24', edgecolor='#D97706', alpha=0.9)
    r4 = ax.bar(x + 1.5*width, df['composite_pqi'], width, label='Composite PQI Index', color='#A855F7', edgecolor='#7E22CE', alpha=0.9)
    
    ax.set_ylabel('Score (0 - 100)', color='#F8FAFC', fontsize=11, weight='bold')
    ax.set_title('Metric Progression Across Prompt Iterations (ShopEase Benchmark)', color='#FFFFFF', fontsize=13, weight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{v}\n({df.loc[i, 'name']})" for i, v in enumerate(versions)], color='#F8FAFC', fontsize=10, weight='bold')
    ax.set_ylim(0, 115)
    
    ax.tick_params(colors='#94A3B8')
    ax.grid(axis='y', color='#334155', linestyle='--', alpha=0.7)
    
    # Value labels on top of composite PQI
    for bar in r4:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.1f}", ha='center', va='bottom', color='#A855F7', fontweight='bold', fontsize=9)
        
    legend = ax.legend(facecolor='#1E293B', edgecolor='#475569', labelcolor='#F8FAFC', fontsize=9, loc='upper left')
    
    out_path = CHARTS_DIR / "metric_progression.png"
    plt.tight_layout()
    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    logger.info(f"Generated metric progression chart at {out_path}")

def generate_hallucination_reduction_chart():
    """
    Generates a chart showing the dramatic reduction in Hallucination Rate and increase in Escalation Accuracy.
    """
    summary_file = DATA_DIR / "evaluation_summary.csv"
    if not summary_file.exists():
        return
        
    df = pd.read_csv(summary_file)
    df = df.fillna(0)
    versions = df['version'].tolist()
    
    fig, ax1 = plt.subplots(figsize=(8, 4.5), dpi=150)
    fig.patch.set_facecolor('#0F172A')
    ax1.set_facecolor('#1E293B')
    
    color_hall = '#EF4444'
    ax1.set_xlabel('Prompt Iteration', color='#F8FAFC', fontsize=11, weight='bold')
    ax1.set_ylabel('Hallucination Rate (%) [Lower is Better]', color=color_hall, fontsize=10, weight='bold')
    line1 = ax1.plot(versions, df['hallucination_rate_pct'], color=color_hall, marker='o', linewidth=3, markersize=8, label='Hallucination Rate %')
    ax1.tick_params(axis='y', labelcolor=color_hall)
    ax1.tick_params(axis='x', colors='#F8FAFC')
    ax1.set_ylim(-5, 105)
    
    for i, txt in enumerate(df['hallucination_rate_pct']):
        ax1.annotate(f"{txt}%", (versions[i], txt + 4), color=color_hall, fontweight='bold', ha='center')
        
    ax2 = ax1.twinx()
    color_esc = '#10B981'
    ax2.set_ylabel('Escalation Accuracy (%) [Higher is Better]', color=color_esc, fontsize=10, weight='bold')
    line2 = ax2.plot(versions, df['escalation_accuracy_pct'], color=color_esc, marker='s', linewidth=3, linestyle='--', markersize=8, label='Escalation Accuracy %')
    ax2.tick_params(axis='y', labelcolor=color_esc)
    ax2.set_ylim(-5, 105)
    
    for i, txt in enumerate(df['escalation_accuracy_pct']):
        ax2.annotate(f"{txt}%", (versions[i], txt - 8), color=color_esc, fontweight='bold', ha='center')
        
    plt.title('Hallucination Reduction & Escalation Precision Improvement', color='#FFFFFF', fontsize=12, weight='bold', pad=15)
    ax1.grid(color='#334155', linestyle=':', alpha=0.6)
    
    out_path = CHARTS_DIR / "hallucination_reduction.png"
    plt.tight_layout()
    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    logger.info(f"Generated hallucination reduction chart at {out_path}")

def generate_all_charts():
    """
    Generates all visualization artifacts.
    """
    generate_radar_chart()
    generate_metric_progression_chart()
    generate_hallucination_reduction_chart()
