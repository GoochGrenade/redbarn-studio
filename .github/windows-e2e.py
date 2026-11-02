"""Windows end-to-end check for GitHub's build server, which has no webcam or mic.

A test pattern and a test tone go through the app's own camera and voice pipelines into OBS Virtual Camera
and VB-CABLE, then are read back where Discord would read them. Exits non-zero if a check fails.
"""
import importlib.machinery
import importlib.util
import struct
import sys
import time

loader = importlib.machinery.SourceFileLoader("redbarn", "redbarn-studio")
spec = importlib.util.spec_from_loader("redbarn", loader)
app = importlib.util.module_from_spec(spec)
loader.exec_module(app)
Gst = app.Gst
Gst.init(None)
for device_class in ("Video/Source", "Audio/Source", "Audio/Sink"):
    monitor = Gst.DeviceMonitor()
    monitor.add_filter(device_class, None)
    monitor.start()
    print(device_class, [d.get_display_name() for d in monitor.get_devices()])
    monitor.stop()
app.report()
failures = []


def check(ok, what):
    print(f"{'PASS' if ok else 'FAIL'} {what}")
    if not ok:
        failures.append(what)


def read(pipeline_text, seconds=1.0):
    """Start a reader pipeline ending in appsink name=a, and return its newest buffer's bytes (or None)."""
    reader = Gst.parse_launch(pipeline_text)
    sink = reader.get_by_name("a")
    reader.set_state(Gst.State.PLAYING)
    data = None
    end = time.time() + seconds + 3
    while time.time() < end:
        sample = sink.emit("try-pull-sample", Gst.SECOND // 2)
        if sample:
            buffer = sample.get_buffer()
            data = buffer.extract_dup(0, buffer.get_size())
            if time.time() > end - 3:
                break
    message = reader.get_bus().pop_filtered(Gst.MessageType.ERROR)
    reader.set_state(Gst.State.NULL)
    if message:
        print("   reader error:", message.parse_error()[0].message)
    return data


# --- Camera: test pattern -> looks -> OBS Virtual Camera
app.WEBCAM_SOURCE = "videotestsrc name=cam is-live=true pattern=smpte75 ! video/x-raw,width=1280,height=720,framerate=30/1"
try:
    camera = app.build_camera_pipeline(None, "obs")
except RuntimeError as e:
    camera = None
    check(False, f"open OBS Virtual Camera: {e}")
if camera:
    sent = [0]
    camera.get_by_name("out").get_static_pad("sink").add_probe(
        Gst.PadProbeType.BUFFER, lambda *_: (sent.__setitem__(0, sent[0] + 1), Gst.PadProbeReturn.OK)[1])
    app.set_look(camera.get_by_name("fx"), "Night Vision")
    camera.set_state(Gst.State.PLAYING)
    time.sleep(4)
    message = camera.get_bus().pop_filtered(Gst.MessageType.ERROR)
    check(message is None, "camera pipeline runs" + (f": {message.parse_error()[0].message}" if message else ""))
    check(sent[0] > 30, f"frames sent to OBS Virtual Camera in 4s: {sent[0]}")
    if Gst.ElementFactory.find("dshowvideosrc"):
        frame = read('dshowvideosrc device-name="OBS Virtual Camera" ! videoconvert ! video/x-raw,format=RGBA ! '
                     "appsink name=a sync=false drop=true max-buffers=1")
        if frame:
            rgb = [sum(frame[i::4 * 97]) / (len(frame) / (4 * 97)) for i in range(3)]
            check(rgb[1] > 2 * max(rgb[0], rgb[2]), f"OBS Virtual Camera shows Night Vision (green): RGB {[round(v) for v in rgb]}")
        else:
            check(False, "read frames back from OBS Virtual Camera")
    else:
        print("SKIP reading OBS Virtual Camera back: no DirectShow source in this GStreamer")
    camera.set_state(Gst.State.NULL)
    camera.virtual_camera.close()

# --- Voice: test tone -> Deep -> VB-CABLE
app.MIC_SOURCE = "audiotestsrc name=mic is-live=true freq=440 volume=0.4 samplesperbuffer=480"
_, output = app.start_virtual_mic()
check(output is not None, "VB-CABLE playback side found")
cable_out = app.windows_device("Audio/Source", "device", "CABLE Output")
check(cable_out is not None, "VB-CABLE Output found")
if output and cable_out:
    voice = app.build_voice_pipeline(None, output)
    app.set_voice(voice, "Deep")
    voice.set_state(Gst.State.PLAYING)
    time.sleep(1.5)
    reader_text = ("wasapi2src name=src low-latency=true ! audioconvert ! audio/x-raw,format=F32LE,channels=1,rate=48000 "
                   "! appsink name=a sync=false max-buffers=100 drop=false")
    reader = Gst.parse_launch(reader_text)
    reader.get_by_name("src").set_property("device", cable_out)
    sink = reader.get_by_name("a")
    reader.set_state(Gst.State.PLAYING)
    samples = []
    end = time.time() + 4
    while time.time() < end and len(samples) < 48000:
        sample = sink.emit("try-pull-sample", Gst.SECOND // 2)
        if sample:
            buffer = sample.get_buffer()
            data = buffer.extract_dup(0, buffer.get_size())
            samples += struct.unpack(f"<{len(data) // 4}f", data)
    reader.set_state(Gst.State.NULL)
    tail = samples[len(samples) // 2:]
    frequency = app.tone_frequency(tail) if tail else 0
    level = app.peak(tail) if tail else 0
    check(abs(frequency - 330) < 15 and level > 0.05,
          f"CABLE Output carries the Deep voice: {frequency:.0f}Hz (expect 330), peak {level:.2f}")
    message = voice.get_bus().pop_filtered(Gst.MessageType.ERROR)
    check(message is None, "voice pipeline runs" + (f": {message.parse_error()[0].message}" if message else ""))
    voice.set_state(Gst.State.NULL)

print(f"\n{len(failures)} failed" if failures else "\nall end-to-end checks passed")
sys.exit(1 if failures else 0)
