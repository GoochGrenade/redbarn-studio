# Redbarn Studio

Cinematic camera looks, voice filters and a soundboard for Discord and other apps. Pick a look and a voice, and your apps see a filtered camera and mic like any other device.

**15 looks:** Clean, Night Vision, Grainy Film, Hi-Def, 2008 Webcam, VHS, Noir, CCTV, Camcorder, Thermal, Silent Film, Blockbuster, Red Barn, Warband and Old Quest. CCTV, Night Vision and Camcorder add a blinking record dot and a date stamp.

**15 voices:** Normal, Deep, Chipmunk, Child, Female, Male, Robot, Walkie-Talkie, Cave, Demon, Alien, Ghost, Ghostface, Orc Warlord and Adventurer.

**Soundboard:** six original sounds (Air Horn, Ba-Dum-Tss, Sad Trombone, Buzzer, Ding and Crickets), plus any MP3, WAV or OGG clips you add with the **+** button or by dragging them onto the soundboard. Search finds a sound quickly, and right-clicking one of your own clips removes it. Sounds broadcast through the mic, so everyone on the call hears them. Every clip is matched to about the loudness of a voice, so quiet and loud clips come out alike. **Output Volume** sets how loud they are for others, and **Monitor Volume** sets how loud they are for you. Redbarn Studio doesn't include game or meme sounds, because they belong to their owners. You can download clips yourself, for example from [myinstants.com](https://www.myinstants.com), and add them.

The **Microphone** menu follows your computer's default mic, so plugging in a headset switches to it, or you can pick a mic. You can also hear your own filtered voice with **Voice Playback**, mirror the overlay text, flip the camera and switch between dark and light mode. Redbarn Studio remembers your settings, and **Setup & Help** in the menu (or F1) checks your computer and shows how to fix anything that's missing.

## Linux

Needs PipeWire, a webcam and a microphone.

1. **[Download the `redbarn-studio` file](https://github.com/GoochGrenade/redbarn-studio/releases/latest/download/redbarn-studio)** (130 KB).
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
| `redbarn-studio --check` | Shows what's installed and what's missing (also in the app, under **Setup & Help**) |
| `redbarn-studio --self-test` | Checks every look and voice on test signals, without your webcam or mic |
| `redbarn-studio --uninstall` | Removes it from your app menu |

## Windows

**[Download the Redbarn Studio installer for Windows](https://github.com/GoochGrenade/redbarn-studio/releases/latest/download/Redbarn-Studio-Setup.exe)** (114 MB, Windows 10 or 11, 64-bit)

1. Run **Redbarn-Studio-Setup.exe**. If Windows warns that it's from an unknown publisher, click **More info**, then **Run anyway**.
2. Leave **Install the VB-CABLE virtual mic** ticked. The installer downloads VB-CABLE from [vb-audio.com](https://vb-audio.com/Cable/) and opens its setup: click **Install Driver**. VB-CABLE is donationware by VB-Audio.
3. Restart Windows when the installer asks.
4. Open Redbarn Studio from the Start menu. In Discord or any other app, choose **OBS Virtual Camera** as the camera and **CABLE Output** as the mic. Keep Redbarn Studio open while you use them.

The installer includes the virtual camera, so you don't need OBS Studio. If you already have OBS Studio, its virtual camera is used instead.

If something's wrong, open **Setup & Help** from the menu (or press F1) to see what's missing, with download links. See the [release notes](https://github.com/GoochGrenade/redbarn-studio/releases/latest) for more help.

## Tips

- Use headphones with **Voice Playback**, or your mic will pick up its own output.
- If people on a call see the overlay text backwards, turn off **Mirror Overlay Text**. Discord mirrors your own view of your camera, so the text can look backwards only to you.
- If sounds get cut off or a voice sounds wrong in Discord, set **Noise Suppression** to **None** or **Standard** under **Settings > Voice & Video**. Krisp is built to remove anything that isn't speech, sound effects included, and no app that sends sounds through a mic can get around that.

## Licence

Redbarn Studio is free software, released under the GNU General Public License version 3 or later. See [LICENSE](LICENSE).

It's built on Rubber Band (GPL), GStreamer, GTK and libadwaita (LGPL).

© 2026 Redbarn Christian Co.
