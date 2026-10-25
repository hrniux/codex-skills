#!/usr/bin/env python3
"""Validate this repository's documented metadata subset and skill-local files.

This is deliberately not a general YAML or Markdown parser. See README.md for
accepted metadata syntax and the link forms checked by this contributor tool.
"""

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


class MetadataError(ValueError):
    pass


def string_value(value):
    """Read the schema's nonempty string scalar, rejecting unsupported YAML."""
    value = value.strip()
    hint = "use the supported metadata format documented in README.md"
    if not value:
        raise MetadataError("empty string; " + hint)
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except ValueError as error:
            raise MetadataError(hint) from error
        if not isinstance(parsed, str) or not parsed.strip():
            raise MetadataError(hint)
        try:
            parsed.encode("utf-8")
        except UnicodeEncodeError as error:
            raise MetadataError("metadata strings require valid Unicode; " + hint) from error
        return parsed
    if value.startswith("'"):
        if not re.fullmatch(r"'(?:[^']|'')*'", value):
            raise MetadataError(hint)
        parsed = value[1:-1].replace("''", "'")
        if not parsed.strip():
            raise MetadataError(hint)
        return parsed
    if (
        value[0] in "-?:[]{},&*!|>\"%@`#"
        or re.search(r"\s#|:(?:\s|$)", value)
        or value.lower() in {"true", "false", "null", "~", "yes", "no", "on", "off", ".inf", "+.inf", "-.inf", ".nan"}
        or re.match(r"^[+\-.]?\d", value)
        or "\t" in value
    ):
        raise MetadataError(hint)
    return value


def mapping_entry(line):
    match = re.fullmatch(r"([a-z_]+):(?:[ ]+(.*))?", line)
    if not match:
        raise MetadataError("use the supported metadata format documented in README.md")
    return match.group(1), match.group(2) or ""


def frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise MetadataError("required opening frontmatter delimiter ---")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise MetadataError("required closing frontmatter delimiter ---") from error
    result = {}
    for line in lines[1:end]:
        if not line.strip() or line.startswith("#"):
            continue
        key, raw = mapping_entry(line)
        if key in result:
            raise MetadataError("duplicate metadata key: " + key)
        if key not in {"name", "description"}:
            raise MetadataError("unsupported metadata key: " + key)
        result[key] = string_value(raw)
    for key in ("name", "description"):
        if key not in result:
            raise MetadataError("required metadata field: " + key)
    return result, "\n".join(lines[end + 1:])


def manifest(text):
    result = {}
    section = None
    products = False
    product_indent = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            raise MetadataError("tabs are outside the supported metadata format")
        if not line.startswith(" "):
            key, raw = mapping_entry(line)
            if key not in {"interface", "policy"} or raw:
                raise MetadataError("expected interface: or policy: in supported metadata format")
            if key in result:
                raise MetadataError("duplicate manifest section: " + key)
            result[key] = {}
            section = key
            products = False
            continue
        if products and re.fullmatch(r"(?:  |    )- .+", line):
            indentation = len(line) - len(line.lstrip())
            if product_indent is not None and indentation != product_indent:
                raise MetadataError("products requires consistent indentation in supported metadata format")
            product_indent = indentation
            value = string_value(line.lstrip()[2:])
            if value in result[section]["products"]:
                raise MetadataError("duplicate policy product: " + value)
            result[section]["products"].append(value)
            continue
        if section is None or not line.startswith("  ") or line.startswith("   "):
            raise MetadataError("use two-space fields in supported metadata format")
        key, raw = mapping_entry(line[2:])
        allowed = (
            {"display_name", "short_description", "icon_small", "icon_large", "brand_color", "default_prompt"}
            if section == "interface" else {"products", "allow_implicit_invocation"}
        )
        if key not in allowed:
            raise MetadataError("unsupported " + section + " field: " + key)
        if key in result[section]:
            raise MetadataError("duplicate " + section + " field: " + key)
        products = section == "policy" and key == "products"
        if products:
            if raw:
                raise MetadataError("products requires a block list in supported metadata format")
            result[section][key] = []
            product_indent = None
        elif section == "policy":
            if raw not in {"true", "false"}:
                raise MetadataError("allow_implicit_invocation requires true or false")
            result[section][key] = raw == "true"
        else:
            result[section][key] = string_value(raw)
    for group, keys in (
        ("interface", ("display_name", "short_description", "icon_small", "icon_large")),
        ("policy", ("products", "allow_implicit_invocation")),
    ):
        for key in keys:
            if group not in result or key not in result[group]:
                raise MetadataError("required manifest field: " + group + "." + key)
    if not result["policy"]["products"]:
        raise MetadataError("required nonempty policy.products list")
    color = result["interface"].get("brand_color")
    if color and not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        raise MetadataError("brand_color requires a quoted #RRGGBB string")
    return result


def local_targets(text):
    """Check inline links and resource backticks outside fenced examples."""
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            value = marker.group(1)
            if fence is None:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence) and not line[marker.end():].strip():
                fence = None
            continue
        if fence:
            continue
        for match in re.finditer(r"\[[^\]\n]*\]\(<?([^\s)>]+)>?(?:\s+[^)]*)?\)", line):
            target = match.group(1)
            if not urlsplit(target).scheme and not target.startswith(("#", "//")):
                yield target, False
        for match in re.finditer(r"`((?:\./)?(?:references|scripts|assets)/[^`\n]+)`", line):
            yield match.group(1), True


def validate(root):
    errors = []
    skills = []
    directory = root / "skills"
    if not directory.is_dir():
        return {"schema_version": 1, "ok": False, "skills": [], "errors": ["required skills directory: " + str(directory)]}
    directories = sorted(path for path in directory.iterdir() if path.is_dir())
    if not directories:
        errors.append("required at least one skill directory")
    for skill in directories:
        label = "skills/" + skill.name
        try:
            skill.resolve().relative_to(directory.resolve())
        except ValueError:
            errors.append(label + ": outside skills directory")
            continue

        def checked_file(path):
            try:
                path.resolve().relative_to(skill.resolve())
            except ValueError:
                errors.append(label + ": outside skill: " + str(path.relative_to(skill)))
                return False
            if not path.is_file():
                errors.append(label + ": required file missing: " + str(path.relative_to(skill)))
                return False
            return True

        metadata = {}
        interface = {}
        body = ""
        for path, parser in ((skill / "SKILL.md", frontmatter), (skill / "agents/openai.yaml", manifest)):
            if not checked_file(path):
                continue
            try:
                parsed = parser(path.read_text(encoding="utf-8"))
                if path.name == "SKILL.md":
                    metadata, body = parsed
                else:
                    interface = parsed["interface"]
            except (MetadataError, OSError, UnicodeError) as error:
                errors.append(label + "/" + str(path.relative_to(skill)) + ": " + str(error))
        if metadata and metadata["name"] != skill.name:
            errors.append(label + "/SKILL.md: name must match directory: " + skill.name)
        if metadata and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", metadata["name"]):
            errors.append(label + "/SKILL.md: name must use lowercase letters, digits and single hyphens")
        for field in ("icon_small", "icon_large"):
            if field in interface:
                checked_file(skill / interface[field])
        resources = []
        documents = [(skill / "SKILL.md", body)]
        for group in ("assets", "references", "scripts"):
            base = skill / group
            if base.exists() and not base.is_dir():
                errors.append(label + ": expected directory: " + group)
                continue
            if base.is_symlink():
                errors.append(label + ": resource directories must not be symlinks: " + group)
                continue
            for path in sorted(base.rglob("*")):
                if path.is_symlink() and path.is_dir():
                    errors.append(label + ": resource directories must not be symlinks: " + str(path.relative_to(skill)))
                elif path.is_file() or path.is_symlink():
                    if checked_file(path):
                        resources.append(path.relative_to(skill).as_posix())
                        if group == "references" and path.suffix.lower() == ".md":
                            documents.append((path, path.read_text(encoding="utf-8")))
        for document, content in documents:
            for target, skill_relative in local_targets(content):
                path = unquote(urlsplit(target).path)
                if path:
                    checked_file((skill if skill_relative else document.parent) / path)
        skills.append({"name": skill.name, "description": metadata.get("description"),
                       "display_name": interface.get("display_name"), "resources": sorted(resources)})
    return {"schema_version": 1, "ok": not errors, "skills": skills, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="repository root")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        report = validate(args.root.resolve())
    except (OSError, UnicodeError, ValueError) as error:
        report = {"schema_version": 1, "ok": False, "skills": [], "errors": [str(error)]}
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in report["skills"]:
            print(item["name"] + ": " + (item["description"] or "invalid metadata"))
        for error in report["errors"]:
            print("ERROR: " + error)
        print(str(len(report["skills"])) + " skill(s); " + str(len(report["errors"])) + " error(s)")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
