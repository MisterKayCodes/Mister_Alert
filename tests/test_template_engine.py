import pytest
from app.utils.template_engine import DynamicTemplateEngine

def test_template_rendering_success():
    content = "Hello {{name}}, welcome to {{bot}}!"
    context = {"name": "Kaycris", "bot": "Mister Alert"}
    expected = "Hello Kaycris, welcome to Mister Alert!"
    
    result = DynamicTemplateEngine.render(content, context)
    assert result == expected

def test_template_rendering_missing_variable():
    content = "Hello {{name}}, how is {{missing}}?"
    context = {"name": "Kaycris"}
    # Missing variable should remain as is
    expected = "Hello Kaycris, how is {{missing}}?"
    
    result = DynamicTemplateEngine.render(content, context)
    assert result == expected

def test_template_rendering_empty_context():
    content = "Stay sharp with {{handle}}."
    context = {}
    expected = "Stay sharp with {{handle}}."
    
    result = DynamicTemplateEngine.render(content, context)
    assert result == expected
