# -*- coding: utf-8 -*-
"""
Script de Prueba Unitaria para X Scraper
Diagnóstico de problemas de apertura y cierre inmediato
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=env_path)

from scraper import XScraper

async def test_basic_connection():
    """Test 1: Verifica que el scraper pueda iniciar y mantener el navegador abierto"""
    print("=" * 60)
    print("TEST 1: Inicialización básica del navegador")
    print("=" * 60)
    
    scraper = XScraper(headless=False)
    
    try:
        print("✓ Inicializando scraper...")
        await scraper.start()
        print("✓ Navegador iniciado correctamente")
        
        print("✓ Navegando a X.com...")
        await scraper.page.goto("https://x.com")
        print("✓ Página cargada")
        
        # Mantener abierto 5 segundos para inspección
        print("\n⏳ Manteniendo navegador abierto por 5 segundos...")
        await asyncio.sleep(5)
        
        print("✅ TEST 1 PASADO: El navegador se inició correctamente")
        return True
        
    except Exception as e:
        print(f"❌ TEST 1 FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("\n🔒 Cerrando navegador...")
        await scraper.close()
        print("✓ Navegador cerrado\n")


async def test_login():
    """Test 2: Verifica el proceso de login"""
    print("=" * 60)
    print("TEST 2: Proceso de Login")
    print("=" * 60)
    
    USERNAME = os.getenv("X_USERNAME", "@jsudbs61239")
    PASSWORD = os.getenv("X_PASSWORD", "xxKPeYAEI00fohS")
    
    print(f"Usuario configurado: {USERNAME}")
    print(f"Password configurado: {'*' * len(PASSWORD)}")
    
    scraper = XScraper(headless=False)
    
    try:
        await scraper.start()
        print("✓ Navegador iniciado")
        
        print("\n🔐 Intentando login...")
        await scraper.login(USERNAME, PASSWORD)
        print("✓ Login completado (o ya estaba autenticado)")
        
        # Verificar si estamos en home
        current_url = scraper.page.url
        print(f"URL actual: {current_url}")
        
        if "home" in current_url or "x.com" in current_url:
            print("✅ TEST 2 PASADO: Login exitoso")
            
            # Mantener abierto para inspección
            print("\n⏳ Manteniendo sesión abierta por 10 segundos para verificar...")
            await asyncio.sleep(10)
            return True
        else:
            print(f"⚠️  TEST 2 ADVERTENCIA: URL inesperada: {current_url}")
            await asyncio.sleep(10)
            return False
            
    except Exception as e:
        print(f"❌ TEST 2 FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        
        # Mantener abierto para ver el error
        print("\n⏳ Manteniendo navegador abierto por 10 segundos para inspección...")
        await asyncio.sleep(10)
        return False
    finally:
        print("\n🔒 Cerrando navegador...")
        await scraper.close()
        print("✓ Navegador cerrado\n")


async def test_simple_search():
    """Test 3: Verifica búsqueda simple sin login"""
    print("=" * 60)
    print("TEST 3: Búsqueda Simple (solo 3 tweets)")
    print("=" * 60)
    
    scraper = XScraper(headless=False)
    
    try:
        await scraper.start()
        print("✓ Navegador iniciado")
        
        # Ir directamente a búsqueda pública (no requiere login)
        test_query = "Python programming"
        print(f"\n🔍 Buscando: '{test_query}'")
        
        tweets = await scraper.scrape_search(test_query, count=3)
        
        print(f"\n📊 Tweets encontrados: {len(tweets)}")
        
        if tweets:
            print("\n📝 Muestra de tweets:")
            for i, tweet in enumerate(tweets[:3], 1):
                print(f"\n  Tweet {i}:")
                print(f"    Autor: {tweet.get('author', 'N/A')[:50]}")
                print(f"    Texto: {tweet.get('text', 'N/A')[:80]}...")
                print(f"    URL: {tweet.get('url', 'N/A')}")
            
            print(f"\n✅ TEST 3 PASADO: Se extrajeron {len(tweets)} tweets")
            return True
        else:
            print("\n⚠️  TEST 3 ADVERTENCIA: No se extrajeron tweets")
            print("⏳ Manteniendo navegador abierto por 15 segundos para inspección...")
            await asyncio.sleep(15)
            return False
            
    except Exception as e:
        print(f"❌ TEST 3 FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n⏳ Manteniendo navegador abierto por 15 segundos para inspección...")
        await asyncio.sleep(15)
        return False
    finally:
        print("\n🔒 Cerrando navegador...")
        await scraper.close()
        print("✓ Navegador cerrado\n")


async def test_full_workflow():
    """Test 4: Workflow completo - Login + Búsqueda"""
    print("=" * 60)
    print("TEST 4: Workflow Completo (Login + Búsqueda)")
    print("=" * 60)
    
    USERNAME = os.getenv("X_USERNAME", "@jsudbs61239")
    PASSWORD = os.getenv("X_PASSWORD", "xxKPeYAEI00fohS")
    
    scraper = XScraper(headless=False)
    
    try:
        await scraper.start()
        print("✓ Navegador iniciado")
        
        print("\n🔐 Haciendo login...")
        await scraper.login(USERNAME, PASSWORD)
        print("✓ Login completado")
        
        test_query = "Inteligencia Artificial"
        print(f"\n🔍 Buscando: '{test_query}' (5 tweets)...")
        
        tweets = await scraper.scrape_search(test_query, count=5)
        
        print(f"\n📊 Tweets encontrados: {len(tweets)}")
        
        if tweets and len(tweets) >= 3:
            print("\n📝 Primeros 3 tweets:")
            for i, tweet in enumerate(tweets[:3], 1):
                print(f"\n  Tweet {i}:")
                print(f"    Autor: {tweet.get('author', 'N/A')[:50]}")
                print(f"    Texto: {tweet.get('text', 'N/A')[:100]}...")
            
            print(f"\n✅ TEST 4 PASADO: Workflow completo funciona correctamente")
            print("⏳ Manteniendo navegador abierto por 5 segundos...")
            await asyncio.sleep(5)
            return True
        else:
            print(f"\n⚠️  TEST 4 ADVERTENCIA: Solo se extrajeron {len(tweets)} tweets")
            print("⏳ Manteniendo navegador abierto por 15 segundos para inspección...")
            await asyncio.sleep(15)
            return False
            
    except Exception as e:
        print(f"❌ TEST 4 FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n⏳ Manteniendo navegador abierto por 15 segundos para inspección...")
        await asyncio.sleep(15)
        return False
    finally:
        print("\n🔒 Cerrando navegador...")
        await scraper.close()
        print("✓ Navegador cerrado\n")


async def main():
    """Ejecuta todos los tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "SUITE DE PRUEBAS UNITARIAS - X SCRAPER" + " " * 10 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    results = {}
    
    # Test 1: Inicialización
    results['test_1'] = await test_basic_connection()
    await asyncio.sleep(2)
    
    # Test 2: Login
    results['test_2'] = await test_login()
    await asyncio.sleep(2)
    
    # Test 3: Búsqueda simple
    results['test_3'] = await test_simple_search()
    await asyncio.sleep(2)
    
    # Test 4: Workflow completo
    results['test_4'] = await test_full_workflow()
    
    # Resumen
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 18 + "RESUMEN DE PRUEBAS" + " " * 20 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    for test_name, passed in results.items():
        status = "✅ PASADO" if passed else "❌ FALLIDO"
        print(f"  {test_name.upper()}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print()
    print(f"  Total: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("\n  🎉 TODAS LAS PRUEBAS PASARON")
    else:
        print(f"\n  ⚠️  {total - passed} prueba(s) fallaron")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
