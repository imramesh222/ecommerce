from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg import openapi
from collections import OrderedDict

class CustomOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        if not schema:
            return schema
        
        def remove_duplicate_params(parameters):
            if not parameters:
                return parameters
                
            seen = set()
            unique_params = []
            
            for param in parameters:
                if not isinstance(param, dict):
                    unique_params.append(param)
                    continue
                    
                # Create a unique key for the parameter
                param_key = (param.get('name'), param.get('in'), param.get('type', ''))
                param_str = str(param_key)
                
                if param_str not in seen:
                    seen.add(param_str)
                    unique_params.append(param)
            
            return unique_params
        
        # Process all paths and operations
        paths = schema.get('paths', {})
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
                
            for method, operation in path_item.items():
                if not isinstance(operation, dict) or 'parameters' not in operation:
                    continue
                
                operation['parameters'] = remove_duplicate_params(operation['parameters'])
        
        return schema

class CustomSwaggerAutoSchema(SwaggerAutoSchema):
    def get_operation_parameters(self, parameters, *args, **kwargs):
        parameters = super().get_operation_parameters(parameters, *args, **kwargs)
        if not parameters:
            return parameters
            
        seen = set()
        unique_params = []
        
        for param in parameters:
            param_key = (param.name, param.in_, getattr(param, 'type', ''))
            param_str = str(param_key)
            
            if param_str not in seen:
                seen.add(param_str)
                unique_params.append(param)
        
        return unique_params
