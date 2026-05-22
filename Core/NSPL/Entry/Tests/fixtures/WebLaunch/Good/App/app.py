from __future__ import annotations


def create_app(context):
    async def app(scope, receive, send):
        return None

    app.web_context = context
    return app
