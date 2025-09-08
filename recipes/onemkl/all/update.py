#!/usr/bin/env python3

import requests
from conan.tools.scm import Version

def get_packages_list():
    raw = requests.get("https://apt.repos.intel.com/oneapi/dists/all/main/binary-amd64/Packages").text
    packages = {}
    for pkg_text in raw.split("\n\n\n"):
        pkg_text = pkg_text.strip()
        if not pkg_text:
            continue
        info = {}
        for l in pkg_text.split("\n"):
            key, value = l.split(": ", 1)
            info[key] = value
        if int(info["Installed-Size"]) == 0:
            continue
        name = info["Package"]
        name = name.split("-" + info["Version"].split(".", 1)[0], 1)[0]
        if name not in packages or Version(info["Version"]) > Version(packages[name]["Version"]):
            packages[name] = info
    return packages

def main():
    packages = get_packages_list()
    version = packages["intel-oneapi-mkl-core"]["Version"]
    urls = []
    for name, info in packages.items():
        if not name.startswith("intel-oneapi-mkl-"):
            continue
        if info["Version"] != version:
            continue
        if "32bit" in name:
            continue
        url = "https://apt.repos.intel.com/oneapi/" + info["Filename"]
        urls.append((url, info["SHA256"]))
    for url, sha256 in sorted(urls):
        print(f'  - url: "{url}"')
        print(f'    sha256: "{sha256}"')

if __name__ == "__main__":
    main()
