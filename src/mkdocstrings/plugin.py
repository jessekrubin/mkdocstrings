"""Plugin module docstring."""

from markdown import Markdown
from mkdocs.config.config_options import Type as MkType
from mkdocs.plugins import BasePlugin

from .documenter import Documenter

# TODO: option to change initial heading level per autodoc instruction
# TODO: add a way to reference other objects in docstrings
#       build all references in an mkdocs event
#       append/fix all those references in a post action

# TODO: use type annotations
# TODO: get attributes types and signatures parameters types from type annotations or docstring

# TODO: steal code from mkautodoc to create a markdown extension (better to render HTML)

# TODO: parse google-style blocks
#       change to admonitions for simple blocks
#       parse Args, Raises and Returns to get types and messages

# TODO: support more properties:
#       generators, coroutines, awaitable (see inspect.is...), decorators?
#       metaclass, dataclass
#       optional (parameters with default values)

# TODO: pick attributes without docstrings?

# TODO: write tests

# TODO: make sure to recurse correctly (module's modules, class' classes, etc.)
# TODO: discover package's submodules

# TODO: option to void special methods' docstrings
#       when they are equal to the built-in ones (ex: "Return str(self)." for __str__)

# TODO: option not to write root group header if it's the only group
# TODO: option to move __init__ docstring to class docstring

config = {
    "show_top_object_heading": False,
    "show_top_object_full_path": True,
    "group_by_categories": True,
    "show_groups_headings": False,
    "hide_no_doc": True,
    "add_source_details": True,
}


class MkdocstringsPlugin(BasePlugin):
    """The mkdocstrings plugin to use in your mkdocs configuration file."""

    config_scheme = (("global_filters", MkType(list, default=["!^_[^_]", "!^__weakref__$"])),)

    def __init__(self, *args, **kwargs) -> None:
        super(MkdocstringsPlugin, self).__init__()
        self.hide_no_doc = True
        self.documenter = None
        self.objects = {}
        self.pages_with_docstrings = []
        self.references = []

    def on_config(self, config, **kwargs):
        """Initializes a [Documenter][mkdocstrings.documenter.Documenter]."""
        self.documenter = Documenter(self.config["global_filters"])
        return config

    def on_nav(self, nav, **kwargs):
        for page in nav.pages:
            with open(page.file.abs_src_path, 'r') as file:
                markdown = file.read()
            lines = markdown.split("\n")
            in_code_block = False
            for i, line in enumerate(lines):
                if line.startswith("```"):
                    in_code_block = not in_code_block
                elif line.startswith("::: ") and not in_code_block:
                    import_string = line.replace("::: ", "")
                    if import_string not in self.objects:
                        root_object = self.documenter.get_object_documentation(import_string)
                        self.references.append(root_object.render_references(page.abs_url))
                        mapping_value = {
                            "object": root_object,
                            "page": page.abs_url
                        }
                        self.objects[import_string] = mapping_value
                        if import_string != root_object.path:
                            self.objects[root_object.path] = mapping_value
                        if page.abs_url not in self.pages_with_docstrings:
                            self.pages_with_docstrings.append(page.abs_url)
        return nav

    def on_page_markdown(self, markdown, page, **kwargs):
        if page.abs_url not in self.pages_with_docstrings:
            return markdown
        lines = markdown.split("\n")
        modified_lines = lines[::]
        for i, line in enumerate(lines):
            # if line.startswith("<p>::: ") or line.startswith("::: "):
            if line.startswith("::: "):
                import_string = line.replace("::: ", "")
                # import_string = line.replace("::: ", "").replace("<p>", "").replace("</p>", "")
                root_object = self.objects[import_string]["object"]
                heading = 2 if config["show_top_object_heading"] else 1
                new_lines = root_object.render(heading, **config)
                modified_lines[i] = new_lines
        modified_lines.extend(self.references)
        return "\n".join(modified_lines)
