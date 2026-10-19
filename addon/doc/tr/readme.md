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

## Kurulum

Eşleşen .nvda-addon paketini NVDA'nın eklenti kurulum penceresiyle yükleyip NVDA'yı yeniden başlatın. DOM bilgisi için aşağıda anlatıldığı gibi eşleşen Chrome Köprüsü'nü de yükleyin. Yerel inceleme, kontroller ve kopyalama Gemini gerektirmez.

## Klavye Kısayolları

| Kısayol | İşlem |
|---------|-------|
| NVDA+Shift+F1 | Odaktaki öğenin detaylarını göster |
| Alt+F1 | Rapor açıkken bildirilen öğeyi AI ile analiz et |
| Atanmamış | Öğenin bilgisini Markdown olarak kopyala; Girdi Hareketleri içinde atayın |

> Komut kısayollarını NVDA'nın **Tercihler > Girdi Hareketleri** bölümünde atayabilir veya değiştirebilirsiniz.

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
4. Gelişmiş Destek etkinken, AI analizi istemek için rapor açıkken Alt+F1 tuşlarına basın.


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

## Dondurulmuş raporlar ve Markdown

HTML ve Markdown aynı yakalanmış verileri ve alan seçimlerini kullanır; H1/H2 başlıkları, kaynak, kullanılabilirlik ve eksik/kesilmiş kanıt bilgisi korunur. NVDA ve DOM gözlemleri ayrı kalır. Kontroller tek öğeyle sınırlıdır; sayfa düzeyinde WCAG uygunluğu belgesi değildir.

Girdi Hareketleri içinde **Copy focused element information as Markdown** komutuna kısayol atayın. NVDA+Ctrl+Shift+F1 zaten NVDA tarafından kullanıldığı için varsayılan kısayol yoktur. Açık rapordan kopyalama o raporun dondurulmuş verilerini kullanır; sayfadan kopyalama yeni bir hedef yakalar. Pano hatası ve kullanılamayan eski anlık görüntüler açıkça bildirilir. Bu yollar Gemini'yi çağırmaz.

Dört yerel bölüm ayarı yalnızca daha önce yoksa açık başlar: **Accessibility and ARIA**, **Layout and contrast**, **Interaction and DOM**, **Diagnostic checks**. Var olan seçimler korunur; Tümünü seç / Tümünü temizle bunları da kapsar. İnsan tarafından NVDA kabul kontrolü beklemektedir.

## Ayarlar

Eklentiyi yapılandırmak için **NVDA menüsü > Tercihler > Ayarlar > Detaylı Öğe Bilgisi** bölümünü açın:

- **Gösterilecek alanları seçme**: Raporun her alanını açıp kapatın — etiket özeti, erişilebilir ad, ad kaynağı ve güveni, DOM etiketi ve yolu, açık / yerel / NVDA / nihai roller, anlamsal kaynak ve uyumsuzluk, ham IA2 nitelikleri, NVDA durumlarından türetilen nitelikler, MSAA rolü ve üst öğeler.
- **Tümünü seç / Tümünü temizle**: Tüm alanları tek seferde açın veya kapatın.
- **Gelişmiş Desteği (AI ve Chrome Eklentisi) Etkinleştir**: Aşağıda açıklanan deneysel Chrome Köprüsü ve yapay zeka özelliklerini açar.
- **Gemini API Anahtarı**: Yapay zeka analizinin çalışabilmesi için kendi Google Gemini API anahtarınızı girin.

## Gelişmiş Destek — Chrome Köprüsü (Deneysel)

Detaylı Öğe Bilgisi, NVDA'nın sanal belleğinin ötesine geçip sayfanın gerçek DOM'unu okumak için isteğe bağlı olarak eşlik eden bir Chrome uzantısına bağlanabilir.

- DOM zenginleştirmesi yalnızca yakalanan uygulama Chrome olduğunda ve Chrome penceresi odaktayken kullanılır. Firefox, diğer tarayıcılar ve bilinmeyen uygulamalar yerel kanıtı korur. Pencere odağı değişince bekleyen istek ve önceki tanıklar silinir; sonraki içerik betiği sinyaline kadar yerel sonuç gösterilebilir.
- Gelişmiş Destek etkinleştirildiğinde eklenti, `127.0.0.1:63333` adresinde yerel bir sunucu başlatır ve Chrome uzantısından öğe verilerini ister.
- Bridge verisi için önceden gözlemlenmiş bir üst düzey belge ve belgeye sabitlenmiş el sıkışma gerekir. Belge kimliği belirsizse, çerçeve desteklenmiyorsa veya süre dolarsa yerel NVDA bilgisi korunur.
- Görünür etiket, dil/yön, form/grup, tablo ve bileşik araç bağlamı sınırlı olarak kaydedilir; NVDA ve DOM kaynakları ayrı tutulur. Korunan veya koruma durumu belirsiz öğelerde DOM metni, işaretleme ve bağlam alınmaz. Düzenlenebilir metin ve doğrulama iletisi yankıları dışlanır; referans özetleri toplam sekiz hedef ve 4000 karakterle sınırlıdır.
- Yerel veri toplama kontrolleri ve bağımsız inceleme geçmiştir; insan tarafından NVDA kabul kontrolü beklemektedir. Hesaplanmış ad, görsel alternatifi, etiketteki ad, tıklama tanısı ve ihtiyatlı doğrudan metin kontrastı için yerel kontroller yazılmıştır; yapılandırılmış HTML/Markdown raporu ve rapora bağlı kopyalama yazılmış ve yerel olarak kontrol edilmiştir. Bu kontroller sayfa uygunluğu veya genel WCAG uyumu belgesi değildir.
- Yerel geliştirme durumu için [birikimli değişiklik günlüğüne](../../../changelog.md) bakın.
- Eşleşen GitHub sürümünden `detailedElementInfo-chrome-bridge.zip` dosyasını indirip ayıklayın. Ardından `chrome://extensions` sayfasını açın, **Geliştirici modu** seçeneğini etkinleştirin, **Paketlenmemiş öğe yükle** düğmesini seçin ve ayıklanan `Bridge` klasörünü gösterin.
- Uzantı, eşleştirilen öğeyi inceleyebilmek için web sayfalarında çalışır. `chrome://` sayfaları gibi tarayıcının dahili sayfaları incelenemez.
- Özellik deneyseldir ve aktif olarak geliştirilmekte ve onarılmaktadır; canlı ilişkilendirme, eşleştirme sınırları ve güvenlik filtreleri sıkılaştırılmaktadır.

## Gemini ile Yapay Zeka Analizi (Deneysel)

Gelişmiş Destek açıkken ve kendi Gemini API anahtarınız ayarlıyken bir öğe raporunda **Alt+F1** tuşlarına basarak o raporun dondurulmuş verileri için analiz isteyin. Rapor açma, Markdown kopyalama, ayar değiştirme ve yerel kontroller Gemini isteği göndermez.

İzin listesi öğenin etiketi/rolü, güvenliyse temizlenmiş hesaplanmış ad/açıklama, sınırlı ilişki alıntıları, seçili kontrast ölçüleri ve tanısal kural/durum kanıtını içerir. Düzenlenebilir değerler, korunan veriler, ham işaretleme, URL'ler, seçiciler, pencere tanıtıcıları, ilgisiz nitelikler ve beş yeni bağlam grubu dışlanır. Bilinen hassas değerler ve ayarlı anahtar izin verilen metinde yinelenirse gizlenir. Koruma belirsizse veya düzenlenebilir hedefin kullanılabilir değer kanıtı yoksa isteğe bağlı metin alınmaz. Geçerli JSON verisi 16.000 karakterle sınırlıdır; isteğe bağlı girdiler, çıkarılma nedeni kaydedilerek atılabilir.

Seçilmiş metin yine de Google'a gönderilir; yalnızca göndermek istediğiniz içerik için analiz isteyin. Sayfa metni güvenilmeyen kanıttır. İstem, NVDA dilinde **Screen Reader Usage** ve **Remediation Guide** bölümlerini ister; yanıt görüntülenmeden önce HTML için kaçışlanır ve yalnızca tavsiye niteliğindedir. Hatalar, kimlik bilgileri veya yanıt gövdesi olmadan yalnızca kategori ya da HTTP durumu bildirir. Çevrimdışı/API hatalarında yerel rapor ve kopyalama kullanılabilir kalır.

Ayarlı model `gemini-2.5-flash` olarak korunur. Google şu anda [2.5 modellerine erişimi önceki kullanıcılarla sınırlar](https://ai.google.dev/gemini-api/docs/deprecations#gemini-2.5-flash-models); erişimi olmayan hesap API hatası alabilir. Bu genişletme için gerçek Gemini kabul kontrolü yapılmamıştır.

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
- Upstream belgesi NVDA 2026.1'i bildirir; bu genişletmenin 2023.1, bir ara sürüm ve 2026.1 üzerinde insan tarafından kabul kontrolü beklemektedir.

## Geliştirici derlemesi

Çalışma zamanı CLI komutu yoktur; NVDA komutları ve ayarları kullanılır. Depo kopyasını [pyproject.toml](../../../pyproject.toml) içinde belirtilen araçlarla derleyin:

```text
uv run --no-sync scons
```

[Geliştirme iş akışı](../../../SKILL.md), [ayar şeması](../../globalPlugins/detailedElementInfo/config.py) ve [birikimli değişiklik günlüğü](../../../changelog.md) kaynaklarına bakın. Üretilen yardım ve paketler derleme çıktısıdır.

Odak geçişi ve canlı duyuru gözlemi ertelenmiştir; rapor yalnızca o anda yakalanan kanıtı kaydeder. Bu genişletmenin NVDA 2023.1, bir ara sürüm ve 2026.1 üzerinde insan tarafından kabul kontrolü beklemektedir.

## Yazar

Mustafa Elçiçek <mustafaelcicek5656@gmail.com>

## Geliştirme katkısı

- Kamal Yaser
- E-posta: [kamalyaser31@gmail.com](mailto:kamalyaser31@gmail.com)
- Telegram: [@kamalyaser31](https://t.me/kamalyaser31)

## Lisans

GPL-2.0

## Katkı Sağlama

Katkılar hoş karşılanır! Hataları bildirmeden, iyileştirmeler önermeden veya bir çekme isteği (pull request) açmadan önce lütfen proje deposundaki [Katkı Kılavuzu'nu](../../../CONTRIBUTING.md) okuyun.

## Katkı Sağlayanlar

Detaylı Öğe Bilgisi; kod katkısı sağlayanların, test edenlerin ve destekçilerin yardımıyla geliştirilmektedir. Katkı sağlayanların tam listesi ve her birinin üzerinde çalıştığı konular için proje deposundaki [CONTRIBUTORS.md](../../../CONTRIBUTORS.md) dosyasına bakın.

## Değişiklik Günlüğü

### Sürüm 1.1.0
- Canlı DOM verilerini almak için paketlenmiş bir Manifest V3 Chrome Köprüsü eklendi.
- Alt+F1 ile isteğe bağlı Google Gemini analizi ve NVDA diline uygun yanıtlar eklendi.
- NVDA ile Chrome arasındaki odaklanılan öğe eşleştirmesi iyileştirildi.
- Ukraynaca yerelleştirme tamamlandı; Türkçe ve Ukraynaca çıktılardaki karışık dil sorunu düzeltildi.
- Köprü istekleri Chrome uzantısı kökenleriyle sınırlandırıldı, parola değerleri gizlendi ve yapay zeka çıktısı güvenli biçimde kaçışlandı.
- Etiketli GitHub sürümlerine ayrı bir Chrome Köprüsü ZIP dosyası eklendi.

### Sürüm 1.0.2
- Proje NV Access eklenti şablonuna ve SCons derleme sistemine geçirildi.
- Manifest, çeviri, belge ve eklenti paketi üretimi otomatikleştirildi.

### Sürüm 1.0.1 (NVDA 2026.1 Uyumluluğu)
- NVDA 2026.1 için uyumluluk bilgileri güncellendi

### Sürüm 1.0.0 (İlk Sürüm)
- Detaylı Öğe Bilgisinin ilk sürümü
- ARIA rollerini ve niteliklerini görüntüleme
- Erişilebilir adları ve kaynaklarını gösterme
- Anlamsal uyumsuzlukları algılama
- Üst öğe navigasyonu
