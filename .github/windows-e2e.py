"""Windows end-to-end check for GitHub's build server, which has no webcam or mic.

A test pattern and a test tone go through the app's own camera and voice pipelines into OBS Virtual Camera
and VB-CABLE, then are read back where Discord would read them. Exits non-zero if a check fails.
"""
import importlib.machinery
import importlib.util
import struct
import subprocess
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
    for d in monitor.get_devices():
        props = d.get_properties()
        keys = {k: props.get_value(k) for k in ("device.default", "wasapi2.device.loopback") if props and props.has_field(k)}
        print(f"  {device_class:12} {d.get_display_name()!r} {keys}")
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
    # The first frame waits for the shader to compile, which takes seconds on the server's software OpenGL.
    deadline = time.monotonic() + 30
    while sent[0] == 0 and time.monotonic() < deadline:
        time.sleep(0.2)
    first = sent[0]
    time.sleep(4)
    message = camera.get_bus().pop_filtered(Gst.MessageType.ERROR)
    check(message is None, "camera pipeline runs" + (f": {message.parse_error()[0].message}" if message else ""))
    check(sent[0] - first > 30, f"frames sent to OBS Virtual Camera in 4s after the first: {sent[0] - first}")
    # Read one frame back the way a DirectShow app like Discord would see the camera.
    grab = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "dshow", "-i", "video=OBS Virtual Camera",
                           "-frames:v", "1", "-s", "160x90", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          capture_output=True, timeout=30)
    frame = grab.stdout
    if len(frame) == 160 * 90 * 3:
        rgb = [sum(frame[i::3]) / (160 * 90) for i in range(3)]
        check(rgb[1] > 2 * max(rgb[0], rgb[2]), f"OBS Virtual Camera shows Night Vision (green): RGB {[round(v) for v in rgb]}")
    else:
        check(False, f"read a frame back from OBS Virtual Camera: {grab.stderr.decode(errors='replace')[-300:]}")
    camera.set_state(Gst.State.NULL)
    camera.virtual_camera.close()

# --- Voice: test tone -> Deep -> VB-CABLE
app.MIC_SOURCE = "audiotestsrc name=mic is-live=true freq=440 volume=0.4 samplesperbuffer=480"
_, output = app.start_virtual_mic()
check(output is not None, "VB-CABLE playback side found")
cable_out = app.windows_device("Audio/Source", "device", "CABLE Output")
check(cable_out is not None, "VB-CABLE Output found")
if output and cable_out:
    def listen_cable(seconds=3):
        reader = Gst.parse_launch("wasapi2src name=src low-latency=true ! audioconvert "
                                  "! audio/x-raw,format=F32LE,channels=1,rate=48000 ! appsink name=a sync=false max-buffers=400")
        reader.get_by_name("src").set_property("device", cable_out)
        sink = reader.get_by_name("a")
        reader.set_state(Gst.State.PLAYING)
        samples = []
        end = time.time() + seconds
        while time.time() < end:
            sample = sink.emit("try-pull-sample", Gst.SECOND // 2)
            if sample:
                buffer = sample.get_buffer()
                data = buffer.extract_dup(0, buffer.get_size())
                samples += struct.unpack(f"<{len(data) // 4}f", data)
        message = reader.get_bus().pop_filtered(Gst.MessageType.ERROR)
        reader.set_state(Gst.State.NULL)
        tail = samples[len(samples) // 2:]
        if message:
            print("   reader error:", message.parse_error()[0].message)
        return len(samples), (app.tone_frequency(tail) if tail else 0), (app.peak(tail) if tail else 0)

    # Baselines without the app: a plain tone straight into VB-CABLE, through each Windows audio option.
    for sink_text, source_text in (("wasapi2sink name=out low-latency=true", "wasapi2src name=src low-latency=true"),
                                   ("wasapi2sink name=out", "wasapi2src name=src"),
                                   ("wasapisink name=out", "wasapisrc name=src")):
        plain = Gst.parse_launch(f"audiotestsrc is-live=true freq=440 volume=0.4 ! audioconvert ! {sink_text}")
        out_device = output if "wasapi2" in sink_text else app.windows_device("Audio/Sink", "device", app.CABLE_INPUT)
        plain.get_by_name("out").set_property("device", out_device)
        state = plain.set_state(Gst.State.PLAYING)
        time.sleep(1)
        reader = Gst.parse_launch(f"{source_text} ! audioconvert ! audio/x-raw,format=F32LE,channels=1,rate=48000 "
                                  "! appsink name=a sync=false max-buffers=400")
        reader.get_by_name("src").set_property("device", cable_out if "wasapi2" in source_text
                                               else app.windows_device("Audio/Source", "device", "CABLE Output"))
        sink = reader.get_by_name("a")
        reader.set_state(Gst.State.PLAYING)
        samples = []
        end = time.time() + 2.5
        while time.time() < end:
            sample = sink.emit("try-pull-sample", Gst.SECOND // 2)
            if sample:
                data = sample.get_buffer().extract_dup(0, sample.get_buffer().get_size())
                samples += struct.unpack(f"<{len(data) // 4}f", data)
        errors = [m.parse_error()[0].message for m in (plain.get_bus().pop_filtered(Gst.MessageType.ERROR),
                                                        reader.get_bus().pop_filtered(Gst.MessageType.ERROR)) if m]
        tail = samples[len(samples) // 2:]
        print(f"   plain tone, {sink_text.split()[0]} {'low-latency' if 'low' in sink_text else ''}: start {state.value_nick}, "
              f"{len(samples)} samples, {app.tone_frequency(tail) if tail else 0:.0f}Hz, peak {app.peak(tail) if tail else 0:.2f} {errors}")
        reader.set_state(Gst.State.NULL)
        plain.set_state(Gst.State.NULL)

    voice = app.build_voice_pipeline(None, output)
    written = [0]
    voice.get_by_name("voice_out").get_static_pad("sink").add_probe(
        Gst.PadProbeType.BUFFER, lambda *_: (written.__setitem__(0, written[0] + 1), Gst.PadProbeReturn.OK)[1])
    app.set_voice(voice, "Deep")
    voice.set_state(Gst.State.PLAYING)
    time.sleep(1.5)
    count, frequency, level = listen_cable()
    print(f"   buffers the app wrote to VB-CABLE: {written[0]}; read back {count} samples")
    print("   voice pipeline state:", [s.value_nick if hasattr(s, "value_nick") else s for s in voice.get_state(0)[:3]],
          "| sink caps:", voice.get_by_name("voice_out").get_static_pad("sink").get_current_caps())
    bus = voice.get_bus()
    while (m := bus.pop_filtered(Gst.MessageType.WARNING | Gst.MessageType.ERROR)):
        print("   voice bus:", m.src.get_name(), (m.parse_warning() if m.type == Gst.MessageType.WARNING else m.parse_error())[0].message)
    check(abs(frequency - 330) < 15 and level > 0.05,
          f"CABLE Output carries the Deep voice: {frequency:.0f}Hz (expect 330), peak {level:.2f}")
    message = voice.get_bus().pop_filtered(Gst.MessageType.ERROR)
    check(message is None, "voice pipeline runs" + (f": {message.parse_error()[0].message}" if message else ""))
    voice.set_state(Gst.State.NULL)

print(f"\n{len(failures)} failed" if failures else "\nall end-to-end checks passed")
sys.exit(1 if failures else 0)
