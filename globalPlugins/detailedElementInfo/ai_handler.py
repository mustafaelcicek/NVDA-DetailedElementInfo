#Şimdilik bu dosya böyle kalsın, hala net veriyi almak birincil önceliğimiz.
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
        return "Hata: Geçerli bir Gemini API anahtarı bulunamadı. Lütfen ayarlardan giriniz."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    Aşağıdaki DOM verisini (JS fonksiyonları, CSS yapıları vb. dahil) inceleyerek, 
    ekran okuyucu kullanan bir görme engelli kullanıcı için bu web elementinin tam olarak 
    ne olduğunu, işlevini ve nasıl kullanılabileceğini açıklayıcı ve kısa bir özetle anlat.
    
    DOM Verisi:
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
        logger.error(f"Gemini API çağrısı sırasında HTTP Hatası: {e.code} - {e.reason}")
        error_body = e.read().decode('utf-8')
        return f"Yapay zeka analizi sırasında HTTP {e.code} hatası oluştu: {error_body}"
    except Exception as e:
        logger.error(f"Gemini API çağrısı sırasında hata oluştu: {e}")
        return f"Yapay zeka analizi sırasında beklenmeyen bir hata oluştu: {str(e)}"
