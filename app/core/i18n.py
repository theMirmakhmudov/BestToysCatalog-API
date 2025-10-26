from fastapi import Request

def get_lang(request: Request) -> str:
    lang = request.query_params.get("lang", "").lower()
    if lang not in {"uz", "ru"}:
        lang = "uz"
    return lang
