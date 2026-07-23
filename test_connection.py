import asyncio
import httpx
import config
import metaapi_client as mt


async def test_all():
    print("=== 1. RAILWAY HEALTH TEST ===")
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("http://localhost:8000/health")
            print(f"Railway Health: {r.status_code} {r.json()}")
    except Exception as e:
        print(f"Railway HATA: {e}")

    print("\n=== 2. GITHUB/CONFIG TEST ===")
    print(f"WEBHOOK_SECRET yüklendi mi: {config.WEBHOOK_SECRET[:3]}***")
    print(f"SYMBOL: {config.SYMBOL}")
    print(f"RISK_PCT: {config.RISK_PCT}")

    print("\n=== 3. METAAPI BAĞLANTI TEST ===")
    try:
        await mt.connect()
        account = await mt.get_account_info()
        print(f"MetaAPI Bağlandı! Hesap: {account['login']} Balance: {account['balance']}")
        await mt.disconnect()
    except Exception as e:
        print(f"MetaAPI HATA: {e}")

    print("\n=== TEST BİTTİ ===")


if __name__ == "__main__":
    asyncio.run(test_all())
