import sys, os, subprocess

if not os.path.split(sys.executable)[1].lower().startswith("fontforge"):
    subprocess.call(["fontforge", "-script", __file__])
    sys.exit()

import fontforge, zipfile, shutil, datetime

def process(name):
    print(f"Selected font: {name}")
    fontforge.setPrefs("AutoHint", False)
    font = fontforge.open(name)
    glyphs = list(font.glyphs())
    glyphCount = len(glyphs)
    fontName = font.fontname
    if not os.path.exists("output"):
        os.makedirs("output")
    ttfPath = os.path.join("output", f"{fontName}.ttf")
    otfPath = os.path.join("output", f"{fontName}.otf")
    ufoPath = os.path.join("output", f"{fontName}.ufo")
    ufoZipPath = f"{ufoPath}.zip"

    print("Generating UFO...")
    if os.path.exists(ufoPath):
        shutil.rmtree(ufoPath)

    font.generate(ufoPath, flags=("opentype"))

    print("Packing UFO...")
    ufoZip = zipfile.ZipFile(ufoZipPath, "w", compression=zipfile.ZIP_LZMA)
    for root, dirs, files in os.walk(ufoPath):
        for file in files:
            src = os.path.join(root, file)
            ufoZip.write(src, os.path.relpath(src, "output"))

    ufoZip.close()
    print("Cleaning...")
    shutil.rmtree(ufoPath)

    print("Optimizing...")
    beginTime = datetime.datetime.now()
    timeDelta = 0
    showProgress = os.environ.get("BUILD_NO_PROGRESS", "0") != "1"
    for g in range(glyphCount):
        if showProgress:
            currentTime = datetime.datetime.now()
            tmpDelta = int((currentTime - beginTime).microseconds / 1e05)
            if tmpDelta != timeDelta:
                print(f"\r{g / glyphCount * 100 :.1f}% ({g}/{glyphCount})", end="")
                timeDelta = tmpDelta
        try:
            glyphs[g].removeOverlap()
            glyphs[g].correctDirection()
        except Exception as ex:
            if showProgress: print(ex)

    if showProgress: print(f"\r100.0% ({glyphCount}/{glyphCount})")

    print("Generating TTF...")
    font.generate(ttfPath, flags=("opentype", "round", "dummy-dsig"))

    print("Generating OTF...")
    font.generate(otfPath, flags=("opentype", "round", "no-flex", "dummy-dsig"))

    font.close()

if __name__ == '__main__':
    entries = os.scandir(os.path.join(os.getcwd(), "src"))
    for e in entries:
        if e.is_file() and e.name.endswith(".sfd"):
            process(e.path)
    print("Done!")
