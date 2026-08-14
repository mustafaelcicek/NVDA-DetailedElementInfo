# Detaylı Öğe Bilgisi

Web sayfalarındaki HTML öğeleri hakkında detaylı erişilebilirlik bilgileri sunan güçlü bir NVDA eklentisidir.

## Genel Bakış

Detaylı Öğe Bilgisi, NVDA için HTML öğelerini incelemenize ve bunların erişilebilirlik niteliklerini, ARIA rollerini ve anlamsal bilgilerini görüntülemenize olanak tanıyan bir yardımcı eklentidir. Bu, özellikle web geliştiricileri, erişilebilirlik denetçileri ve ekran okuyucularının web içeriğini nasıl algıladığını anlamak isteyen NVDA kullanıcıları için yararlıdır.

## Özellikler

- **ARIA Rollerini Görüntüleme**: Herhangi bir HTML öğesinin hesaplanan ARIA rolünü görmek
- **Erişilebilir Adları Gösterme**: Erişilebilir adı ve kaynağını görüntüleme (aria-label, alt metin, içerik vb.)
- **Anlamsal Uyumsuzlukları Algılama**: Açık ARIA rollerinin yerel HTML anlamsal özellikleriyle çeliştiği durumları belirleme
- **Nitelikleri İnceleme**: Tüm IA2 nitelikleri ve ARIA özelliklerini görüntüleme
- **DOM Yolunu Görüntüleme**: Odaktaki öğe için kısa ve teknik bir DOM yolu görme
- **Üst Öğe Navigasyonu**: Belge yapısını anlamak için üst öğeler arasında gezinme
- **Durum Takibi**: Öğe durumlarını (genişletilmiş, işaretli, seçili vb.) ARIA nitelikleri olarak görüntüleme
- **Kaynak Algılaması**: Erişilebilir adların nereden geldiğini anlama (aria-label, içerik, alt, başlık vb.)

## Klavye Kısayolları

| Kısayol | İşlem |
|---------|-------|
| NVDA+Shift+F1 | Odaktaki öğenin detaylarını göster |

> Not: Bu kısayolu NVDA menüsünden **Tercihler > Girdi Hareketleri** bölümünden değiştirebilirsiniz.

## Nasıl Kullanılır

1. Web sayfasındaki herhangi bir HTML öğesine Tab tuşu veya ok tuşlarını kullanarak gidin
2. Odaktaki öğenin detaylarını görüntülemek için NVDA+Shift+F1 tuşuna basın
3. Aşağıdakileri gösteren gezinebilir bir mesaj penceresi açılacaktır:
   - Öğe etiket adı ve nitelik sayısı
   - Erişilebilir ad ve kaynağı
   - Hesaplanan ARIA rolü
   - Yerel vs açık rol kaynağı
   - Anlamsal uyumsuzluklar
   - Tüm ham IA2 nitelikleri
   - Odaktaki öğenin DOM yolu
   - DOM ağacındaki üst öğeler


## Görüntülenen Bilgiler

### Erişilebilir Ad
Ekran okuyucularının öğe için duyurduğu ad.

### Ad Kaynağı
Erişilebilir adın nereden geldiği:
- **aria-label**: Açık ARIA etiketi
- **aria-labelledby**: Başka bir öğeye başvuru
- **contents**: Öğenin metin içeriği
- **alt**: Alt metin (görüntüler için)
- **value**: Öğe değer niteliği
- **title**: Başlık niteliği
- **placeholder**: Yer tutucu metni

### Hesaplanan Rol
Aşağıdakilerden belirlenen ARIA rolü:
1. Açık XML-roles (role niteliği)
2. HTML yerel anlamsal özellikleri
3. NVDA kontrol tipi eşleştirmesi
4. Bilinmiyor (varsayılan)

### Anlamsal Kaynak
Rolün nereden geldiğini gösterir:
- **native HTML**: HTML'nin örtülü anlamsal özellikleri (örn: <button> → button rolü)
- **explicit role**: role niteliği ile geçersiz kılma
- **redundant explicit role**: role niteliği yerel anlamsal özellikleri eşleştir
- **unknown**: Belirlenemiyor

### Yerel Anlamsal Uyumsuzluk
Açık bir ARIA rolünün öğenin yerel HTML anlamsal özellikleriyle çelişip çelişmediğini gösterir.

### DOM Yolu
Öğenin sayfa yapısındaki konumunu hızlıca anlamanızı sağlayan kısa teknik yol (örnek: `main > form#login > input[name="email"]`).

## Teknik Ayrıntılar

Bu eklenti şunları kullanır:
- IAccessible2 (IA2) arayüzleri erişilebilirlik nitelikleri için
- NVDA'nın nesne modeli ve kontrol türleri
- WAI-ARIA 1.2 spesifikasyonları
- Windows MSAA rolleri

## Desteklenen NVDA Sürümleri

- Minimum: NVDA 2023.1
- Son test edilen: NVDA 2026.1

## Yazar

Mustafa Elçiçek <mustafaelcicek5656@gmail.com>

## Lisans

GPL-2.0

## Katkı Sağlama

Katkılar hoş karşılanır! Lütfen hataları bildirin ve iyileştirmeler önerin.

## Katkı Sağlayanlar

- **Değerli abim Uğur Gürbüz'e** — Kıymetli destekleri ve yapıcı fikirleri için teşekkür ederim.
- **Google Gemini ve GitHub Copilot'a** — Bir NVDA eklentisi geliştirecek düzeyde kodlama bilgim olmasa da, fikirden çalışır hale gelene kadar tüm süreçte bana yol gösteren, kod yazımından hata çözümüne kadar her aşamada destek olan yapay zekâ asistanları Google Gemini ve GitHub Copilot’a teşekkür ederim.

## Değişiklik Günlüğü

### Sürüm 1.0.1 (NVDA 2026.1 Uyumluluğu)
- NVDA 2026.1 için uyumluluk bilgileri güncellendi

### Sürüm 1.0.0 (İlk Sürüm)
- Detaylı Öğe Bilgisinin ilk sürümü
- ARIA rollerini ve niteliklerini görüntüleme
- Erişilebilir adları ve kaynaklarını gösterme
- Anlamsal uyumsuzlukları algılama
- Üst öğe navigasyonu

