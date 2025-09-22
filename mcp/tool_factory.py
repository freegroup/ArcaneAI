# tool_factory.py
from pydantic import create_model, Field
from typing import Dict

# Wir mappen JSON-Typen auf Python-Typen
TYPE_MAPPING = {
    "string": str,
    "integer": int,
    "boolean": bool
}

def create_tool_from_json(definition: Dict):
    """
    Erstellt dynamisch eine Pydantic-Klasse aus einer JSON-Definition
    und korrigiert das Schema für die strikte OpenAI-Kompatibilität.
    """
    field_definitions = {}
    if "parameters" in definition:
        for param in definition["parameters"]:
            param_type = TYPE_MAPPING.get(param["type"], str)
            field_definitions[param["name"]] = (param_type, Field(..., description=param["description"]))

    DynamicModel = create_model(
        definition["name"],
        **field_definitions
    )
    DynamicModel.__doc__ = definition["description"]
    
    # --- FINALE ANPASSUNG ---
    # Diese Methode wird überschrieben, um das Schema exakt in das Format zu bringen,
    # das der lokale Server (llama.cpp-basiert) erwartet.
    @classmethod
    def model_json_schema(cls):
        # 1. Generiere das Standard-Pydantic-Schema
        schema = super(DynamicModel, cls).model_json_schema()
        
        # 2. Extrahiere die Parameter-Eigenschaften und die 'required'-Liste
        parameters = schema.pop('properties', {})
        required_params = schema.pop('required', [])
        
        # 3. Baue die korrekte, finale Struktur zusammen
        final_schema = {
            'name': schema.pop('title'),
            'description': schema.pop('description'),
            # 4. Der entscheidende Teil: Wickle die Parameter in die erwartete Struktur ein
            'parameters': {
                'type': 'object',
                'properties': parameters,
                'required': required_params
            }
        }
        return final_schema

    DynamicModel.model_json_schema = model_json_schema
    # ---------------------------

    return DynamicModel