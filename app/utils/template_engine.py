import re
from typing import Dict, Any

class DynamicTemplateEngine:
    """
    Utility for safe placeholder replacement in marketing templates.
    """
    
    @staticmethod
    def render(content: str, context: Dict[str, Any]) -> str:
        """
        Replaces {{variable}} placeholders with values from context.
        """
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))
        
        return content
