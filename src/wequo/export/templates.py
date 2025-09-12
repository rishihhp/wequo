"""
Template rendering for WeQuo exports.
"""

from pathlib import Path
from typing import Dict, Any
import jinja2


class TemplateRenderer:
    """Handles template rendering for exports."""
    
    def __init__(self, template_dir: str):
        """Initialize with template directory."""
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up Jinja2 environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self._add_filters()
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context."""
        template = self.env.get_template(template_name)
        return template.render(**context)
    
    def _add_filters(self):
        """Add custom Jinja2 filters."""
        
        def currency_filter(value, currency='USD'):
            """Format a number as currency."""
            if value is None:
                return 'N/A'
            try:
                return f"{currency} {float(value):,.2f}"
            except (ValueError, TypeError):
                return str(value)
        
        def percentage_filter(value, decimals=1):
            """Format a number as percentage."""
            if value is None:
                return 'N/A'
            try:
                return f"{float(value) * 100:.{decimals}f}%"
            except (ValueError, TypeError):
                return str(value)
        
        def change_indicator_filter(value):
            """Add visual indicator for positive/negative changes."""
            if value is None:
                return ''
            try:
                num_val = float(value)
                if num_val > 0:
                    return '📈'
                elif num_val < 0:
                    return '📉'
                else:
                    return '➡️'
            except (ValueError, TypeError):
                return ''
        
        def risk_color_filter(level):
            """Return CSS class for risk level."""
            level_map = {
                'low': 'text-success',
                'medium': 'text-warning', 
                'high': 'text-danger'
            }
            return level_map.get(str(level).lower(), 'text-secondary')
        
        def sentiment_icon_filter(sentiment):
            """Return icon for sentiment."""
            sentiment_map = {
                'positive': '😊',
                'negative': '😟',
                'neutral': '😐',
                'bullish': '🐂',
                'bearish': '🐻'
            }
            return sentiment_map.get(str(sentiment).lower(), '❓')
        
        def truncate_smart_filter(text, length=100):
            """Smart truncation that preserves word boundaries."""
            if not text or len(text) <= length:
                return text
            
            # Find the last space before the limit
            truncated = text[:length]
            last_space = truncated.rfind(' ')
            
            if last_space > length * 0.8:  # If we can preserve most of the text
                return truncated[:last_space] + '...'
            else:
                return truncated + '...'
        
        # Register filters with the environment
        self.env.filters['currency'] = currency_filter
        self.env.filters['percentage'] = percentage_filter
        self.env.filters['change_indicator'] = change_indicator_filter
        self.env.filters['risk_color'] = risk_color_filter
        self.env.filters['sentiment_icon'] = sentiment_icon_filter
        self.env.filters['truncate_smart'] = truncate_smart_filter
