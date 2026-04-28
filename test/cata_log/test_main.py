from fastapi.routing import APIRoute


def test_operation_ids(fastapi_app):
    operation_ids = [
        route.operation_id
        for route in fastapi_app.routes
        if isinstance(route, APIRoute) and route.operation_id is not None
    ]
    unique_operation_ids = set(operation_ids)

    assert len(operation_ids) == len(unique_operation_ids)


def test_openapi(fastapi_app):
    openapi_paths = fastapi_app.openapi()["paths"]
    operation_ids = [
        method_data["operationId"]
        for path_data in openapi_paths.values()
        for method_data in path_data.values()
    ]
    unique_operation_ids = set(operation_ids)

    assert len(operation_ids) == len(unique_operation_ids)
    for operation_id in operation_ids:
        assert operation_id
