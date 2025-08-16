def _to_doc(model):
    """Convert a pydantic model (or list / nested models) into a plain dict."""
    return model.model_dump(mode="json") if hasattr(model, "model_dump") else model