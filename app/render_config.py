from pathlib import Path
import yaml


def load_yaml(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def render_template(template_path: str, profile_path: str, output_path: str) -> None:
    template_text = Path(template_path).read_text()
    profile = load_yaml(profile_path)

    rendered = template_text
    for key, value in profile.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(rendered)


if __name__ == "__main__":
    render_template(
        template_path="templates/vllm_pod_template.yaml",
        profile_path="profiles/profile_default.yaml",
        output_path="outputs/runs/rendered_vllm.yaml",
    )
    print("Rendered config written to outputs/runs/rendered_vllm.yaml")
