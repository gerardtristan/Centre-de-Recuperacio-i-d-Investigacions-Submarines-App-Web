"""Genera els secrets del servidor de proves (decisió 099) i els escriu a la sortida estàndard en
format «NOM=valor». arrenca.ps1 l'executa una sola vegada, dins de la imatge, i els desa a
`deploy/proves/local/secrets.env`, que no va mai al repositori. Cada portàtil té els seus.

Cap valor no conté «$» ni cometes: el fitxer es pot llegir tal qual des de Docker Compose."""

import secrets

import pyotp
from cryptography.fernet import Fernet


def genera() -> dict[str, str]:
    db_password = secrets.token_urlsafe(24)
    return {
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(50),
        "FIELD_ENCRYPTION_KEYS": Fernet.generate_key().decode(),
        "MANDATE_ENCRYPTION_KEYS": "1:" + Fernet.generate_key().decode(),
        "CARD_QR_KEYS": "k1:" + secrets.token_urlsafe(48),
        "CARD_QR_ACTIVE_KEY": "k1",
        "POSTGRES_PASSWORD": db_password,
        "DATABASE_URL": f"postgres://cris:{db_password}@db:5432/cris",
        # El segon factor dels comptes d'administració inventats (seed_demo_data, 090).
        "STAGING_TOTP_SECRET": pyotp.random_base32(32),
        # La contrasenya del davant (usuari «proves»). El Caddy només en rep el resum (bcrypt).
        "ACCES_CONTRASENYA": secrets.token_urlsafe(12),
    }


if __name__ == "__main__":
    for name, value in genera().items():
        print(f"{name}={value}")
