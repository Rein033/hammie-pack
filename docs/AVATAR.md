# Make your own avatar with Claude or ChatGPT

*English · [Español](AVATAR.es.md)*

Hammie is one avatar. With **Kode Avatar** you make your own: a cat, a robot, yourself as a cartoon.
An AI chat (Claude or ChatGPT) draws each animation as a Lottie file. The Kode Avatar app checks
each file against kodeOS's own rules and packs them into a face pack for the Kode Dot.

**Open the app: <https://rein033.github.io/kode-avatar/app/>**

Everything runs in your browser. Nothing is uploaded. Your work is kept in the browser until you
press *Clear all*.

> [!WARNING]
> Face packs are **not tested on an official Kode Dot yet**. The app runs the same checks as
> kodeOS (`kui_pack.c`), but its previews are drawn by your browser, not by the Dot. Try your
> pack from a microSD card first: taking the card out brings Kody back.

## What you need

- A free account at [Claude](https://claude.ai) or [ChatGPT](https://chatgpt.com).
- A Kode Dot with kodeOS that has face packs, and a microSD card (or Wi-Fi, see below).

## The twelve animations

| Card in the app | When the Dot plays it | Canvas | Needed |
|---|---|---|---|
| Wake up | the face appears after the screen turns on | 410 x 334 | yes |
| Idle (loop) | the face, looping all day | 410 x 334 | yes |
| Look at you | someone picks up or taps the Dot | 410 x 334 | |
| On the hour | every full hour | 410 x 334 | |
| Notification | a notification arrives | 410 x 334 | |
| Charging | the USB cable is plugged in | 410 x 334 | |
| Joke 1, Joke 2 | now and then, at random | 410 x 334 | |
| No apps | the launcher with no apps | 410 x 369 | |
| Installing | the card while an app is written | 410 x 160 | |
| Goodbye | the card just before an app starts | 410 x 160 | |
| Loading | the loading screen | 264 x 264 | |

Only **Wake up** and **Idle** are needed. Start with those two, put them on the Dot, and add the
rest later.

## Step by step

1. **Describe your character** in the app. Name its colours, its shape and one prop. For example:
   *"A round grey cat with big green eyes, a pink nose, short whiskers and a small yellow
   headset. Front view, head and upper body, filling most of the screen."*
2. **Start a new chat** in Claude or ChatGPT. Use one chat for the whole avatar, so the AI keeps
   the same drawing.
3. On the **Idle** card, press **Copy prompt** and paste it in the chat. The prompt already holds
   every rule the Dot has (canvas, frame rate, size, which Lottie features to avoid).
4. Copy the AI's whole answer. On the Idle card, press **Paste answer**, paste, and press
   **Use this**. The app finds the JSON in the answer, plays it, and checks it.
   - **✓ OK for the Dot**: go on.
   - **✗ The Dot would refuse this**: the list says why. Paste that line back into the chat:
     *"The checker says: … Please fix it and send the whole JSON again."*
   - Yellow lines are warnings: things the Dot may not draw (images, text, effects).
5. Do the same for **Wake up**, then any other card. Already happy with Idle? **Same as Idle** or
   **Idle, scaled** fills a card with your idle animation, scaled to that card's canvas.
6. Press **Download face pack (.zip)**.

### Tips for good results

- **Claude** with the *Artifacts* feature can show the animation while it works. Ask it:
  *"Show it as a Lottie preview too."* ChatGPT can do the same with its code tool.
- The answer was cut off, or the app says *"Could not read JSON"*? Ask *"Make it shorter: fewer
  shapes and keyframes, and send the whole JSON again."* The Dot allows 96 KB per animation.
- Wrong size? Press **Fit to canvas**. It scales the animation into the right canvas, centred.
- Keep it simple. Big flat shapes, few colours, 2 to 4 seconds per animation. The Dot's screen is
  small, and simple shapes draw fastest.
- Already have a Lottie from [LottieFiles](https://lottiefiles.com) or After Effects
  (Bodymovin)? Use **Upload .json**. Check its licence first.
- Want to tweak Hammie instead? Press **Start from Hammie**, then replace the cards you want.

## Put it on the Dot

### With a microSD card (easiest)

1. Format the card as FAT32.
2. Unzip the download. It holds a folder `kode`.
3. Copy that `kode` folder to the root of the card, so the card holds `/kode/kode.json`.
4. Put the card in the Dot and restart it.

**Back to Kody:** take the card out, or delete the `kode` folder, and restart.

### Over Wi-Fi

1. Put the files from the `kode` folder online, for example in a public GitHub repository of
   your own.
2. Open the Dot's console over USB-C (any serial terminal, see the [README](../README.md#b-over-wi-fi-from-this-repository)).
3. Type, with the link to **your** `kode.json`:

   ```
   function name="assets_update" arg="https://raw.githubusercontent.com/YOU/REPO/main/kode.json"
   ```

**Back to Kody:** `function name="assets_update"` without `arg`.

## Share your avatar

Made something nice? Put it in a public repository with the `kode` files and a GIF, and open an
issue in [kode-avatar](https://github.com/Rein033/kode-avatar/issues) with the link. Please do
not share avatars of real people without their permission, or of characters you do not own.

## For developers

The app is three files, no build step: [`app/index.html`](../app/index.html),
[`app/pack.js`](../app/pack.js) and [`app/i18n.js`](../app/i18n.js) (English and Spanish texts). `pack.js` holds the checks (the limits from kodeOS's
`kui_pack.h`), the same JSON shrinking as `src/dotpack.py`, zlib, SHA-256, the manifest and a ZIP
writer. Its output passes [`tools/packcheck`](../tools/packcheck).
