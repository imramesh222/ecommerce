from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.utils import no_body, force_real_str

class NoDuplicateParamsAutoSchema(SwaggerAutoSchema):
    def __init__(self, view, path, method, components, request, overrides):
        super().__init__(view, path, method, components, request, overrides)
    
    def get_operation(self, operation_keys):
        operation = super().get_operation(operation_keys)
        if not operation or not operation.parameters:
            return operation
            
        # Remove duplicate parameters
        seen = set()
        unique_params = []
        for param in operation.parameters:
            # Create a unique key for each parameter (name + in)
            param_key = (param.name, param.in_)
            if param_key not in seen:
                seen.add(param_key)
                unique_params.append(param)
                
        operation.parameters = unique_params
        return operation
