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
- **Ad Kaynağı Güveni**: Erişilebilir adın nereden geldiği konusunda eklentinin ne kadar emin olduğunu görme (kesin, çıkarım, bilinmiyor)
- **Çoklu Rol Görünümü**: Açık ARIA rolünü, yerel HTML rolünü, NVDA rolünü ve nihai çıkarılan rolü yan yana karşılaştırma
- **MSAA Rolü ve Başlık Düzeyi**: Ham MSAA rolünü ve başlıklar için başlık düzeyini görüntüleme
- **Durumdan Türetilen Nitelikler**: NVDA durumlarından türetilen ARIA benzeri nitelikleri görme (genişletilmiş, işaretli, seçili vb.)
- **Yapılandırılabilir Alanlar**: Raporda hangi alanların görüneceğini eklenti ayarlarından seçme; Tümünü seç / Tümünü temizle düğmeleriyle
- **Gelişmiş Destek — Chrome Köprüsü (Deneysel)**: Sayfanın gerçek DOM verisine, HTML niteliklerine ve aktif özelliklerine doğrudan erişmek için eşlik eden bir Chrome uzantısına bağlanma
- **Gemini ile Yapay Zeka Analizi (Deneysel)**: Odaktaki öğenin ne olduğunu ve nasıl kullanılabileceğini sade bir dille açıklaması için Google Gemini'ye sorma

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

## Ayarlar

Eklentiyi yapılandırmak için **NVDA menüsü > Tercihler > Ayarlar > Detaylı Öğe Bilgisi** bölümünü açın:

- **Gösterilecek alanları seçme**: Raporun her alanını açıp kapatın — etiket özeti, erişilebilir ad, ad kaynağı ve güveni, DOM etiketi ve yolu, açık / yerel / NVDA / nihai roller, anlamsal kaynak ve uyumsuzluk, ham IA2 nitelikleri, NVDA durumlarından türetilen nitelikler, MSAA rolü ve üst öğeler.
- **Tümünü seç / Tümünü temizle**: Tüm alanları tek seferde açın veya kapatın.
- **Gelişmiş Desteği (AI ve Chrome Eklentisi) Etkinleştir**: Aşağıda açıklanan deneysel Chrome Köprüsü ve yapay zeka özelliklerini açar.
- **Gemini AI Token**: Yapay zeka analizinin çalışabilmesi için kendi Google Gemini API anahtarınızı girin.

## Gelişmiş Destek — Chrome Köprüsü (Deneysel)

Detaylı Öğe Bilgisi, NVDA'nın sanal belleğinin ötesine geçip sayfanın gerçek DOM'unu okumak için isteğe bağlı olarak eşlik eden bir Chrome uzantısına bağlanabilir.

- Gelişmiş Destek etkinleştirildiğinde, eklenti Chrome uzantısıyla HTTP uzun yoklama (long polling) kullanarak konuşan hafif bir yerel sunucu (`127.0.0.1:63333`) başlatır.
- Rapor daha sonra Chrome'dan alınan canlı HTML nitelikleri ve özellikleriyle bir **Aktif elementin dom öznitelikleri** bölümü içerir.
- Bu özellik, eşlik eden Chrome uzantısının kurulu olmasını gerektirir. Özellik deneyseldir ve aktif olarak geliştirilmektedir.

## Gemini ile Yapay Zeka Analizi (Deneysel)

Gelişmiş Destek etkinken ve bir Gemini API anahtarı girildiğinde, rapor bir **AI Yorumu iste** eylemi sunar.

- Toplanan DOM verisi Google Gemini'ye gönderilir ve Gemini, öğenin ne olduğunu, amacını ve bir ekran okuyucu kullanıcısının onunla nasıl etkileşime girebileceğini kısa ve sade bir dille açıklar.
- Bu, ayarlarda girilen kendi Google Gemini API anahtarınızı gerektirir. Özellik deneyseldir.

## Teknik Ayrıntılar

Bu eklenti **sıfır bağımlılıklı yerel bir mimari** kullanır:
- `pip` bağımlılık sorunlarından kaçınmak için saf Python standart kütüphaneleri (`http.server`, `urllib.request`)
- IAccessible2 (IA2) arayüzleri erişilebilirlik nitelikleri için
- NVDA'nın nesne modeli ve kontrol türleri
- WAI-ARIA 1.2 spesifikasyonları
- Windows MSAA rolleri
- HTTP uzun yoklama: eşlik eden Chrome uzantısının Manifest V3 hizmet çalışanına (service worker), içerik betiği sinyalleriyle canlı tutulan hafif bir köprü

## Desteklenen NVDA Sürümleri

- Minimum: NVDA 2023.1
- Son test edilen: NVDA 2026.1

## Yazar

Mustafa Elçiçek <mustafaelcicek5656@gmail.com>

## Lisans

GPL-2.0

## Katkı Sağlama

Katkılar hoş karşılanır! Hataları bildirmeden, iyileştirmeler önermeden veya bir çekme isteği (pull request) açmadan önce lütfen proje deposundaki Katkı Kılavuzu'nu (`CONTRIBUTING.md`) okuyun.

## Katkı Sağlayanlar

Detaylı Öğe Bilgisi; kod katkısı sağlayanların, test edenlerin ve destekçilerin yardımıyla geliştirilmektedir. Katkı sağlayanların tam listesi ve her birinin üzerinde çalıştığı konular için proje deposundaki `CONTRIBUTORS.md` dosyasına bakın.

## Değişiklik Günlüğü

### Sürüm 1.0.2
- Eklentinin NVDA'nın sanal belleğine bağlı kalmadan sayfanın gerçek DOM verisini okuyabilmesi için deneysel bir Chrome Köprüsü uzantısı eklendi.
- Google Gemini kullanılarak toplanan DOM/ARIA verilerinin deneysel yapay zeka analizi eklendi.
- Raporlar artık düz metin yerine yapılandırılmış, hiyerarşik bir HTML görünümünde gösteriliyor.
- Eklenti ayarlarına "Gelişmiş Desteği Etkinleştir" ve "Gemini API Anahtarı" seçenekleri eklendi.

### Sürüm 1.0.1 (NVDA 2026.1 Uyumluluğu)
- NVDA 2026.1 için uyumluluk bilgileri güncellendi

### Sürüm 1.0.0 (İlk Sürüm)
- Detaylı Öğe Bilgisinin ilk sürümü
- ARIA rollerini ve niteliklerini görüntüleme
- Erişilebilir adları ve kaynaklarını gösterme
- Anlamsal uyumsuzlukları algılama
- Üst öğe navigasyonu

