"""app.prompts.loader 단위 테스트.

검증 대상:
  - load_prompt_yaml: 파일 없음 / 잘못된 포맷 / 필수 키 누락 / default variant 없음
                    / variant 구조 오류 / 정상 로드
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.prompts.loader import load_prompt_yaml


def _write_yaml(path: Path, data: object) -> Path:
    path.write_text(yaml.dump(data), encoding="utf-8")
    return path


def _valid_template(name: str = "test") -> dict:
    return {
        "name": name,
        "version": "1.0",
        "variants": {
            "default": {
                "system": "You are a helpful assistant.",
                "user": "Hello {name}",
            }
        },
    }


# ── FileNotFoundError ──────────────────────────────────────────────────────────


class TestFileNotFound:
    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            load_prompt_yaml(tmp_path / "nonexistent.yaml")


# ── 포맷 오류 ──────────────────────────────────────────────────────────────────


class TestInvalidFormat:
    def test_non_dict_raises_value_error(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.yaml"
        f.write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid prompt template format"):
            load_prompt_yaml(f)


# ── 필수 키 누락 ───────────────────────────────────────────────────────────────


class TestMissingRequiredKeys:
    def test_missing_name_raises(self, tmp_path: Path) -> None:
        data = _valid_template()
        data.pop("name")
        f = _write_yaml(tmp_path / "t.yaml", data)
        with pytest.raises(ValueError, match="Missing required keys"):
            load_prompt_yaml(f)

    def test_missing_version_raises(self, tmp_path: Path) -> None:
        data = _valid_template()
        data.pop("version")
        f = _write_yaml(tmp_path / "t.yaml", data)
        with pytest.raises(ValueError, match="Missing required keys"):
            load_prompt_yaml(f)

    def test_missing_variants_raises(self, tmp_path: Path) -> None:
        data = _valid_template()
        data.pop("variants")
        f = _write_yaml(tmp_path / "t.yaml", data)
        with pytest.raises(ValueError, match="Missing required keys"):
            load_prompt_yaml(f)


# ── default variant 없음 ──────────────────────────────────────────────────────


class TestMissingDefaultVariant:
    def test_no_default_raises(self, tmp_path: Path) -> None:
        data = _valid_template()
        data["variants"] = {"experimental": {"system": "s", "user": "u"}}
        f = _write_yaml(tmp_path / "t.yaml", data)
        with pytest.raises(ValueError, match="Missing 'default' variant"):
            load_prompt_yaml(f)


# ── variant 구조 오류 ─────────────────────────────────────────────────────────


class TestInvalidVariantStructure:
    def test_variant_missing_system_raises(self, tmp_path: Path) -> None:
        data = _valid_template()
        data["variants"]["default"] = {"user": "Hello"}
        f = _write_yaml(tmp_path / "t.yaml", data)
        with pytest.raises(ValueError, match="must have 'system' and 'user'"):
            load_prompt_yaml(f)

    def test_variant_missing_user_raises(self, tmp_path: Path) -> None:
        data = _valid_template()
        data["variants"]["default"] = {"system": "You are helpful."}
        f = _write_yaml(tmp_path / "t.yaml", data)
        with pytest.raises(ValueError, match="must have 'system' and 'user'"):
            load_prompt_yaml(f)

    def test_secondary_variant_missing_keys_raises(self, tmp_path: Path) -> None:
        data = _valid_template()
        data["variants"]["v2"] = {"system": "Only system, no user"}
        f = _write_yaml(tmp_path / "t.yaml", data)
        with pytest.raises(ValueError, match="must have 'system' and 'user'"):
            load_prompt_yaml(f)


# ── 정상 로드 ─────────────────────────────────────────────────────────────────


class TestValidLoad:
    def test_returns_dict(self, tmp_path: Path) -> None:
        data = _valid_template()
        f = _write_yaml(tmp_path / "t.yaml", data)
        result = load_prompt_yaml(f)
        assert isinstance(result, dict)

    def test_name_preserved(self, tmp_path: Path) -> None:
        data = _valid_template("my_prompt")
        f = _write_yaml(tmp_path / "t.yaml", data)
        result = load_prompt_yaml(f)
        assert result["name"] == "my_prompt"

    def test_accepts_path_string(self, tmp_path: Path) -> None:
        data = _valid_template()
        f = _write_yaml(tmp_path / "t.yaml", data)
        result = load_prompt_yaml(str(f))
        assert "name" in result

    def test_multiple_variants_valid(self, tmp_path: Path) -> None:
        data = _valid_template()
        data["variants"]["v2"] = {"system": "Sys", "user": "User {x}"}
        f = _write_yaml(tmp_path / "t.yaml", data)
        result = load_prompt_yaml(f)
        assert "v2" in result["variants"]
