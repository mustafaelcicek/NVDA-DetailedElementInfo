import logging
import json
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


def get_api_key():
    from .config import getConfig, getString
    cfg = getConfig()
    return getString(cfg, "aiToken", "").strip()

def setup_gemini():
    if get_api_key():
        return True
    return False

def analyze_dom_with_gemini(dom_data):
    api_key = get_api_key()
    if not api_key:
        return _("No valid Gemini API key was found. Enter one in the add-on settings.")

    try:
        import languageHandler
        response_language = languageHandler.getLanguage()
    except Exception:
        response_language = "en"
    
    model_name = "gemini-2.5-flash"
    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model_name}:generateContent?key={api_key}"
    )
    
    prompt = f"""
    Analyze the following DOM data, including JavaScript functions and CSS properties.
    Give a short, clear explanation of what the web element is, what it does, and how a
    screen reader user can interact with it. Respond in the language identified by the
    locale code "{response_language}".

    DOM data:
    {dom_data}
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result_str = response.read().decode('utf-8')
            result_json = json.loads(result_str)
            
            text = result_json['candidates'][0]['content']['parts'][0]['text']
            return text
            
    except urllib.error.HTTPError as e:
        logger.error(f"Gemini API request failed: {e.code} - {e.reason}")
        error_body = e.read().decode('utf-8')
        return _("AI analysis failed with HTTP {code}: {body}").format(
            code=e.code,
            body=error_body,
        )
    except Exception as e:
        logger.error(f"Gemini API request failed: {e}")
        return _("AI analysis failed unexpectedly: {error}").format(error=str(e))
