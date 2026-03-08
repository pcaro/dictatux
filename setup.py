from setuptools import setup

# Las traducciones se compilan manualmente con ./compile_translations.sh (Docker)
# o se distribuyen como archivos .qm pre-compilados

data_files = [
    (
        "share/icons/hicolor/scalable/apps/",
        ["icons/dictatux/scalable/micro.svg", "icons/dictatux/scalable/nomicro.svg"],
    ),
    ("share/doc/dictatux/", ["README.md", "LICENSE"]),
    ("share/applications/", ["dictatux.desktop"]),
]

setup(
    data_files=data_files,
    package_data={"": ["translations/*.qm"]},
)
