from pathlib import Path

import pytest

from check_commit_msg import check, main, subject_from_file


@pytest.mark.parametrize(
    "subject",
    [
        "feat: crear cuenta",
        "fix(fx): usar cotización de venta",
        "feat(credit-cards)!: cambiar el cálculo de cuotas",
        "feat(shared): chequeo de base de datos en /health [PF-19] (#6)",
    ],
)
def test_accepts_valid_prefix(subject: str) -> None:
    assert check(subject) is None


@pytest.mark.parametrize(
    "subject",
    ["crear cuenta", "feature: crear cuenta", "feat:sin espacio", "Feat: mayúscula", "feat(): x"],
)
def test_rejects_invalid_prefix(subject: str) -> None:
    assert check(subject) is not None


def test_require_key() -> None:
    assert check("feat: crear cuenta [PF-14]", require_key=True) is None
    assert check("feat: crear cuenta", require_key=True) is not None


def test_subject_from_file_skips_comments(tmp_path: Path) -> None:
    message = tmp_path / "COMMIT_EDITMSG"
    message.write_text("\n# comentario de git\nfix: algo\n\ncuerpo\n", encoding="utf-8")

    assert subject_from_file(message) == "fix: algo"


def test_empty_message_is_invalid(tmp_path: Path) -> None:
    message = tmp_path / "COMMIT_EDITMSG"
    message.write_text("# solo comentarios\n", encoding="utf-8")

    assert check(subject_from_file(message)) is not None


def test_main_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    message = tmp_path / "COMMIT_EDITMSG"
    message.write_text("arreglo cosas\n", encoding="utf-8")

    assert main(["--file", str(message)]) == 1
    assert "Prefijo inválido" in capsys.readouterr().err
    assert main(["docs: actualizar README", "ci: agregar workflow"]) == 0


def test_max_length_counts_characters_not_bytes() -> None:
    # 72 caracteres con tildes: son más de 72 bytes, pero entran.
    subject = "feat(frontend): perfil, tarjeta y últimos movimientos más largos [PF-79]"
    assert len(subject) == 72
    assert check(subject, max_length=72) is None
    assert check(subject + "x", max_length=72) is not None
    assert main(["--max-length", "72", subject + "x"]) == 1
