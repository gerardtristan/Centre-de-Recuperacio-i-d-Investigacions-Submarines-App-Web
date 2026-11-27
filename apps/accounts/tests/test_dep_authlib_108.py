"""La biblioteca d'OpenID Connect hi és (decisió 108, D.2)."""

from authlib.integrations.django_client import OAuth


def test_authlib_registra_un_client_oidc_sense_xarxa():
    oauth = OAuth()
    oauth.register(
        "proves",
        client_id="client-de-proves",
        client_secret="contrasenya-de-proves-1954",  # noqa: S106 (valor únic de proves)
        server_metadata_url="https://proves.invalid/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    assert oauth.create_client("proves").client_id == "client-de-proves"
