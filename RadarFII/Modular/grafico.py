import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import os
from datetime import datetime

def gerar_grafico_variacao(df, pasta="relatorios"):
    os.makedirs(pasta, exist_ok=True)
    path = os.path.abspath(f"{pasta}/variacao_fiis_{datetime.now().strftime('%Y%m%d')}.png")
    
    plt.figure(figsize=(12, 6))
    cores = ['green' if x > 0 else 'red' for x in df['Variação (%)']]
    bars = plt.bar(df['FII'], df['Variação (%)'], color=cores)

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height + (0.1 if height >= 0 else -0.5),
                 f"{height:.2f}%", ha='center', va='bottom' if height >= 0 else 'top',
                 fontsize=9, fontweight='bold')

    plt.title('📈 Variação Diária dos FIIs', fontsize=16)
    plt.xlabel('FII')
    plt.ylabel('Variação (%)')
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path
