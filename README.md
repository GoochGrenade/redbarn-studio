# Redbarn Studio

Cinematic camera looks and voice filters for Discord. Pick a look and a voice, and Discord sees a filtered camera and mic like any other device.

**13 looks:** Clean, Night Vision, Grainy Film, Hi-Def, 2008 Webcam, VHS, Noir, CCTV, Camcorder, Thermal, Silent Film, Blockbuster and Red Barn. CCTV, Night Vision and Camcorder add a blinking record dot and a date stamp.

**13 voices:** Normal, Deep, Chipmunk, Child, Female, Male, Robot, Walkie-Talkie, Cave, Demon, Alien, Ghost and Ghostface.

**Soundboard:** six original sounds (Air Horn, Ba-Dum-Tss, Sad Trombone, Buzzer, Ding and Crickets), plus any MP3, WAV or OGG clips you add with the **+** button. Sounds play through the mic, so Discord hears them, and you hear them too. Redbarn Studio doesn't include game or meme sounds, because they belong to their owners. You can download clips yourself, for example from [myinstants.com](https://www.myinstants.com), and add them.

You can also hear your own filtered voice, mirror the overlay text, flip the camera and switch between dark and light mode.

## Linux

Needs PipeWire, a webcam and a microphone.

1. Download the `redbarn-studio` file.
2. In a terminal, in the folder you saved it to, run:
   ```
   python3 redbarn-studio --install
   ```
   This adds Redbarn Studio to your app menu, then lists anything else it needs, with the commands to install it on Fedora or Ubuntu/Debian.
3. The virtual camera needs the `v4l2loopback` kernel module. If the list says it's missing, install it and load it with:
   ```
   sudo modprobe v4l2loopback exclusive_caps=1 card_label="Redbarn Camera"
   ```
4. Open Redbarn Studio. Then in Discord, under **Settings > Voice & Video**, choose **Redbarn Camera** and **Redbarn Mic**. Keep Redbarn Studio open while you use them.

### Useful commands

| Command | What it does |
|---|---|
| `redbarn-studio --check` | Shows what's installed and what's missing |
| `redbarn-studio --self-test` | Checks every look and voice on test signals, without your webcam or mic |
| `redbarn-studio --uninstall` | Removes it from your app menu |

## Windows

**[Download Redbarn Studio for Windows](https://github.com/GoochGrenade/redbarn-studio/releases/download/v1.0.0-beta/Redbarn-Studio-Windows.zip)** (beta, 175 MB)

This is a beta: it passes all automated tests on a Windows build server, but hasn't been tested on a real Windows PC yet.

1. Install [OBS Studio](https://obsproject.com), which provides the virtual camera. You don't need to open it.
2. Install [VB-CABLE](https://vb-audio.com/Cable/), which provides the virtual mic, then restart Windows.
3. Unzip the download and open **Redbarn Studio.exe**. If Windows warns that it's from an unknown publisher, click **More info**, then **Run anyway**.
4. In Discord, under **Settings > Voice & Video**, choose **OBS Virtual Camera** and **CABLE Output**. Keep Redbarn Studio open while you use them.

If something's wrong, run `"Redbarn Studio.exe" --check` in a terminal in the unzipped folder to see what's missing. See the [release notes](https://github.com/GoochGrenade/redbarn-studio/releases/tag/v1.0.0-beta) for more help.

## Tips

- Use headphones with **Hear my voice**, or your mic will pick up its own output.
- If people on a call see the overlay text backwards, turn off **Mirror overlay text**. Discord mirrors your own view of your camera, so the text can look backwards only to you.
- If a voice sounds wrong in Discord, or the soundboard is cut off, try turning off Discord's noise suppression.

## Licence

Redbarn Studio is free software, released under the GNU General Public License version 3 or later. See [LICENSE](LICENSE).

It's built on Rubber Band (GPL), GStreamer, GTK and libadwaita (LGPL).

© 2026 Redbarn Christian Co.
