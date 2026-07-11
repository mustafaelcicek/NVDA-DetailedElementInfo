# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] 

### Added
- **Chrome Bridge (Gelişmiş Destek):** Eklentiye özel bir Chrome uzantısı (Bridge) geliştirildi. Bu sayede NVDA, tarayıcının sanal belleğine (virtual buffer) mahkum kalmadan sayfanın gerçek DOM verisine, HTML yapısına ve aktif özelliklerine doğrudan erişebilir hale gelmesi planlanıyor.
- **Yapay Zeka (Gemini) Analizi:** Çekilen ham DOM verisini ve ARIA niteliklerini analiz etmek için sisteme Google Gemini yeteneği kazandırıldı. (dom verisi alındıktan sonra devreye girecek.)
- **Chrome Eklentisi Haberleşmesi** `http.server`, `urllib.request` kullanılarak arka planda yerel bir iletişim sunucusu kuruldu. karıştı.
- **Yapılandırılmış HTML Raporlama:** Rapor çıktıları düz metin yerine temiz başlıklar (H1, H2) ve yapılandırılmış listeler içeren hiyerarşik bir HTML arayüzüne (Browseable Message) geçildi. 
- **Ayarlar Paneli Güncellemesi:** NVDA eklenti ayarlarına "Gelişmiş Desteği Etkinleştir" ve "Gemini API Anahtarı" seçenekleri eklendi.

### Changed
- Raporlama arayüzü, hem NVDA'nın standart IA2 verilerini hem de Chrome ve Yapay Zeka'dan gelen derinlemesine analizleri gösterecek şekilde zenginleştirildi.
