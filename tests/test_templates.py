from lback.core.templates import TemplateRenderer


def test_template_rendering(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "hello.html"
    template_file.write_text("Hello, {{ name }}!")

    renderer = TemplateRenderer(str(template_dir))
    output = renderer.render("hello.html", {"name": "Lback"})
    assert output == "Hello, Lback!"