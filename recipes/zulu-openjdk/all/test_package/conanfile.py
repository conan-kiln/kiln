from io import StringIO

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.build import can_run
from conan.tools.layout import basic_layout


class TestPackage(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build(self):
        pass

    def test(self):
        if can_run(self):
            output = StringIO()
            self.run("java --version", output, env="conanrun")
            version_info = output.getvalue()
            self.output.info(f"java --version returned: \n{version_info}")
            if "Zulu" not in version_info:
                raise ConanException("zulu-openjdk test package failed: 'Zulu' not found in java --version output")
