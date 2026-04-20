import json


def get_swagger_ui_html(
    *,
    openapi_url: str,
    title: str,
    swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
    swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    swagger_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
    swagger_ui_parameters: dict = None,
) -> str:
    full_swagger_ui_parameters = {
        "dom_id": "#swagger-ui",
        "layout": "BaseLayout",
        "deepLinking": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "presets": [
            "SwaggerUIBundle.presets.apis",
            "SwaggerUIBundle.SwaggerUIStandalonePreset"
        ],
    }
    if swagger_ui_parameters:
        full_swagger_ui_parameters.update(swagger_ui_parameters)
    
    # We need to handle presets separately because they are JS objects, not strings
    # but for simplicity we can just dump the ones that are strings and then 
    # replace them in the JS if needed, or just hardcode the presets if they are standard.
    
    # Actually, the most robust way is to build the JS object carefully.
    
    config = {
        "url": openapi_url,
        "dom_id": "#swagger-ui",
        "deepLinking": True,
        "layout": "BaseLayout",
    }
    if swagger_ui_parameters:
        config.update(swagger_ui_parameters)
        
    config_json = json.dumps(config)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link type="text/css" rel="stylesheet" href="{swagger_css_url}">
    <link rel="shortcut icon" href="{swagger_favicon_url}">
    <title>{title}</title>
    <style>
    /* Premium Dark Theme for Swagger UI */
    body {{
        background-color: #0d1117;
        color: #c9d1d9;
    }}
    .swagger-ui .topbar {{
        background-color: #161b22;
        border-bottom: 1px solid #30363d;
    }}
    .swagger-ui .info .title, .swagger-ui .opblock-tag, .swagger-ui .opblock .opblock-summary-operation-id {{
        color: #f0f6fc;
    }}
    .swagger-ui .scheme-container {{
        background-color: #0d1117;
        box-shadow: none;
        border-bottom: 1px solid #30363d;
    }}
    .swagger-ui select {{
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
    }}
    .swagger-ui .opblock {{
        background-color: #161b22;
        border-color: #30363d;
    }}
    .swagger-ui .opblock.opblock-get {{
        background-color: rgba(46, 160, 67, 0.1);
        border-color: #2ea043;
    }}
    .swagger-ui .opblock.opblock-post {{
        background-color: rgba(31, 111, 235, 0.1);
        border-color: #1f6feb;
    }}
    .swagger-ui .opblock.opblock-put {{
        background-color: rgba(187, 128, 9, 0.1);
        border-color: #bb8009;
    }}
    .swagger-ui .opblock.opblock-delete {{
        background-color: rgba(248, 81, 73, 0.1);
        border-color: #f85149;
    }}
    .swagger-ui .opblock .opblock-summary-path {{
        color: #f0f6fc;
    }}
    .swagger-ui .opblock .opblock-summary-description {{
        color: #8b949e;
    }}
    .swagger-ui .btn.execute {{
        background-color: #238636;
        border-color: rgba(240, 246, 252, 0.1);
    }}
    .swagger-ui .btn.execute:hover {{
        background-color: #2ea043;
    }}
    .swagger-ui .response-col_status, .swagger-ui .response-col_description {{
        color: #c9d1d9;
    }}
    .swagger-ui table thead tr td, .swagger-ui table thead tr th {{
        color: #f0f6fc;
        border-bottom: 1px solid #30363d;
    }}
    </style>
    </head>
    <body>
    <div id="swagger-ui">
    </div>
    <script src="{swagger_js_url}"></script>
    <script>
    const ui = SwaggerUIBundle({{
        ...{config_json},
        presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
    }})
    </script>
    </body>
    </html>
    """

def get_redoc_html(
    *,
    openapi_url: str,
    title: str,
    redoc_js_url: str = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    redoc_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>{title}</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <link rel="shortcut icon" href="{redoc_favicon_url}">
    <style>body {{ margin: 0; padding: 0; }}</style>
    </head>
    <body>
    <redoc spec-url="{openapi_url}"></redoc>
    <script src="{redoc_js_url}"> </script>
    </body>
    </html>
    """
