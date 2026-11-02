"""Answers the open questions for the Windows port. Prints a report; changes nothing."""
import ctypes
import glob
import os
import sys
import time

print("python", sys.version.split()[0], sys.platform)
try:
    import gi
    for namespace, version in (("Gtk", "4.0"), ("Adw", "1"), ("Gst", "1.0"), ("GstApp", "1.0")):
        gi.require_version(namespace, version)
    from gi.repository import Adw, Gst, Gtk
    print("PASS ui: gtk", Gtk.get_major_version(), Gtk.get_minor_version(), "adw", Adw.get_major_version(), Adw.get_minor_version())
except Exception as e:
    print("FAIL ui:", e)
    sys.exit(1)

Gst.init(None)
print("gstreamer", Gst.version_string())
elements = ("videotestsrc", "glupload", "glcolorconvert", "glshader", "gldownload", "jpegdec", "textoverlay", "videoflip",
            "mfvideosrc", "ksvideosrc", "wasapisrc", "wasapisink", "wasapi2src", "wasapi2sink", "appsrc", "appsink",
            "audiotestsrc", "audiocheblimit", "audioecho", "audioamplify", "freeverb", "pngenc")
missing = [e for e in elements if not Gst.ElementFactory.find(e)]
print("PASS elements" if not missing else f"MISSING elements: {', '.join(missing)}")

dlls = sorted(glob.glob(os.path.join(os.path.dirname(sys.executable), "librubberband*.dll")))
print("rubberband dlls:", [os.path.basename(d) for d in dlls])
for dll in dlls:
    try:
        lib = ctypes.CDLL(dll)
        print("PASS rubberband:", os.path.basename(dll), "formant control", hasattr(lib, "rubberband_set_formant_scale"))
        break
    except OSError as e:
        print("FAIL rubberband load:", dll, e)

FRAGMENT = """#version 110
varying vec2 v_texcoord; uniform sampler2D tex;
void main() { vec3 c = texture2D(tex, v_texcoord).rgb; gl_FragColor = vec4(0.0, dot(c, vec3(0.3, 0.6, 0.1)), 0.0, 1.0); }
"""


def run(tag, chain, fragment=None):
    try:
        p = Gst.parse_launch(f"videotestsrc num-buffers=10 ! video/x-raw,format=RGBA,width=320,height=180 ! {chain} "
                             "! video/x-raw,format=RGBA ! appsink name=a sync=false")
    except Exception as e:
        print(f"FAIL {tag}: {e}")
        return
    if fragment:
        p.get_by_name("s").set_property("fragment", fragment)
    a = p.get_by_name("a")
    p.set_state(Gst.State.PLAYING)
    last = None
    t = time.time()
    while time.time() - t < 10:
        s = a.emit("try-pull-sample", Gst.SECOND)
        if s is None:
            break
        last = s
    m = p.get_bus().pop_filtered(Gst.MessageType.ERROR)
    p.set_state(Gst.State.NULL)
    if not last:
        print(f"FAIL {tag}: no frame", m.parse_error()[0].message if m else "")
        return
    b = last.get_buffer()
    ok, info = b.map(Gst.MapFlags.READ)
    d = bytes(info.data)
    b.unmap(info)
    rgb = [round(sum(d[i::4]) / (len(d) / 4)) for i in range(3)]
    print(f"{'PASS' if sum(rgb) > 30 else 'FAIL'} {tag}: mean RGB {rgb}", m.parse_error()[0].message if m else "")


run("gl passthrough", "glupload ! gldownload")
run("gl shader (expect green only)", "glupload ! glcolorconvert ! glshader name=s ! gldownload", FRAGMENT)

try:
    import pyvirtualcam
    print("PASS pyvirtualcam import", pyvirtualcam.__version__)
except Exception as e:
    print("FAIL pyvirtualcam:", e)
