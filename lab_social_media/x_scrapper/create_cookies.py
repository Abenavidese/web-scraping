import json
import time

def create_state_file():
    print("=== Generador de Cookies para X.com ===")
    print("Por favor, ingresa los valores de las cookies de tu navegador.")
    print("Instrucciones:")
    print("1. Abre X.com en tu navegador (Chrome/Edge/Firefox).")
    print("2. Presiona F12 para abrir las Developer Tools.")
    print("3. Ve a la pestaÃ±a 'Application' (o 'Storage').")
    print("4. Busca 'Cookies' en el menÃº lateral y selecciona 'https://x.com'.")
    print("5. Copia el valor de 'auth_token' y 'ct0'.")
    
    auth_token = input("\nIntroduce el valor de la cookie 'auth_token': ").strip()
    ct0 = input("Introduce el valor de la cookie 'ct0': ").strip()

    if not auth_token or not ct0:
        print("Error: Debes ingresar ambos valores.")
        return

    # Estructura de state.json para Playwright
    # Seteamos las cookies para .x.com y .twitter.com para asegurar compatibilidad
    state = {
        "cookies": [
            {
                "name": "auth_token",
                "value": auth_token,
                "domain": ".x.com",
                "path": "/",
                "expires": -1,
                "httpOnly": True,
                "secure": True,
                "sameSite": "None"
            },
            {
                "name": "ct0",
                "value": ct0,
                "domain": ".x.com",
                "path": "/",
                "expires": -1,
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            },
             {
                "name": "auth_token",
                "value": auth_token,
                "domain": ".twitter.com",
                "path": "/",
                "expires": -1,
                "httpOnly": True,
                "secure": True,
                "sameSite": "None"
            },
            {
                "name": "ct0",
                "value": ct0,
                "domain": ".twitter.com",
                "path": "/",
                "expires": -1,
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            }
        ],
        "origins": []
    }

    with open("state.json", "w", encoding='utf-8') as f:
        json.dump(state, f, indent=2)

    print("\n[Exito] Archivo 'state.json' creado correctamente.")
    print("Ahora puedes ejecutar 'python main.py' y usarÃ¡ estas cookies para entrar.")

if __name__ == "__main__":
    create_state_file()
