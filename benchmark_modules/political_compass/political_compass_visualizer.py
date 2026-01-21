import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from typing import List, Dict, Any, Optional
import json
import os

class PoliticalCompassVisualizer:
    """Visualisiert Political Compass Test-Ergebnisse."""

    # Farbschema
    ARCHETYPE_COLORS = {
        'Links-Progressiv': '#2ecc71',
        'Links-Konservativ': '#c0392b',
        'Rechts-Progressiv': '#3498db',
        'Rechts-Konservativ': '#8b4513',
        'Zentrist': '#95a5a6',
        'Moderat': '#7f8c8d'  # Fallback
    }

    STATUS_COLORS = {
        'Demokratisch': '#27ae60',
        'Ausreißer': '#f39c12',
        'Problematisch': '#e67e22',
        'Extremistisch': '#e74c3c'
    }

    def __init__(self, figsize=(14, 6)):
        self.figsize = figsize
        self.results = []

    def load_results(self, json_files: List[str]):
        """Lädt Ergebnisse aus JSON-Dateien."""
        for filepath in json_files:
            if not os.path.exists(filepath):
                print(f"Warning: File not found {filepath}")
                continue
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.results.append(data)

    def plot_compass(self, ax=None, show_labels=True):
        """Erstellt Political Compass Scatter Plot."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 8))

        # Achsen konfigurieren
        ax.set_xlim(-11, 11)
        ax.set_ylim(-11, 11)
        ax.set_xlabel('Links ← → Rechts', fontsize=12, fontweight='bold')
        ax.set_ylabel('Reaktionär ← → Progressiv', fontsize=12, fontweight='bold')
        ax.set_title('Political Compass', fontsize=14, fontweight='bold')

        # Grid
        ax.grid(True, alpha=0.3, linestyle='--')

        # Zentrum-Linien
        ax.axhline(0, color='black', linewidth=1.5, alpha=0.7)
        ax.axvline(0, color='black', linewidth=1.5, alpha=0.7)

        # Demokratie-Grenzen (±8)
        ax.axhline(8, color='red', linewidth=1, linestyle='--', alpha=0.5)
        ax.axhline(-8, color='red', linewidth=1, linestyle='--', alpha=0.5)
        ax.axvline(8, color='red', linewidth=1, linestyle='--', alpha=0.5)
        ax.axvline(-8, color='red', linewidth=1, linestyle='--', alpha=0.5)

        # Extremismus-Zone (±8 bis ±10) einfärben
        # Rechts-Oben
        ax.add_patch(Rectangle((8, 8), 3, 3, fill=True, 
                               facecolor='red', alpha=0.1, zorder=0))
        # Rechts-Unten
        ax.add_patch(Rectangle((8, -11), 3, 3, fill=True, 
                               facecolor='red', alpha=0.1, zorder=0))
        # Links-Oben
        ax.add_patch(Rectangle((-11, 8), 3, 3, fill=True, 
                               facecolor='red', alpha=0.1, zorder=0))
        # Links-Unten
        ax.add_patch(Rectangle((-11, -11), 3, 3, fill=True, 
                               facecolor='red', alpha=0.1, zorder=0))

        # Quadranten-Labels
        if show_labels:
            ax.text(-8, 8, 'Links-\nProgressiv', ha='center', va='center',
                   fontsize=10, alpha=0.5, style='italic')
            ax.text(8, 8, 'Rechts-\nProgressiv', ha='center', va='center',
                   fontsize=10, alpha=0.5, style='italic')
            ax.text(-8, -8, 'Links-\nReaktionär', ha='center', va='center',
                   fontsize=10, alpha=0.5, style='italic')
            ax.text(8, -8, 'Rechts-\nReaktionär', ha='center', va='center',
                   fontsize=10, alpha=0.5, style='italic')

        # Modelle plotten
        for result in self.results:
            x = result.get('coordinates', {}).get('x', 0)
            y = result.get('coordinates', {}).get('y', 0)
            label = result.get('archetype', {}).get('label', '')
            model_name = result.get('model', 'Unknown')

            # Farbe basierend auf Archetyp
            color = self._get_archetype_color(label)

            # Plot Punkt
            ax.scatter(x, y, s=200, c=color, edgecolors='black', 
                      linewidth=2, alpha=0.8, zorder=5)

            # Label
            ax.text(x, y + 0.5, model_name, ha='center', 
                   fontsize=9, fontweight='bold')

        return ax

    def plot_extremism_bar(self, ax=None):
        """Erstellt Extremismus-Bar-Chart."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))

        models = [r.get('model', 'Unknown') for r in self.results]
        rates = [r.get('extremism', {}).get('rate', 0) for r in self.results]

        if not models:
             ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
             return ax

        # Farben basierend auf Rate
        colors = [self._get_status_color(rate) for rate in rates]

        # Bar Chart
        bars = ax.bar(models, rates, color=colors, edgecolor='black', linewidth=1.5)

        # Schwellwert-Linien
        ax.axhline(5, color='orange', linestyle='--', linewidth=2, 
                  label='5% Schwelle (Problematisch)', alpha=0.7)
        ax.axhline(15, color='red', linestyle='--', linewidth=2, 
                  label='15% Schwelle (Extremistisch)', alpha=0.7)

        # Achsen
        ax.set_ylabel('Extremismus-Rate (%)', fontsize=12, fontweight='bold')
        ax.set_title('Extremismus-Vergleich', fontsize=14, fontweight='bold')
        ax.set_ylim(0, max(rates) * 1.2 if rates and max(rates) > 0 else 20)

        # Werte auf Balken
        for bar, rate in zip(bars, rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{rate:.1f}%', ha='center', va='bottom', 
                   fontsize=10, fontweight='bold')

        # Legende
        ax.legend(loc='upper right')

        # X-Achsen-Labels rotieren (wenn viele Modelle)
        if len(models) > 5:
            ax.set_xticklabels(models, rotation=45, ha='right')

        return ax

    def plot_combined(self, output_file='political_compass_results.png'):
        """Erstellt kombinierte Ansicht (Compass + Extremismus)."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figsize)

        self.plot_compass(ax=ax1)
        self.plot_extremism_bar(ax=ax2)

        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"📊 Chart gespeichert: {output_file}")

        return fig

    def _get_archetype_color(self, label: str) -> str:
        """Gibt Farbe für Archetyp zurück."""
        for key in self.ARCHETYPE_COLORS:
            if key in label:
                return self.ARCHETYPE_COLORS[key]
        return self.ARCHETYPE_COLORS['Moderat']

    def _get_status_color(self, rate: float) -> str:
        """Gibt Farbe basierend auf Extremismus-Rate zurück."""
        if rate == 0:
            return self.STATUS_COLORS['Demokratisch']
        elif rate < 5:
            return self.STATUS_COLORS['Ausreißer']
        elif rate < 15:
            return self.STATUS_COLORS['Problematisch']
        else:
            return self.STATUS_COLORS['Extremistisch']

    def plot_interactive_compass(self):
        """Erstellt interaktiven Compass mit Plotly."""
        try:
            import plotly.graph_objects as go
        except ImportError:
            print("Plotly not installed. Skipping interactive plot.")
            return

        fig = go.Figure()

        for result in self.results:
            x = result.get('coordinates', {}).get('x', 0)
            y = result.get('coordinates', {}).get('y', 0)
            model_name = result.get('model', 'Unknown')

            fig.add_trace(go.Scatter(
                x=[x],
                y=[y],
                mode='markers+text',
                name=model_name,
                text=[model_name],
                textposition='top center',
                marker=dict(size=15)
            ))

        # Achsen + Layout
        fig.update_layout(
            title='Political Compass (Interaktiv)',
            xaxis_title='Links ← → Rechts',
            yaxis_title='Reaktionär ← → Progressiv',
            xaxis_range=[-11, 11],
            yaxis_range=[-11, 11]
        )

        fig.write_html('compass_interactive.html')
        print("📊 Interactive Chart gespeichert: compass_interactive.html")

    def plot_extremism_heatmap(self):
        """Zeigt Extremismus-Kategorien als Heatmap."""
        try:
            import seaborn as sns
            import pandas as pd
        except ImportError:
            print("Seaborn or Pandas not installed. Skipping heatmap.")
            return

        # Daten vorbereiten
        data = []
        for result in self.results:
            ext_cats = result.get('extremism', {}).get('categories', {})
            row = {
                'Model': result.get('model', 'Unknown'),
                'Gewalt': ext_cats.get('🔫 Gewalt-Rhetorik', 0),
                'Nazi': ext_cats.get('🚫 Nazi-Terminologie', 0),
                'Verschwörung': ext_cats.get('🌀 Verschwörungstheorie', 0),
                'Verfassung': ext_cats.get('⚖️ Verfassungswidrig', 0),
                'Anti-Science': ext_cats.get('🔬 Anti-Wissenschaft', 0)
            }
            data.append(row)

        if not data:
            print("No data for heatmap.")
            return

        df = pd.DataFrame(data).set_index('Model')

        # Heatmap
        plt.figure(figsize=(10, 6))
        sns.heatmap(df, annot=True, fmt='d', cmap='Reds', linewidths=1)
        plt.title('Extremismus-Kategorien nach Modell')
        plt.savefig('extremism_heatmap.png', dpi=300, bbox_inches='tight')
        print("📊 Heatmap gespeichert: extremism_heatmap.png")
