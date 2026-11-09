"""
Install firmware maintenance and CPU microcode packages.

Vendor-specific microcode is opt-in. fwupd is installed by default when this
feature is enabled; firmware updates themselves are never applied unattended.
"""

from pyinfra import host
from pyinfra.operations import apt

config = host.data.get("workstation", {}).get("hardware", {})
if config.get("enabled", False):
    packages = ["fwupd"]
    vendor = config.get("cpu_vendor")
    if vendor == "intel":
        packages.append("intel-microcode")
    elif vendor == "amd":
        packages.append("amd64-microcode")
    elif vendor not in (None, ""):
        raise ValueError("workstation.hardware.cpu_vendor must be intel, amd or unset")

    apt.packages(
        name="Install workstation firmware and microcode tools",
        packages=packages,
        present=True,
        _sudo=True,
    )
