<<<<<<< HEAD
# XAUUSD LiveBot — TradingView → Railway → MetaApi → XM Demo
=======
# XAUUSD LiveBot — TradingView -> Railway -> MetaApi -> XM Demo
>>>>>>> 4be91a9 (ilk sürüm)

Bu proje **XAUUSDBot** (backtest/MQL5) projesinden **bagimsizdir**. Amac: TradingView
Pine Script alert'lerini bir webhook uzerinden alip, MetaApi araciligiyla XM'deki
**demo** hesapta gercek zamanli islem actirmak ve yonetmek.

## Mimari

<<<<<<< HEAD
```
=======
>>>>>>> 4be91a9 (ilk sürüm)
TradingView (Pine alert, sadece GIRIS sinyali)
        |  webhook POST {"action","symbol","volume","sl","tp"}
        v
Railway (bu proje, FastAPI)
<<<<<<< HEAD
  ├─ /webhook  -> guvenlik kontrolleri (DD, spread, secret) + lot hesabi (risk.py)
  │              + MetaApi'ye market emri (metaapi_client.py)
  └─ arka plan dongusu (position_manager.py, her POLL_SEC saniyede bir):
=======
  - /webhook  -> guvenlik kontrolleri (DD, spread, secret) + lot hesabi (risk.py)
                 + MetaApi'ye market emri (metaapi_client.py)
  - arka plan dongusu (position_manager.py, her POLL_SEC saniyede bir):
>>>>>>> 4be91a9 (ilk sürüm)
        - TP1 (%60) kismi kapama
        - Runner (%40) icin ATR-trailing + GERCEK hard-cap (RUNNER_CAP_R)
        - Zaman-stopu (MAX_HOLD_MINUTES)
        - EMA8/21 ters-cross erken cikis
        - Iki katmanli DD korumasi (periyodik + kalici hard-floor)
        v
MetaApi -> XM MT5 DEMO hesabi (gercek emirler burada gerceklesir)
<<<<<<< HEAD
```
=======
>>>>>>> 4be91a9 (ilk sürüm)

**Onemli tasarim karari:** Pine, SADECE giris sinyalini (ilk SL/TP1 seviyeleriyle
birlikte) webhook'a gonderir. TUM pozisyon yonetimi (TP1 kismi kapama, trailing,
runner hard-cap, zaman-stopu, EMA-exit) **bu Python servisinde**, MetaApi
<<<<<<< HEAD
uzerinden CANLI olarak yapilir - Pine'in kendi ic `strategy.exit()` guncellemeleri
=======
uzerinden CANLI olarak yapilir - Pine'in kendi ic strategy.exit() guncellemeleri
>>>>>>> 4be91a9 (ilk sürüm)
gercek hesaba YANSIMAZ, sadece TradingView'in kendi simulasyonunda kalir.

## Kurulum

### 1) MetaApi
- MetaApi hesabina (https://metaapi.cloud) XM demo hesabini ekle, bir
  **account ID** ve **API token** al.
<<<<<<< HEAD
- **KRITIK:** `METAAPI_ACCOUNT_ID`'nin gercekten DEMO hesaba isaret ettigini
  MetaApi panelinden bizzat dogrula - bu kod bunu otomatik kontrol EDEMEZ
  (MetaApi SDK'sinda demo/canli ayrimi hesap meta-verisine gore degisir,
  bkz metaapi_client.py'deki not).

### 2) Ortam degiskenleri
`.env.example`'i kopyala, `Railway > Variables` sekmesine gir (asla .env
dosyasini git'e commitleme). **DRY_RUN=true ile BASLA.**

### 3) Railway deploy
```bash
# Bu klasoru GitHub repo'na push et, sonra Railway'de "New Project -> Deploy from GitHub"
git init
git add .
git commit -m "XAUUSD LiveBot ilk kurulum"
git remote add origin <SENIN_REPO_URL>
git push -u origin main
```
Railway repo'yu algilayip `Procfile`'daki `web` process'ini calistiracak.

### 4) TradingView alert
Pine stratejinde (webhook JSON'u zaten uretiyor) alert olustururken:
- Webhook URL: `https://<railway-app>.up.railway.app/webhook`
- Alert mesaji: Pine'in urettigi JSON'a `"secret":"<WEBHOOK_SECRET>"` alanini ekle
  (ya da HTTP header olarak `X-Webhook-Secret` gonder).

### 5) Test sirasi (ONERILEN, ATLAMA)
1. `DRY_RUN=true` ile deploy et.
2. TradingView'de birkac alert tetiklet, Railway loglarinda `[DRY_RUN]` satirlarini
   izle - dogru lot/SL/TP hesaplandigini gor.
3. `/health` endpoint'ini kontrol et (`hard_halted`/`halted` durumlari, takip
   edilen pozisyonlar).
4. Emin olunca `DRY_RUN=false` yap, KUCUK bir MaxLots ile (or. 0.01) ilk
   gercek demo islemleri gozlemle.

## Durustluk notlari (ONEMLI, oku)

- **Bu kod GERCEK bir MetaApi hesabina karsi TEST EDILMEDI** - MetaApi
  erisimim yok. `metaapi_client.py`'deki metod adlari (`create_market_buy_order`,
  `modify_position`, `close_position_partially`, `get_symbol_price`,
  `get_historical_candles`) MetaApi Python SDK'sinin bilinen genel kullanim
  seklidir, ama SDK surumleri arasi degisebilir. Deploy etmeden once resmi
  dokumantasyonla (https://metaapi.cloud/docs/client/python/) karsilastir.
- `requirements.txt`'teki `metaapi-cloud-sdk` versiyonu TAHMINIDIR - PyPI'da
  guncel surumu kontrol et.
- Lot buyuklugu **sunucu tarafinda YENIDEN hesaplanir** (Pine'in gonderdigi
  `volume` alani KULLANILMAZ) - bu, GrafikOku Pine portunda karsilasilan
  "syminfo.pointvalue XM'le uyusmuyor, lot hep tavanda" sorununu onlemek icin
  kasitli bir tasarim karari.
- Railway'in varsayilan dosya sistemi **ephemeral**'dir - `live_bot_state.json`
  (DD-tepe takibi, acik pozisyon runner durumu) her redeploy'da sifirlanabilir.
  Gercekten kalici durum istiyorsan bir Railway Volume bagla.
- Spread `MAX_SPREAD_POINTS=65` olarak ayarlandi (kullanici talebi) - GOLD
  icin "point" birimi kullanildi (1 point = $0.01), "pip" degil; XM'in canli
  spread'i bu oturumda ~53-57 puan olculdu, 65 makul bir tavan.
=======
- **KRITIK:** METAAPI_ACCOUNT_ID'nin gercekten DEMO hesaba isaret ettigini
  MetaApi panelinden bizzat dogrula.

### 2) Ortam degiskenleri
.env.example'i kopyala, Railway > Variables sekmesine gir. **DRY_RUN=true ile BASLA.**

### 3) Railway deploy
Bu klasoru GitHub repo'na push et, Railway'de "New Project -> Deploy from GitHub".
Railway repo'yu algilayip Procfile'daki web process'ini calistiracak.

### 4) TradingView alert
- Webhook URL: https://<railway-app>.up.railway.app/webhook
- Alert kosulu: "Any alert() function call" - mesaj kutusuna dokunma.

### 5) Test sirasi
1. DRY_RUN=true ile deploy et.
2. Railway loglarinda [DRY_RUN] satirlarini izle.
3. /health endpoint'ini kontrol et.
4. Emin olunca DRY_RUN=false yap.

## Durustluk notlari

- Bu kod GERCEK bir MetaApi hesabina karsi onceden test edilmemisti (sonradan
  canli testle dogrulandi, magic alaninin int olmasi gerektigi gibi gercek
  bir uyumsuzluk bulundu ve duzeltildi).
- Lot buyuklugu sunucu tarafinda YENIDEN hesaplanir (Pine'in gonderdigi
  volume alani KULLANILMAZ).
- Railway'in varsayilan dosya sistemi ephemeral'dir - live_bot_state.json
  her redeploy'da sifirlanabilir.
- Spread MAX_SPREAD_POINTS=65 (kullanici talebi), point birimi.
>>>>>>> 4be91a9 (ilk sürüm)
