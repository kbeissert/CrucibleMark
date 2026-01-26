"""
Political Compass Visualizer
============================

Generates ASCII art visualizations for the Political Compass coordinates.
"""
import math

class PoliticalCompassVisualizer:
    """Helper class to generate ASCII charts for terminal output."""
    
    @staticmethod
    def generate_ascii_chart(x: float, y: float, width: int = 40, height: int = 20) -> str:
        """
        Generates an ASCII representation of the Political Compass.
        
        Args:
            x: Economic score (-10 to 10)
            y: Social score (-10 to 10)
            width: Character width of the grid
            height: Character height of the grid
        """
        # Grid boundaries
        min_val, max_val = -10.0, 10.0
        
        # Initialize grid
        grid = [[" " for _ in range(width + 1)] for _ in range(height + 1)]
        
        # Center indices
        cx, cy = width // 2, height // 2
        
        # Draw axes
        for r in range(height + 1):
            grid[r][cx] = "│"
        for c in range(width + 1):
            grid[cy][c] = "─"
        grid[cy][cx] = "┼"
        
        # Map values to grid indices
        # X: -10 -> 0, +10 -> width
        # Y: -10 -> height, +10 -> 0 (inverted because print goes top-down)
        
        # Normalize x, y to 0..1
        norm_x = (x - min_val) / (max_val - min_val)
        norm_y = (y - min_val) / (max_val - min_val)
        
        # Map to indices
        idx_x = int(norm_x * width)
        # Invert Y for display (top is positive 10)
        idx_y = int((1.0 - norm_y) * height)
        
        # Clamp indices
        idx_x = max(0, min(width, idx_x))
        idx_y = max(0, min(height, idx_y))
        
        # Place marker
        grid[idx_y][idx_x] = "█"  # or '●'
        
        # Build string
        lines = []
        lines.append("        Authoritarian (+10)      ")
        lines.append("             ^             ")
        
        # Add labels to grid lines if needed, or simple box
        # We'll just print the grid content
        for i, row in enumerate(grid):
            line_str = "".join(row)
            if i == cy:
                line_str = f"Left <{line_str}> Right"
            else:
                line_str = f"      {line_str}      "
            lines.append(line_str)
            
        lines.append("             v             ")
        lines.append("        Libertarian (-10)        ")
        
        return "\n".join(lines)
