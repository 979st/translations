import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List
from xml.dom import minidom

import tomllib


def main():
    repository = Path(__file__).parent.resolve()
    projects = [p.name for p in (repository / "projects").iterdir() if p.is_dir()]

    allowed_locales = [
        line.strip()
        for line in open((repository / "allowed_locales.txt"), "r", encoding="utf-8")
        if line.strip()
    ]

    parser = argparse.ArgumentParser(
        description="build translations for a specific project"
    )

    parser.add_argument(
        "-p",
        "--project",
        type=str,
        choices=projects,
        dest="project",
        help="project name to build",
    )

    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        dest="list_projects",
        help="print all available projects and exit",
    )

    parser.add_argument(
        "-c",
        "--check",
        action="store_true",
        dest="check",
        help="print translation completion percentage for the specified project or for all projects if -p/--project is omitted",
    )

    parser.add_argument(
        "-m",
        "--missing",
        type=str,
        choices=allowed_locales,
        dest="missing",
        help="print uncompleted file names for the specified locale",
    )

    parser.add_argument(
        "-t",
        "--target",
        type=str,
        choices=["android"],
        dest="target",
        help="build target platform (requires -p/--project)",
    )

    args = parser.parse_args()

    if args.list_projects:
        print("available projects:")
        for proj in projects:
            print(f"\t{proj}")
        return

    if args.check:
        if args.project:
            try:
                percents = get_translations_percent_for_project(
                    repository / "projects" / args.project, allowed_locales
                )
            except Exception as e:
                print(e)
                return
            print(f"translation percentages for {args.project}:")
            for locale, pct in percents.items():
                print(f"\t{locale}: {pct:.2f}%")
        else:
            print("translation percentages for all projects:")
            for proj in projects:
                try:
                    percents = get_translations_percent_for_project(
                        repository / "projects" / proj, allowed_locales
                    )
                except Exception as e:
                    print(e)
                    return
                print(f"\t{proj}:")
                for locale, pct in percents.items():
                    print(f"\t\t{locale}: {pct:.2f}%")
        return

    if args.missing:
        if args.project:
            try:
                missing_files = get_missing_files_for_locale(
                    repository / "projects" / args.project, args.missing
                )
            except Exception as e:
                print(e)
                return
            print(f"uncompleted files for {args.missing} in {args.project}:")
            if missing_files:
                for filename in missing_files:
                    print(f"\t{filename}")
            else:
                print("\t(none)")
        else:
            print(f"uncompleted files for {args.missing} in all projects:")
            for proj in projects:
                try:
                    missing_files = get_missing_files_for_locale(
                        repository / "projects" / proj, args.missing
                    )
                except Exception as e:
                    print(e)
                    return
                print(f"\t{proj}:")
                if missing_files:
                    for filename in missing_files:
                        print(f"\t\t{filename}")
                else:
                    print("\t\t(none)")
        return

    if args.target:
        if not args.project:
            print("error: -t/--target requires -p/--project to be specified")
            return

        try:
            output_base = repository / "target" / args.target
            if args.target == "android":
                build_android_translations(
                    repository / "projects" / args.project, output_base, allowed_locales
                )
                print(f"android translations built successfully for {args.project}")
        except Exception as e:
            print(f"error building translations: {e}")
        return

    if not args.project:
        print("you have to select a project")
        return


def is_translation_complete(locale_data: Dict) -> bool:
    v = locale_data.get("v", "")
    if isinstance(v, str) and v.strip():
        return True

    one = locale_data.get("one", "")
    other = locale_data.get("other", "")
    if (
        isinstance(one, str)
        and one.strip()
        and isinstance(other, str)
        and other.strip()
    ):
        return True

    return False


def get_translations_percent_for_project(
    project: Path, allowed_locales: List[str]
) -> Dict[str, float]:
    files = [f for f in project.iterdir() if f.is_file() and f.suffix == ".toml"]
    if not files:
        return {locale: 0.0 for locale in allowed_locales}

    counts = {locale: 0.0 for locale in allowed_locales}
    errors = []

    for file in files:
        try:
            with file.open("rb") as fp:
                obj = tomllib.load(fp)
        except Exception as e:
            errors.append(f"{file.name}: {e}")
            continue

        for locale in allowed_locales:
            locale_data = obj.get(locale, {})
            if is_translation_complete(locale_data):
                counts[locale] += 1

    if errors:
        raise ValueError("\n".join(errors))

    total = len(files)
    return {
        locale: round((counts[locale] / total) * 100.0, 2) for locale in allowed_locales
    }


def get_missing_files_for_locale(project: Path, locale: str) -> List[str]:
    files = [f for f in project.iterdir() if f.is_file() and f.suffix == ".toml"]

    missing = []
    errors = []

    for file in files:
        try:
            with file.open("rb") as fp:
                obj = tomllib.load(fp)
        except Exception as e:
            errors.append(f"{file.name}: {e}")
            continue

        locale_data = obj.get(locale, {})
        if not is_translation_complete(locale_data):
            missing.append(file.name)

    if errors:
        raise ValueError("\n".join(errors))

    return sorted(missing)


def locale_to_android_resource_dir(locale: str) -> str:
    if locale == "en_US":
        return "values"

    parts = locale.split("_")
    if len(parts) == 2:
        lang, region = parts
        return f"values-{lang}-r{region}"
    else:
        return f"values-{locale}"


def escape_android_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\")  # \
    escaped = escaped.replace("'", "\\'")  # '
    escaped = escaped.replace('"', '\\"')  # "
    escaped = escaped.replace("\n", "\\n")  # new line
    escaped = escaped.replace("\t", "\\t")  # tab
    escaped = escaped.replace("@", "\\@")  # @
    escaped = escaped.replace("?", "\\?")  # ?
    return escaped


def build_android_translations(
    project_path: Path, output_path: Path, allowed_locales: List[str]
):
    files = [f for f in project_path.iterdir() if f.is_file() and f.suffix == ".toml"]

    if not files:
        raise ValueError(f"no .toml files found in {project_path}")

    translations = {
        locale: {"strings": {}, "plurals": {}} for locale in allowed_locales
    }
    errors = []

    for file in files:
        try:
            with file.open("rb") as fp:
                obj = tomllib.load(fp)
        except Exception as e:
            errors.append(f"{file.name}: {e}")
            continue

        key = file.stem

        for locale in allowed_locales:
            locale_data = obj.get(locale, {})

            v = locale_data.get("v", "")
            if isinstance(v, str) and v.strip():
                translations[locale]["strings"][key] = v.strip()

            elif "one" in locale_data or "other" in locale_data:
                one = locale_data.get("one", "")
                other = locale_data.get("other", "")
                few = locale_data.get("few", "")
                many = locale_data.get("many", "")

                if (
                    isinstance(one, str)
                    and one.strip()
                    and isinstance(other, str)
                    and other.strip()
                ):
                    plural_data = {"one": one.strip(), "other": other.strip()}
                    if isinstance(few, str) and few.strip():
                        plural_data["few"] = few.strip()
                    if isinstance(many, str) and many.strip():
                        plural_data["many"] = many.strip()

                    translations[locale]["plurals"][key] = plural_data
                else:
                    # en_US fallback
                    if locale != "en_US":
                        en_data = obj.get("en_US", {})
                        en_v = en_data.get("v", "")
                        if isinstance(en_v, str) and en_v.strip():
                            translations[locale]["strings"][key] = en_v.strip()
                        elif "one" in en_data and "other" in en_data:
                            en_one = en_data.get("one", "")
                            en_other = en_data.get("other", "")
                            en_few = en_data.get("few", "")
                            en_many = en_data.get("many", "")

                            if (
                                isinstance(en_one, str)
                                and en_one.strip()
                                and isinstance(en_other, str)
                                and en_other.strip()
                            ):
                                plural_data = {
                                    "one": en_one.strip(),
                                    "other": en_other.strip(),
                                }
                                if isinstance(en_few, str) and en_few.strip():
                                    plural_data["few"] = en_few.strip()
                                if isinstance(en_many, str) and en_many.strip():
                                    plural_data["many"] = en_many.strip()

                                translations[locale]["plurals"][key] = plural_data
            # en_US fallback
            elif locale != "en_US":
                en_data = obj.get("en_US", {})
                en_v = en_data.get("v", "")
                if isinstance(en_v, str) and en_v.strip():
                    translations[locale]["strings"][key] = en_v.strip()
                elif "one" in en_data and "other" in en_data:
                    en_one = en_data.get("one", "")
                    en_other = en_data.get("other", "")
                    en_few = en_data.get("few", "")
                    en_many = en_data.get("many", "")

                    if (
                        isinstance(en_one, str)
                        and en_one.strip()
                        and isinstance(en_other, str)
                        and en_other.strip()
                    ):
                        plural_data = {"one": en_one.strip(), "other": en_other.strip()}
                        if isinstance(en_few, str) and en_few.strip():
                            plural_data["few"] = en_few.strip()
                        if isinstance(en_many, str) and en_many.strip():
                            plural_data["many"] = en_many.strip()

                        translations[locale]["plurals"][key] = plural_data

    if errors:
        raise ValueError("\n".join(errors))

    for locale, data in translations.items():
        strings = data["strings"]
        plurals = data["plurals"]

        if not strings and not plurals:
            continue

        res_dir = output_path / locale_to_android_resource_dir(locale)
        res_dir.mkdir(parents=True, exist_ok=True)

        root = ET.Element("resources")

        for key, value in sorted(strings.items()):
            string_elem = ET.SubElement(root, "string", name=key)
            string_elem.text = escape_android_string(value)

        for key, plural_data in sorted(plurals.items()):
            plurals_elem = ET.SubElement(root, "plurals", name=key)

            for quantity in ["one", "few", "many", "other"]:
                if quantity in plural_data:
                    item_elem = ET.SubElement(plurals_elem, "item", quantity=quantity)
                    item_elem.text = escape_android_string(plural_data[quantity])

        xml_str = minidom.parseString(ET.tostring(root, encoding="utf-8")).toprettyxml(
            indent="    ", encoding="utf-8"
        )

        strings_xml = res_dir / "strings.xml"
        with strings_xml.open("wb") as f:
            f.write(xml_str)


if __name__ == "__main__":
    main()
