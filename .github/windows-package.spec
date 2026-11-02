# PyInstaller recipe for the Windows download, run by .github/workflows/windows.yml on MSYS2 UCRT64.
import os
import sys

root = os.path.join(SPECPATH, "..")
a = Analysis(
    [os.path.join(root, "redbarn_studio.py")],
    hiddenimports=["pyvirtualcam", "numpy"],
    # Loaded with ctypes at runtime, so PyInstaller can't see it; its own DLL dependencies are found from here.
    binaries=[(os.path.join(os.path.dirname(sys.executable), "librubberband-3.dll"), ".")],
    hooksconfig={"gi": {"module-versions": {"Gtk": "4.0", "Gdk": "4.0"}, "icons": ["Adwaita"], "themes": ["Adwaita"]}},
)
# Mesa's software OpenGL is only for the GPU-less build server: shipped, it would override users' graphics drivers.
a.binaries = [b for b in a.binaries if os.path.basename(b[0]).lower() not in ("opengl32.dll", "libgallium_wgl.dll")]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Redbarn Studio", console=False,
          icon=os.path.join(root, "redbarn-studio.ico"))
coll = COLLECT(exe, a.binaries, a.datas, name="Redbarn Studio")
