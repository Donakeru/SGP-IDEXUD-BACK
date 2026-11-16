"""Pruebas de GET /api/proposal/documents/{uuid_archivo}."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app
from app.models.documento import Documento
from app.repositories.documento_repository import DocumentoRepository
from app.services import storage_service

EXPEDIENTE = "11111111-1111-1111-1111-111111111111"
PDF_BYTES = b"%PDF-1.4 contenido de prueba"


def _documento(ruta: str, **overrides) -> Documento:
    values = {
        "uuid_archivo": uuid4(),
        "ruta_archivo": ruta,
        "nombre_original": "Propuesta año 2026.pdf",
        "tipo_mime": "application/pdf",
        "es_activo": True,
        "fecha_eliminacion": None,
        "estado_carga": "cargado",
    }
    values.update(overrides)
    return Documento(**values)


@pytest.fixture
def storage(tmp_path, monkeypatch):
    """Usa tmp_path/storage como storage_root y crea un PDF de ejemplo."""
    root = tmp_path / "storage"
    (root / EXPEDIENTE).mkdir(parents=True)
    (root / EXPEDIENTE / "archivo.pdf").write_bytes(PDF_BYTES)
    (tmp_path / "secreto.txt").write_text("fuera de storage_root")
    monkeypatch.setattr(
        storage_service, "settings", SimpleNamespace(storage_root=root)
    )
    return root


@pytest.fixture
def client(monkeypatch):
    documentos: dict = {}
    monkeypatch.setattr(
        DocumentoRepository,
        "get_by_uuid",
        lambda self, uuid_archivo: documentos.get(uuid_archivo),
    )

    def fake_db():
        yield object()

    app.dependency_overrides[get_db] = fake_db
    test_client = TestClient(app)
    test_client.documentos = documentos
    yield test_client
    app.dependency_overrides.clear()


def _register(client, **overrides) -> Documento:
    ruta = overrides.pop("ruta", f"storages/{EXPEDIENTE}/archivo.pdf")
    documento = _documento(ruta, **overrides)
    client.documentos[documento.uuid_archivo] = documento
    return documento


def _url(documento: Documento) -> str:
    return f"/api/proposal/documents/{documento.uuid_archivo}"


def test_inline_devuelve_pdf_con_nombre_codificado(client, storage):
    documento = _register(client)

    response = client.get(_url(documento))

    assert response.status_code == 200
    assert response.content == PDF_BYTES
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["x-content-type-options"] == "nosniff"
    disposition = response.headers["content-disposition"]
    assert disposition.startswith("inline;")
    assert "filename*=utf-8''Propuesta%20a%C3%B1o%202026.pdf" in disposition


def test_download_true_devuelve_attachment(client, storage):
    documento = _register(client)

    response = client.get(_url(documento), params={"download": "true"})

    assert response.status_code == 200
    assert response.content == PDF_BYTES
    assert response.headers["content-disposition"].startswith("attachment;")
    assert response.headers["x-content-type-options"] == "nosniff"


def test_tipo_no_previsualizable_fuerza_attachment(client, storage):
    (storage / EXPEDIENTE / "pagina.html").write_text("<script>alert(1)</script>")
    documento = _register(
        client,
        ruta=f"storages/{EXPEDIENTE}/pagina.html",
        nombre_original="pagina.html",
        tipo_mime="text/html",
    )

    response = client.get(_url(documento), params={"download": "false"})

    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("attachment;")


def test_uuid_inexistente_devuelve_404(client, storage):
    response = client.get(f"/api/proposal/documents/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "overrides",
    [
        {"es_activo": False},
        {"estado_carga": "pendiente"},
        {"ruta": f"storages/{EXPEDIENTE}/no-existe.pdf"},
    ],
    ids=["inactivo", "no-cargado", "archivo-ausente-en-disco"],
)
def test_documento_no_disponible_devuelve_404(client, storage, overrides):
    documento = _register(client, **overrides)

    assert client.get(_url(documento)).status_code == 404


@pytest.mark.parametrize(
    "ruta",
    [
        "storages/../secreto.txt",
        "storages/../../secreto.txt",
        f"storages/{EXPEDIENTE}/../../secreto.txt",
        "../secreto.txt",
        "..\\secreto.txt",
    ],
)
def test_ruta_fuera_de_storage_root_devuelve_404(client, storage, tmp_path, ruta):
    assert (tmp_path / "secreto.txt").exists()
    documento = _register(client, ruta=ruta)

    assert client.get(_url(documento)).status_code == 404


def test_ruta_absoluta_devuelve_404(client, storage, tmp_path):
    documento = _register(client, ruta=str(tmp_path / "secreto.txt"))

    assert client.get(_url(documento)).status_code == 404
