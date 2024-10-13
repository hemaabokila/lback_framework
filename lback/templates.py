from jinja2 import Environment, FileSystemLoader, TemplateNotFound

class TemplateRenderer:
    def __init__(self, templates_dir='templates'):
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def render_template(self, template_name, **context):
        try:
            template = self.env.get_template(template_name)
            return template.render(context)
        except TemplateNotFound:
            return {"status_code": 404, "body": "Template not found"}
        except Exception as e:
            return {"status_code": 500, "body": f"Error rendering template: {str(e)}"}

if __name__ == "__main__":
    renderer = TemplateRenderer('myapp/templates') 
    output = renderer.render_template("admin_dashboard.html", title="Admin Dashboard", user="Admin")
    print(output)
