# New Love Plus+ English Patch (2026)

> **About this fork.** This is my best attempt at a comprehensive New Love Plus+ translation. It is a fork of [czyrustuazon/NewLovePlusPlusEngPatcher](https://github.com/czyrustuazon/NewLovePlusPlusEngPatcher). Every piece of text the game shows was reviewed against the Japanese by Claude Opus 5.5 and checked in a test emulator. As of **v1.1.0** (CIA title version 10):
>
> - **All dialogue.** Every Rinko, Manaka and Nene script and all 55 shared scripts reviewed and corrected line by line, in all three copies of the scripts the game chooses between (`script`, `NLP_01`, `NLP_02`). A default build has **no Japanese dialogue left**: 509,148 lines, none in Japanese apart from `・` pause dots.
> - **All phone messages.** The 1,822 text messages from the three heroines, plus the word lists that fill their blanks (season, weather, food, ...), reviewed and shipped in every build.
> - **System text.** 25,399 / 25,412 UI strings in English. The 13 left are single kanji that a reading quiz asks you to read.
> - **Menus and pictures.** 1,780 English UI images, including the tutorials, magazine titles, shop signs, the photo contest, Profile labels and the date present picker.
> - **Fixes.** Consistent place names and currency ("Riches"); popups that fit their boxes and lines that fit the 30-column text box; US date order; the quit-without-saving voice checks prompt the Japanese phrase in romaji with its English meaning (speaking the romaji as printed is accepted).
>
> Japanese on purpose: the Love Plus mode voice-hint bubbles are romaji (see [Known issues](#known-issues)), quiz questions quote the Japanese they ask about, the name-entry keyboard keeps its kanji, and the game's logos stay as they are.
>
> It should be a solid, complete, playable experience in its own right. The review hasn't been human-proofread yet, so please report anything that reads wrong. To build it, follow [Quick start](#quick-start-drag-and-drop): every build packs this fork's menus and text locally. For the original project, its contributors and its own releases, see the [original repository](https://github.com/czyrustuazon/NewLovePlusPlusEngPatcher).

One-click English patcher for **New Love Plus+** (New Love Plus Plus) on the Nintendo 3DS. This is the current patch. The 2017 [NLPPATCH](https://github.com/LovePlusProject/NLPPATCH) repo is the old 28% release, not this build.

Project site: [New Love Plus+ English patch](https://newloveplus.loc.moe)

Translation work-in-progress lives elsewhere ([Makein/NLPPGit](https://github.com/Makein/NLPPGit), localization project) and in the **volunteer HTML workbench** (see [Volunteer localization workbench](#volunteer-localization-workbench)). This repo holds **completed** scripts/images, HTML *templates*, and a toolchain that turns an official **CIA or .3ds/.cci** dump into a playable English **CIA**.

**License:** EngPatcher original work is [MIT](LICENSE) for the community. That license covers **only** this project’s own code and assets — not third-party tools, fonts, or vendored trees (see [Credits](#credits) and `LICENSE`).

---

## What it can do

Drop in a **decrypted** dump (`.cia` or `.3ds` / `.cci`) and it will:

1. **Verify** the dump (SHA-1) before touching anything  
2. **Wipe `out/`, `release/`, and `cache/`** completely, then recreate them empty. That deletes the previous CIA, logs, `out/extdata_backup/`, gold bake, TRB overlay, name-input `code.bin`, the vanilla RomFS extract, and the PNG pack cache. The A/B Azahar copies in `ab_test/azahar_instances/` are left in place. `python src/patch_cia.py` on its own does not do this wipe  
3. **Reject encrypted dumps** — decrypt yourself first (GodMode9, Batch CIA 3DS Decryptor, etc.)  
4. **Inject English scripts** — layered by `src/script_inject.py`: reviewed contributor files in `assets/script_contrib/` first (every Nene and Rinko script, mirrored onto `NLP_01` / `NLP_02` by `tools/build_community_packs.py`), then Manaka `t*` + common `p*` from `rebuild_dbin2/`, then the ex-NLPPATCH community stems. Drop asks **Include Gemini Nene, Rinko, and SMS?** Answer **no** (the default): reviewed English already covers every line, and a reviewed file always wins. Yes (`NLPP_INCLUDE_GEMINI_NENE=1`) only lets the unreviewed machine pass in `assets/gemini_heroines/` fill a script or message set with no reviewed file, and none is left.  

5. **English heroine names** — rewrite dialog tokens (`▲高嶺＊＊▲` → `Takane`, etc.) and patch UI name tables in `textresource_resident_jpn.trb` / `img.bin`  
6. **Inject Profile name-input `code.bin`** from `release/name_input_code.bin` when present (romaji keyboard, Called-name list, Message Speed, US date order, AM/PM on the home clock, title-loop guard, My Camera Restore Default, Communication Settings StreetPass). Older single-pane `--patch-code` is still available and is **not** this stack  
7. **Inject gold UI** from `release/bake_img.bin` (PNG pack + menu chrome + English mini-game screens + CESA + day-counter), built locally from this fork. The bake file keeps Japanese phone messages; the reviewed English ones in `assets/sms_contrib/` are spliced into a copy of `img.bin` at CIA time (`patch_cia._apply_sms`).  
8. **Apply TRB overlay** from `release/romfs_overlay/` when present  
9. **Rebuild** a decrypted **CIA** for FBI / Azahar / Citra (even when the input was `.3ds`) at `out/NewLovePlusPlus-EN.cia`. A Luma LayeredFS folder is **not** built (see [LayeredFS does not work on hardware](#layeredfs-does-not-work-on-hardware))
10. **Clean** `out/` to the CIA + `log.txt` (SpotPass Watcher #28 is baked into `code.bin`)
11. **Append a PATCH SUMMARY** to `out/log.txt` (same file as the image-pack report and gold-rebuild summary; `--no-log` / `NLPP_NO_LOG=1` to skip)

| Included assets | Approx. count |
|-----------------|--------------:|
| Finished dialog scripts (XML → `.dbin2`) | 230 XML in `assets/scripts` → 753 `.dbin2` across `NLP_01` / `NLP_02` / `script` |
| Unique EN UI PNG masters (`IMAGE_MAP`) | **1765** in **101 / 101** folders |
| Chrome subset (site “UI textures”) | **564** in **25 / 25** folders |

PNG counts are **audited English masters present** (deduped by stem under `assets/images/`, prefer `.check`; recounted 2026-10-20). Not a percent of every BCLIM in vanilla `img.bin`. Chrome = the 25 folders `tools/export_progress_metrics.py` posts as UI textures. Full mapped pack is what gold bake packs. All 101 `IMAGE_MAP` keys have an asset folder (`intro111` / `intro203` / `intro304` are sparse dumps).

Title ID: `00040000000F4E00`

---

## Why this rebuilds a CIA

Most 3DS mods ship as a Luma LayeredFS folder. You copy the changed files to `sdmc:/luma/titles/<titleid>/`, the stock install or cartridge stays untouched, and a bad mod is removed by deleting the folder. That became the usual path because a lot of games store textures and text as loose RomFS files, a public mod page can host those files without hosting the game, and rebuilding a CIA means unpacking the RomFS, rebuilding its hash tree, and reinstalling through FBI.

This project started from the other problem: images, dialog, and `code.bin` each had their own patch, and nothing required them to be the same game. Copying one of them left English names and script on Japanese menus. Drop CIA injects the gold `img.bin`, the script and TRB overlay, and `name_input_code.bin` together, and it stops if the bake is missing instead of emitting that half-English title. A LayeredFS folder of whichever piece you happened to have would still have been those separate routes.

The English release is also its own installable title, which a loose overlay does not produce.

- **HOME menu, region, and product code live in the CIA.** Vanilla shows ニューラブプラス＋, region Japan, product code `CTR-P-BLPJ`. LayeredFS does not rewrite the SMDH or the NCCH header. The rebuilt CIA sets the English title **New Love Plus+**, a USA region lock by default, and product code `CTR-P-BLPE`. The title ID stays `00040000000F4E00`, so existing saves still match. Other regions: `--cia-region japan|europe|free`.
- **Menus are one archive.** UI chrome sits inside `img.bin` (about 680 MB), so a LayeredFS copy of the English UI is still that whole file. Drop CIA deletes `release/` at the start of every build and packs a new `release/bake_img.bin` before inject.
- **FBI, Azahar, and Citra install a CIA.** A dropped `.3ds` / `.cci` is rebuilt into the same CIA at `out/NewLovePlusPlus-EN.cia`. Install that. Drop CIA no longer writes a Luma LayeredFS folder, because it white-screens on real hardware (see [LayeredFS does not work on hardware](#layeredfs-does-not-work-on-hardware)).

The git repo still does not contain a dump. You bring your own decrypted CIA or `.3ds`. `release/bake_img.bin` and the finished CIA are generated on your machine (or fetched as a bake by collaborators) and are not committed.

---

## Quick start (drag and drop)

These steps build a CIA with everything in this fork.

1. **Get this fork.** `git clone https://github.com/mentalfoundry/NewLovePlusPlusEngPatcher`, or **Code → Download ZIP** on GitHub. Both work.
2. **Decrypt your dump yourself** (see [Required dump](#required-dump)).
3. **Back up your save and extra data** (Checkpoint or JKSM on 3DS; `python tools\restore_azahar_extdata.py backup` on Azahar).
4. Double-click **`Drop CIA or 3DS Here to Patch.bat`** and drop your **decrypted** `.cia` / `.3ds` / `.cci` on the window (or use Browse → Patch, or drag the file onto the `.bat`).
5. Answer its questions:

   | Question | Answer |
   |----------|--------|
   | Have you backed up your New Love Plus+ save and extdata? | **y**, once you have |
   | Continue patching anyway? (only when your dump's SHA-1 is not on the known list) | **y** if it is a decrypted New Love Plus+ dump; the known dumps skip this |
   | Include Gemini Nene, Rinko, and SMS? | **N** (the default). Reviewed English already covers every line |

6. **Wait.** Drop deletes `out/`, `release/` and `cache/` (a previous CIA, log, bake or extra-data backup in them is removed), packs the English menus and text from this fork, then builds the CIA. Expect roughly **40 minutes to 2 hours** depending on hardware (see [Gold bake](#gold-bake-every-drop-cia)).
7. **Check `out/log.txt`.** Its PATCH SUMMARY should show `[OK] CIA title version: 10 (v1.1.0 ...)`, `[OK] Phone messages (SMS): English` and `[OK] UI img.bin (menus / chrome): gold bake + English SMS`.
8. **Install `out/NewLovePlusPlus-EN.cia`** over the existing game with FBI (do not delete the game first, that orphans its extra data), or open it in Azahar / Citra.

For an unattended run, set `NLPP_BACKUP_CONFIRMED=1` and `NLPP_INCLUDE_GEMINI_NENE=0` before starting the bat. The SHA-1 question still appears for a dump that is not on the known list.

**Why nothing is downloaded.** This fork publishes no gold bake, and the upstream one (`czyrustuazon/nlpp-gold-maker`) is built from upstream `main`: it would put the original project's menus and images into your CIA. So Drop always packs the bake from this tree. A ZIP copy (no `.git`) first refreshes its sources from **this fork's** `main` (`mentalfoundry/NewLovePlusPlusEngPatcher`), which resets files you edited there; set `NLPP_SKIP_SOURCE_FETCH=1` to keep them. Set `NLPP_GITHUB_REPO=owner/repo` only to use a bake you published from this fork.

### Sharing a build (skip the cold PNG pack)

`release/bake_img.bin` is **gitignored** (too large for GitHub). Assets under `assets/` **are** in the repo.

This fork publishes no GitHub gold bake (the upstream **nlpp-gold-maker** runner in [`infra/README.md`](infra/README.md) builds from upstream `main`). If you run your own runner from this fork, collaborators can fetch its bake with:

```bash
set NLPP_GITHUB_REPO=your-owner/nlpp-gold-maker
python tools/fetch_release_bake.py --tag gold
```

Manual handoff:

1. Clone / zip this repo (includes `assets/`, scripts, tools).  
2. Also give them your finished **`release/`** pack:
   - `release/bake_img.bin` — English UI bake  
   - `release/romfs_overlay/` — TRB overlay  
   - `release/textresource/` — optional but useful  
3. They supply **their own** matching dump.

Running the drop bat deletes that copied `release/` and packs again from `assets/`. To inject a bake already on disk, run `python src/patch_cia.py` (that command does not wipe `out/` or `release/`).

Do **not** ship the game dump, `cache/`, `out/`, or `*.bak_pre_*` sidecars. CIA patching stays on **Windows**.

### Azahar a/b testing (devs / agents)

Dual isolated Azahar user dirs for LayeredFS experiments (no fighting roaming AppData):

```powershell
.\ab_test\make.ps1 instances
.\ab_test\make.ps1 deploy-a    # default: name-input stack → instance A
.\ab_test\make.ps1 save-nene   # shared Nene title save → A and B
.\ab_test\make.ps1 launch-a
.\ab_test\make.ps1 restore-a
```

Full guide: [`ab_test/README.md`](ab_test/README.md). Paths: an Azahar checkout next to this repo (`..\azahar`) and MSYS2 at `C:\msys64` are found automatically; otherwise copy `ab_test/paths.local.ps1.example` → `ab_test/paths.local.ps1` or set the `NLPP_*` variables listed there. Name-input RE: `docs/technical.md` §17.

### Companion site progress bar

The bars on [newloveplus.loc.moe](https://newloveplus.loc.moe) are the committed file `src/data/progress.json` in the site repo. Recount here with `python tools/export_progress_metrics.py`, then run `node scripts/import-progress.mjs` in the site repo and commit the result. The site does not read a live progress endpoint, and the old admin panel is gone. `src/report_progress.py` and `.\ab_test\make.ps1 progress` still know the old POST; that route is no longer on the site.

Use **564** (chrome) or **1765** (all mapped UI masters) from the table above. `images_ui.ui_png_masters_total` in the export is the chrome subset.

### Gold bake (every Drop CIA)

**Drop CIA wipes `out/`, `release/`, and `cache/` first,** then packs the bake from this tree and re-extracts a full RomFS (`Plus/` included) from the dropped ROM. On this fork nothing is downloaded unless `NLPP_GITHUB_REPO` / `NLPP_GOLD_REPO` names a gold repo. `PATCHER_RELEASE` is **`v1.1.0`** on this fork. `CIA_TITLE_VERSION` is **10**. `NLPP_USE_PACK_CACHE` does not survive that wipe. `set NLPP_SKIP_GOLD_FETCH=1` skips the download and packs locally. `set NLPP_REUSE_BAKE=1` skips the stamp check on a leftover local bake. `rebuild_bake_img.py --skip-pack` does **not** refresh the PNG fingerprint when PNGs changed, and it does not wipe `out/`, `release/`, or `cache/`.

The drop bat then runs:

```bash
python tools/rebuild_bake_img.py --rom path\to\game.cia   # or .3ds / .cci
```

That regenerates bake + TRBs from sources. A cold pack is typically **about 40 minutes to 2 hours**, depending on hardware (historically ~16h sequential zopfli). Empty-block-first + `--pkg-workers` + zopfli undershoot pad; see `docs/technical.md` §12.5.3. The console keeps one bottom line: the overall percent (PNG pack, then each chrome script, then the CIA step), the file in progress, and the elapsed time. Each ``[tag]`` line has its own color.

- Vanilla RomFS is re-extracted from the dropped ROM into `cache/vanilla_from_rom/` (full tree, including `Plus/`). A slim cache is refused.  
- Resume after pack finishes: `python tools/rebuild_bake_img.py --skip-pack` (from **repo root**).  
- Drop CIA refuses `NLPP_WITH_IMAGES=0` (no incomplete patches). For a scripts-only test CIA, run `python src/patch_cia.py --no-images` by hand.

Details / pitfalls: `docs/technical.md` §15.

### Required dump

**Decrypt the dump yourself first.** This patcher does not ship `decrypt.exe`.

Known New Love Plus+ dumps (SHA-1). Encrypted hashes may still match the allowlist but are **rejected** at the crypto gate:

```
a9fbd2e6d790b6cb6194f7820e1a71f597160f2b  # encrypted CIA (decrypt first)
811d2f0f72c2a1437997256f30b18fbb2dea6cda  # decrypted CIA
6af1751f8b4f9d074311f3a7cf2b5d3c5e807cc8
d138d92fd9d522827cb9665bc2c954f1e8ba1f92  # decrypted full .3ds
6428e72eefec31d19282d2c7f0cb5082723a3206  # encrypted trim .3ds (decrypt first)
```

Other decrypted dumps are not on that list. Drop then asks **Continue patching anyway?**; answer **y** for a decrypted New Love Plus+ dump. With `patch_cia.py` directly, use `--expect-sha1 <hash>` to require one specific dump, or `--skip-hash` to bypass (not recommended).

### Requirements

- Windows x64  
- Python 3.10+ (the drop bat finds `python`, `py -3`, or common install folders)  
- `py -3 -m pip install -r requirements.txt` (Pillow, numpy, zopfli, **etcpak**, PyYAML via `dev/requirements.txt` — the drop bat runs this first)  
- A few GB free disk (RomFS rebuild is large)  
- A **decrypted** dump (GodMode9, Batch CIA 3DS Decryptor Redux, etc.)  
- First run verifies vendored `tools/cia/` bins (`3dstool` / `ctrtool` / `makerom` / `seeddb`); downloads only if a bin is missing  
- UI glyph font is bundled: `assets/fonts/MPLUS1p-Regular.ttf` (SIL OFL)  

If you see **Python not found**: install from [python.org](https://www.python.org/downloads/) with **Add python.exe to PATH** checked, open a **new** Command Prompt, and confirm `py -3 --version` works. Turning off Windows “App execution aliases” for `python.exe` only helps after a real install exists.

### Git commit signing (contributors)

PRs into `main` require **verified** commit signatures. Prefer **GPG** (GitHub verifies these reliably). Use the same email as your commits (GitHub noreply is fine).

```bash
# 1) Create a key (interactive). Choose RSA 4096, set email to your GitHub noreply
#    e.g. 12345678+USERNAME@users.noreply.github.com
gpg --full-generate-key

# 2) Copy the KEYID from the sec line (example: rsa4096/ABCDEF1234567890 → ABCDEF1234567890)
gpg --list-secret-keys --keyid-format LONG

# 3) Upload the public key: GitHub → Settings → SSH and GPG keys → New GPG key
gpg --armor --export KEYID

# 4) Tell git to sign with that key (replace KEYID with the real id from step 2)
git config --global gpg.format openpgp
git config --global user.signingkey KEYID
git config --global commit.gpgsign true
git config --global tag.gpgsign true
```

Probe: `git commit --allow-empty -S -m "gpg probe"` then `git log -1 --show-signature` (should show a good signature). Remove the probe with `git reset --hard HEAD~1`.

To re-sign an existing PR branch onto `main` after enabling GPG:

```bash
git fetch origin
git rebase --force-rebase -S origin/main
git push --force-with-lease origin HEAD
```

SSH commit signing is optional and not documented here — GitHub may leave SSH-signed commits **Unverified** (`unknown_key`) even when the Signing key fingerprint matches.

### Outputs

| Path | Description |
|------|-------------|
| `out/NewLovePlusPlus-EN.cia` | Patched **decrypted** CIA — install with FBI, or open in Azahar/Citra |
| `out/log.txt` | One log for the run: image-pack report, gold rebuild, and PATCH SUMMARY |
| `release/bake_img.bin` | Gold UI `img.bin` (preferred by drop-bat / `patch_cia`) |
| `release/romfs_overlay/` | Durable RomFS overlay (TRBs); auto-applied if present |
| `release/textresource/` | Durable TRB / translation work |
| `cache/new_img.bin` | Optional PNG-pack scratch (incomplete vs gold) |
| `cache/vanilla_from_rom/` | Vanilla RomFS extracted from a dropped ROM when needed |

Before that build starts, Drop CIA deletes **`out/`, `release/`, and `cache/` completely** (previous CIA, patch log, `extdata_backup/`, gold bake, overlay, name-input `code.bin`, vanilla RomFS extract, PNG pack cache) and recreates them empty. `ab_test/azahar_instances/` is not part of that wipe. After a successful patch, `out/` is cleaned again to **the CIA + `log.txt`**. Large intermediates (unpacked packages, extracted CXI/RomFS, duplicate `img.bin` copies) are deleted **as soon as each step finishes**, not only at the end. Pass `--keep-work` to `patch_cia.py` to retain scratch from that inject step; it does not skip the Drop CIA wipe. Towano Watcher #28 (SpotPass) ships in `release/name_input_code.bin`; there is nothing to paste.

### LayeredFS does not work on hardware

Install the CIA. A Luma LayeredFS folder is no longer built by Drop CIA.

On a real 3DS, every romfs override white-screens after the CESA warnings (music keeps playing). That was tested on Luma v10.3 and v13 with the baked `img.bin`, with an unmodified vanilla `img.bin`, and with a single script file. A guarded `code.bin` alone boots to the title, and the same files installed as a CIA boot fine, so the patches are not the problem. The cause is not confirmed. The likely one is that the game opens `img.bin` in a way a path-based redirect does not cover.

The crash-guards added for the title scene (null panes, bad name-walk offsets, non-heap texture pointers) came from LayeredFS runs. They ride along in `name_input_code.bin`, which the CIA also uses, and the CIA boots fine.

The full investigation, what was ruled out, and what to try next are in [docs/layeredfs-investigation.md](docs/layeredfs-investigation.md).

LayeredFS still works for emulator tests. Pass `--layeredfs-out <folder>` to `src/patch_cia.py` to write one by hand, then copy it into Azahar/Citra’s `load/mods/`. The A/B workflow in `ab_test/` does this for you.

**A hand-built LayeredFS folder needs this repo’s `code.bin`**

Retail `code.bin` already loads textures. A BCLIM in `romfs/img.bin` is accepted only when its pointer is 128-byte aligned, the `CLIM` header and `imag` block match, and the format byte hits a GPU row (A8, RGBA4444, ETC1A4, and the rest). A valid English texture gets that far on an unpatched executable. Details: [`docs/technical.md` §5.4](docs/technical.md).

Two English graphics are outside that loader, so a `--layeredfs-out` folder also needs `release/name_input_code.bin` copied to `code.bin` beside `romfs/`:

1. **Main Menu Eng Patch badge.** The title layout adds a picture pane retail does not have. When the hub rebuilds, that pane can be a null child, and retail `FindPaneByName` jumps to address 0. The menu aborts before it finishes drawing. The patched executable skips that attach ([`docs/technical.md` §15.7](docs/technical.md)).
2. **CESA thank-you blurb.** Retail draws the companion logo as a 400×400 quad. The English texture is 240×320. The patched executable keeps that real size so the blurb stays on the pane ([`docs/technical.md` §12.7](docs/technical.md)).

Azahar picks up `code.bin` only when it is in the folder. A folder with English `img.bin` and no `code.bin` runs the retail ExeFS: the textures are present, then the hub aborts and the thank-you quad is the wrong size.

Use the `code.bin` from the same bake. It is rebuilt from vanilla during the bake (`deploy_name_input_en.py`), and an older ExeFS can miss one of those two hooks. The same file also carries the romaji name keyboard, Message Speed, and the SpotPass Watcher embed. The CIA gets it the same way: Drop CIA injects it into the ExeFS.

Deploy scripts mirror into Azahar LayeredFS by default when that mod `img.bin` exists (`NLPP_ALSO_AZAHAR=0` to opt out). For iterative testing prefer `ab_test/` instances (`.\ab_test\make.ps1 deploy-a`) over roaming AppData — see [`ab_test/README.md`](ab_test/README.md).

### Known issues

- **Boop / network install:** Installing the patched CIA over the network with Boop does not work. Copy `out/NewLovePlusPlus-EN.cia` to the SD card and install with FBI, or open the CIA in Azahar/Citra.
- **Love Plus mode voice-hint bubbles are not translated:** see below.

#### Voice-hint bubbles (Love Plus mode)

<img src="docs/images/voice-hint-bubbles.png" alt="Voice-hint bubbles around the heroine in Love Plus mode: ヒマだね, 遊ぼう, 好きですか？, あのさ, 選んで, お話しよう" width="369">

When the mic is open in Love Plus mode, bubbles like ヒマだね, 遊ぼう and お話しよう float around her. They tell you what you can say to her. The screenshot shows the unpatched game. The English patch writes each bubble in romaji, so ヒマだね reads "Hima da ne" and お話しよう reads "Ohanashi shiyou". The romaji fits in the bubbles and is easy to read. You can read what to say, but the bubbles aren't translated into English. I have no plans to translate them, so you need some basic Japanese to know what you're saying.

The reason is the voice-to-text engine. Each bubble is tied to a Japanese reading, and that reading is the only thing the game listens for. The bubbles live in `img.bin` package 4073 (`keyword_stringu_*.lmb`). Each one is paired, row for row, with a katakana reading in `keyword_strings_*.lmb`, and the mic matches your speech against that katakana. An English bubble would tell you what she means but not what to say. Accepting English speech would mean changing the recognizer's vocabulary, which is the voice-to-text side of the game.

I might come back to this later. For now I'm focusing on translation and bug fixes.

---

## SpotPass (とわのウォッチャー)

**SpotPass already works in the patched CIA. You don't need to set anything up.** Nintendo's SpotPass servers are gone, so on an unpatched game the cold-boot check finds nothing and shows **“No SpotPass data found.”** The English CIA ships the archived issue, 「とわのウォッチャー」第28号, inside `code.bin`. After a save loads, the game takes that issue through its normal apply path once: Watcher, city voices, and outing/date/meal info. The “No SpotPass data found.” message never appears. Real 3DS and Azahar both work this way, with no extdata paste, no FBI step, and no Azahar build changes. (`src/patch_spotpass_skip.py` + `src/patch_spotpass_embed.py`, [`docs/technical.md` §16.7–§16.8](docs/technical.md).)

SpotPass is **not** the in-game **Communication** menu (Girlfriend Comm / Business Card / Wireless Battle are StreetPass / local wireless). Enoshima is already on the cart (script `t146`, extra data `00000f4e`) and has nothing to do with SpotPass.

Thank you to **[Cetaceaqua](https://github.com/Cetaceaqua/)** for providing the SpotPass dump this comes from (vendored under `tools/spotpass/`).

`tools/build_spotpass_inject.py` still builds a BOSS-shaped `extdata/…/00000321/boss/info.dat` for RE and emulator experiments. The English CIA does not use it. See [`tools/spotpass/README.md`](tools/spotpass/README.md) and [`docs/technical.md` §16](docs/technical.md). [`docs/spotpass-rebuild.md`](docs/spotpass-rebuild.md) covers rebuilding the service so new issues can go out.

---

## Pipeline (what runs under the hood)

```
decrypted .cia  OR  decrypted .3ds/.cci
  → SHA-1 check
  → crypto gate (refuse if still encrypted)
  → extract CXI (ctrtool contents / 3dstool partitions)
  → extract RomFS (3dstool)
  → inject rebuild_dbin2/*.dbin2 into script/bin/{NLP_01,NLP_02,script}/
  → name patches (plain Takane/Rinko/Nene in scripts + resident/img tables)
  → inject gold bake img.bin + romfs_overlay TRBs
  → rebuild RomFS → CXI → CIA (makerom, decrypted)
  → append PATCH SUMMARY to out/log.txt
  → clean out/ (keep the CIA + log.txt)
```

CLI example (cartridge dump → English CIA):

```bash
python src/patch_cia.py --cia "C:\path\to\00040000000F4E00_v00.3ds" --out "out/NewLovePlusPlus-EN.cia"
```

**Heroine names**

- Finished XML under `assets/scripts` uses plain **Takane** / **Rinko** / **Nene** (not `▲高嶺＊＊▲`).  
  Player tokens like `▲主人公＊▲` are unchanged.  
- At patch time, `src/patch_names.py` also rewrites any leftover tokens inside `.dbin2` and patches the resident TRB + `img.bin` name table.  
- Standalone:  
  `python src/patch_names.py --romfs path\to\romfs`  
  `python src/patch_names.py --xml assets/scripts`  
  `python src/patch_names.py --dbin rebuild_dbin2`  
- Skip with `--skip-name-patches`. For LayeredFS without a full UI pack but with the name table: `--name-img`.

**Player name UI (`code.bin`)**

- **Default (gold / Drop CIA):** inject `release/name_input_code.bin` from `deploy_name_input_en.py` — romaji Profile keyboard, Message Speed, title-loop null-pane guard (`docs/technical.md` §17 / §21). Bake always rebuilds it from vanilla.  
- Older opt-in `--patch-code` only rewrites `SetNameCharsToPanes` / clear / backspace so the whole name draws in one pane (max still 8). It is **not** the name-input stack.  
- Standalone (legacy): `python src/patch_code.py` (uses `cache/vanilla_from_rom` or sibling dump) or `python src/patch_code.py path\to\code.bin`  
- LayeredFS installs `code.bin` next to `romfs/` (Azahar/Luma ExeFS overlay).  
- CIA builds unpack/repack ExeFS via `3dstool`.

**Encryption notes**

- Input must already be **decrypted** (`Crypto Key: None`). Encrypted dumps are refused.  
- Output is a **decrypted** CIA — correct for CFW and emulators.  
- True retail NCCH re-encryption is **not** done here; use Decrypt9WIP *CIA Encryptor (NCCH)* on a console if you specifically need that.

**UI bake (gold `img.bin`)**

- Put translated UI PNGs under `assets/images`.  
- **Gold path:** `python tools/rebuild_bake_img.py` → `release/bake_img.bin` (+ `release/name_input_code.bin`)  
  PNG pack + main TRB from `assets/textresource/translations.json` + ordered `deploy_*` chrome (Options / menus / Confirm / softkeys / multiwin / gallery / UI buttons / keyboard tabs / Title / CESA / …) + SMS + day-counter + overlay + Profile name-input `code.bin`.  
- No sibling dump needed: pass `--rom game.cia|.3ds|.cci` (drop-bat does this automatically).  
- Drop-bat **rebuilds the bake locally** on this fork (it publishes none), then patches the CIA. With `NLPP_GITHUB_REPO` set it polls that Release first.  
- Drop-bat / `patch_cia.py` **prefer `release/bake_img.bin`** when present; inject `release/name_input_code.bin` when present.  
- **Cold PNG pack** is CPU-bound exact-zlib (see `docs/technical.md` §12.5.3): empty-block-first + `--pkg-workers` + zopfli empty-block pad. Watch live ``[timer]`` elapsed / heartbeat lines. Expect roughly **40 minutes to 2 hours** depending on hardware (historically ~16h sequential zopfli). Warm `cache/img_pack/` re-packs take minutes, but only for manual `rebuild_bake_img.py` runs: Drop CIA deletes `cache/` first, so its local packs are always cold.  
- Resume deploys only: `python tools/rebuild_bake_img.py --skip-pack`.  
- Optional PNG-only scratch: `cache/new_img.bin` via `pack_images` / `NLPP_REPACK_IMAGES=1` — incomplete vs gold; does not refresh bake.  
- Scripts-only: `python src/patch_cia.py --no-images` (Drop CIA refuses `NLPP_WITH_IMAGES=0`).  
- Parallel convert: `--workers` / `--image-workers`. Fine-tune opt-in: `--fine-tune` / `--image-fine-tune` (very slow).  
- Exact-length zlib for compressed ARCs: `src/exact_zlib.py` (see `docs/technical.md` §12.5 / §15).  
- The drop bat does **not** mutate your RomFS dump in-place.

**Main Menu vs submenus**

| Screen | Package | Notes |
|--------|---------|--------|
| Main Menu **rows** + Eng Patch badge | **5261** `Title.arc` | `deploy_title_engpatch_en.py` (replaces labels-only `deploy_title_main_menu_en.py` in bake) |
| Gallery / Communication / Data Management homes | **5244 / 5241 / 5242** | `deploy_msel_menus_en.py` |
| Gallery girl-select / multiwin headers | **5153** / **5237** | `deploy_gallery_common_en.py` / `deploy_multiwin_headers_en.py` |
| Softkeys Back / Next / Confirm / Quit / Restore Default | **5238** | `deploy_softkey_back_next_en.py` + `deploy_confirm_btn_en.py` + `deploy_softkey_quit_en.py` + `deploy_softkey_defaults_en.py` |
| Options chrome | **5245** | `deploy_msel_options_en.py` |
| In-room Options overlay | **5380** + **5575** | `deploy_myroom_options_en.py` (`optn_tex_*`, Zhoumaru) |
| Password entry window | **5251** `OptionPassword.arc` | `deploy_optionpassword_en.py` (`Pass_Win01`) |
| Password entry header | **5245** | `Password Input` (`Plate_Text03_05`) |
| Boot CESA warning | **90** | `deploy_cesa_en.py` (not auto PNG-pack) |
| Profile name-input (romaji) | ExeFS `code.bin` | `deploy_name_input_en.py` → `release/name_input_code.bin` |
| “Main Menu” title string | **5261** `Title_menu_word` | Render gray EN (do not pack Zhoumaru RGB dump) |

---

## Credits

Thank you to everyone whose work this patcher builds on — translators who lived in XML for years, painters who redrew every softkey, and the people who clicked through every menu so the rest of us didn’t have to. Their materials keep **their own** licenses; the MIT grant in [`LICENSE`](LICENSE) is only for EngPatcher original work.

### EngPatcher contributors

New work on **this** patcher. Not the 2016–17 NLPPATCH / tooling lineage in the tables below.

| Person | Contribution |
|--------|----------------|
| **[Zhoumaru](https://github.com/andiii-k/NLPP-ETT)** | Complete English UI texture translations ([NLPP-ETT](https://github.com/andiii-k/NLPP-ETT)) — the painted masters gold bake packs into `img.bin` |
| **DDMeisterX** | Manaka (`t*`) + everyday / player (`p*`) routes, and the early Rinko/Nene community layer (48 reviewed scripts each; see note below) |
| **[Cetaceaqua](https://github.com/Cetaceaqua/)** | [NLPP Toolchain](https://github.com/Cetaceaqua/) — EngPatcher and [nlpp-texture-tool](https://github.com/czyrustuazon/nlpp-texture-tool) borrow from it to fix packing / BCLIM issues; also SpotPass dump + RGB8/RGBA8 byte order (below) |
| **Dragios** & **D.** | QA testing — the “does this menu still say 決定?” crew |
| **Lieutenant Dan** | Proofreading |
| **Armando Esteban Quito** | Translated Nene's first day at Dixie's (`a000`) and lines in her confession and date scenes (`a002`, `a004`, `a005`) |
| **Dnnz.Cstr** | Translated Rinko's hair and outfit reactions (`k007`) |
| **i need help here...** | Knowledge sharing |
| **( ˘ ᵕ˘(˘ᵕ ˘ )** | Shared save files that unlocked quicker access to post-game context |

**Coverage on this fork (2026-11-20, `tools/export_progress_metrics.py`):** every script with dialogue is English, **522 / 578** files. The other **56** (28 per Nene / Rinko route) are empty retail stubs with no lines, so the fansite bar draws them as their own segment and fills to **100%**. Nene and Rinko are fully reviewed (`assets/script_contrib/`), post-game included, in all three script packs; on 2026-10-23 it was 48 / 174 reviewed per route plus an unreviewed Gemini pass. Phone messages are **1,822 / 1,822**, reviewed (`assets/sms_contrib/`) and shipped by default. Spoken text plus phone messages is **2,344 / 2,400** entries with text, the same 56 stubs making up the rest.

**System text (2026-11-20):** `textresource_jpn.trb` is **25,399 / 25,412 (99.9%)**. The last **13** slots stay Japanese on purpose. They are single kanji a study quiz asks you to read (`胤`, `欧`, `戟`, `原`, `哉`, `諏`, `成`, `替`, `鉄`, `乍`, `蜂`, `憂`, `梨`). An English quiz prompt that quotes a Japanese word keeps that quotation. The player-name token, the middle dot `・`, and the long-vowel mark `ー` are already English, so the counter skips them.

### CIA / RomFS tooling

| Component | Credit |
|-----------|--------|
| `3dstool` / `ctrtool` / `makerom` / `seeddb.bin` | Vendored under `tools/cia/` ([CREDITS](tools/cia/CREDITS.md)); `setup_tools.py` fetches only if missing |
| `ctrtool` / `makerom` | [3DSGuy/Project_CTR](https://github.com/3DSGuy/Project_CTR) (auto-fetched) |
| `seeddb.bin` | [ihaveamac/3DS-rom-tools](https://github.com/ihaveamac/3DS-rom-tools) (auto-fetched) |

### Image packing / UI

| Component | Credit |
|-----------|--------|
| `nlpp-tools` (`ie`, `pe`, `png2bclim`, `png2texi`, …) | **[kiwiz/nlpp-tools](https://github.com/kiwiz/nlpp-tools)** — thank you to **kiwiz** |
| NLPP Toolchain (packing / BCLIM fixes used by EngPatcher + nlpp-texture-tool) | **[Cetaceaqua](https://github.com/Cetaceaqua/)** |
| BCLIM RGB8 / RGBA8 byte order | Thank you to **Cetaceaqua** for the RGB8 and RGBA8 byte order |
| Zhoumaru UI PNG masters (menus, softkeys, headers, …) | **[Zhoumaru / NLPP-ETT](https://github.com/andiii-k/NLPP-ETT)** |
| Name-select screen buttons (OK / Yes / No / Options) | **lolipop221** |
| UI glyph font `MPLUS1p-Regular.ttf` | [M PLUS 1p](https://fonts.google.com/specimen/M+PLUS+1p) / [Coji / M+ FONTS](https://github.com/coz-m/MPLUS_FONTS), SIL OFL 1.1 (`assets/fonts/OFL.txt`) |
| Menu-row font `Arimo[wght].ttf` | [Arimo](https://fonts.google.com/specimen/Arimo) by The Arimo Project Authors, SIL OFL 1.1 (`assets/fonts/Arimo-OFL.txt`) |
| Other fonts under `assets/fonts/` (Pixelify Sans, Press Start 2P, Silkscreen, VT323) | [Google Fonts](https://fonts.google.com/) / respective OFL authors (editor / optional assets) |

### Text / scripts / localization community

| Component | Credit |
|-----------|--------|
| NLPPATCH (historical community patch) | [LovePlusProject/NLPPATCH](https://github.com/LovePlusProject/NLPPATCH) and contributors (see [their credits](https://github.com/LovePlusProject/NLPPATCH/issues/1)) — EngPatcher ships its own `rebuild_dbin2/` + `assets/` |
| Manaka + common + early Rinko dialogue layer | **DDMeisterX** (via the NLPPATCH-era scripts this repo still injects) |
| NLPTextTool (XML ↔ `.dbin2`) | [LovePlusProject/NLPTextTool](https://github.com/LovePlusProject/NLPTextTool) (orig. [gdkchan](https://github.com/gdkchan)) |
| NLPUnpacker | [LovePlusProject/NLPUnpacker](https://github.com/LovePlusProject/NLPUnpacker) (orig. [gdkchan](https://github.com/gdkchan)) |
| Translation asset repo (reference) | [Makein/NLPPGit](https://github.com/Makein/NLPPGit) |
| `Trb2xlsx` / `lookup.txt` (TRB character codebook) | [deaknaew/Trb2xlsx](https://github.com/deaknaew/Trb2xlsx) (vendored under `tools/Trb2xlsx/`) |
| SpotPass / とわのウォッチャー archive (`tools/spotpass/`) | **[Cetaceaqua](https://github.com/Cetaceaqua/)** — thank you for providing the SpotPass dump |

Python packages used at runtime: [Pillow](https://python-pillow.org/), [NumPy](https://numpy.org/), [zopfli](https://github.com/google/zopfli) (`python-zopfli`), [etcpak](https://github.com/K0lb3/etcpak) (ETC1/ETC1A4 for BCLIM), [PyYAML](https://pyyaml.org/) (`yaml` — required by vendored `ie` / nlpp-tools).

---

## Layout

```
Drop CIA or 3DS Here to Patch.bat   ← only end-user entry point
README.md
LICENSE                          MIT for this project's own code
.env.example                     copy to .env (progress-bar token; gitignored .env)
docs/technical.md                RE notes (§15 gold bake, §16 SpotPass, §17 name-input, §18 a/b)
.github/CONTRIBUTING.md          how to pick up a task
.github/CODE_OF_CONDUCT.md
requirements.txt                 Drop CIA installs this first (`py -3 -m pip install -r`)
dev/requirements.txt             runtime pins (Pillow, numpy, zopfli, etcpak, PyYAML)
dev/requirements-dev.txt         pytest
ab_test/
  README.md                  Azahar dual-instance workflow
  make.ps1                   .\ab_test\make.ps1 instances / deploy / launch / restore
  Makefile                   make -C ab_test <target>
  setup_azahar_instances.ps1
  paths.local.ps1.example    → paths.local.ps1 (gitignored)
  azahar_instances/{a,b}/    portable Azahar + saves (survives a CIA wipe)
  patches/azahar-openlinkfile.patch  Azahar OpenLinkFile clone (`build-azahar`)
  saves/nene/                local Nene title save, gitignored (`.\ab_test\make.ps1 save-nene`)
assets/
  scripts/                   finished DBIN2 XML
  images/                    finished UI PNGs (+ editor sources)
  textresource/              translations.json (source for main TRB rebuild)
  fonts/                     MPLUS1p + OFL (UI deploy glyph font)
src/
  patch_cia.py               CIA extract → inject → rebuild (decrypted input only)
  patch_names.py             heroine names (dbin2 / resident TRB / img.bin)
  patch_code.py              single-pane name draw (ExeFS code.bin)
  patch_input_*.py           Profile name-input code.bin patches (§17)
  pack_images.py             PNG → img.bin
  exact_zlib.py              exact-length zlib/zopfli for ARC slots
  extract_vanilla_from_rom.py  vanilla img/TRB from dropped ROM
  darcutil.py / bclimutil.py / image_map.py
  setup_tools.py             verify vendored CIA bins (no decrypt.exe)
  drop_zone.ps1              WinForms drop window
tools/
  rebuild_bake_img.py        regenerate bake + TRBs from sources
  deploy_*.py / restore_*.py / import_azahar_save.py / rebuild_test_cia.py
  build_spotpass_inject.py   optional BOSS info.dat (RE only; Watcher #28 is baked in)
  spotpass/                  archived BOSS dump + README
  nlpp-tools/                vendored img.bin helpers (kiwiz/nlpp-tools)
  cia/                       3dstool / ctrtool / makerom / seeddb (see CREDITS.md)
rebuild_dbin2/               finished English .dbin2 scripts
assets/script_contrib/       reviewed Nene / Rinko / shared dialogue (wins over every other layer)
assets/sms_contrib/          reviewed phone messages + worddic (shipped in every build)
assets/gemini_heroines/      unreviewed Gemini Nene, Rinko, and SMS (Drop asks; answer no; NLPP_INCLUDE_GEMINI_NENE=1)
release/                     gold bake + TRB overlay; Drop CIA deletes this folder before each build (binaries gitignored; docs/technical.md §15.5)
cache/                       PNG scratch + vanilla_from_rom (gitignored; Drop CIA deletes this folder on every from-scratch build)
out/                         Drop CIA deletes this folder before each build; the run then writes the CIA and log.txt (gitignored)
```

Finished `.dbin2` scripts used at patch time live in `rebuild_dbin2/` (generated from `assets/scripts`).

---

## Volunteer localization workbench

A browser workbench so translators can help **without Python**: [czyrustuazon/nlpp-localization-workbench](https://github.com/czyrustuazon/nlpp-localization-workbench) (open `index.html`).

### For volunteers

1. Clone / unzip the workbench folder.
2. Open **`index.html`** → tabs:
   - **Scripts** — dialogue for **Nene `a*`**, **Rinko `k*`**, **Manaka `t*`**, **common `p*`**. The Japanese line is vanilla. The edit box is the text the patcher currently ships (Gemini for Nene/Rinko stems that have a machine pass; Manaka, common, and community English otherwise).
   - **Strings** — **SMS** for all three heroines, plus any TRB line whose exact Japanese is not already in `translations.json`.
3. Edit → **Save progress** → download JSON (`nlpp-contrib-….json` or `nlpp-strings-….json`).
4. Post the JSON in Discord **[#translated-work-to-review](https://discord.com/channels/1536915629787840572/1545180296343715891)**.

Keep nickname tokens (`▲高嶺＊＊▲`), `※`, and `▼` unchanged. Translate `●`: it is the player's "I" (the game shows 俺 or 僕 there), so write I / me / my.

**What’s in each tab (sources):** see **`docs/technical.md` §20.2**. Rebuild the kits with `python tools/sync_workbench.py`. The images tab was removed; UI masters stay in `assets/images/`.

### For maintainers

Script packs (`nlpp-contrib-….json`) apply with:

```bash
python tools/ingest_pack.py path\to\nlpp-contrib.json
python tools/ingest_pack.py path\to\nlpp-contrib.json --apply
```

The first command only reports. `--apply` writes a line only when the volunteer changed it and the repo line is still the Japanese baseline they edited. A script that already has English on that line is listed as a conflict and left as-is. `--force` replaces those conflicts. Nickname tokens (`▲…▲`, including an unclosed `▲`) must keep the same multiset. A drop in `※` or `▼`, or an edit to a circle / punctuation placeholder, rejects the pack and writes nothing. A `●` count change is a warning.

Writes land in `assets/scripts/<stem>.xml` and the matching `rebuild_dbin2/<pack>/<stem>.dbin2`. A stem Gemini already translated is left alone: the review is written under `assets/script_contrib/` instead, and Drop CIA includes that file on its own, ahead of the Gemini machine pass. A stem that exists only as `.dbin2` also gains an XML file. Review the diff, then run Drop CIA. This command does not bake.

Strings packs are not applied by `ingest_pack.py`. The HTML templates under `tools/localization_workbench/` are not built yet. Pack schema and the rest of the rules: **`docs/technical.md` §20**.



---

## Advanced CLI

```bash
# Tool setup
python src/setup_tools.py

# Rebuild gold bake (from repo root)
python tools/rebuild_bake_img.py
python tools/rebuild_bake_img.py --rom path\to\game.cia
python tools/rebuild_bake_img.py --skip-pack          # resume after PNG pack

# Full CIA patch (prefers release/bake_img.bin; same as the .bat)
python src/patch_cia.py --cia "path\to\game.cia"
# Run log: out/log.txt (image pack + gold rebuild + PATCH SUMMARY)
# python src/patch_cia.py --cia "path\to\game.cia" --log D:\patch.txt
# python src/patch_cia.py --cia "path\to\game.cia" --no-log

# Optional PNG-only scratch rebuild (does not refresh gold bake)
python src/patch_cia.py --cia "path\to\game.cia" --repack-images

# Scripts only (skip UI inject)
python src/patch_cia.py --cia "path\to\game.cia" --no-images

# LayeredFS only
python src/patch_cia.py --cia "path\to\game.cia" --layeredfs-only

# UI bank only
python src/pack_images.py
python src/pack_images.py --only title mail

# Skip SHA-1 (not recommended)
python src/patch_cia.py --cia "..." --skip-hash

# Name patches only
python src/patch_names.py --romfs "path\to\romfs"
python src/patch_names.py --dbin rebuild_dbin2

# Volunteer Scripts pack (report only; add --apply to write)
python tools/ingest_pack.py path\to\nlpp-contrib.json

# Name-input LayeredFS (Azahar a/b)
.\ab_test\make.ps1 deploy-a
.\ab_test\make.ps1 launch-a
# or: python tools/deploy_name_input_en.py

# Hub main menu + Eng Patch badge / CESA only (onto release/bake_img.bin)
python tools/deploy_title_engpatch_en.py
python tools/deploy_cesa_en.py

# SpotPass inject (RE / emulator experiments only — Watcher #28 is already in name_input_code.bin)
# python tools/build_spotpass_inject.py
# python tools/build_spotpass_inject.py --azahar

# Patch code.bin only (finds cache/vanilla_from_rom or sibling dump)
python src/patch_code.py

# Asset helpers
python src/patcher.py status
python src/patcher.py validate
python src/patcher.py dialogs --script a002
python src/patcher.py build --clean
```

`patcher.py build` only stages loose `assets/` → `out/patch/`. CIA / LayeredFS work is the drop bat / `src/patch_cia.py`.

---

## What this is not

- A full 100% translation of every line and texture (skipped UI formats stay Japanese).  
- A dump of the game — you must supply your own matching **decrypted** CIA / `.3ds`.  
- A ROM decryptor — decrypt outside this tool, then drop the clear dump.  
- An on-console retail re-encryptor.  
- A gold bake **in this git repo** — `release/bake_img.bin` is gitignored. Drop builds it locally from this fork (or fetches one you published, with `NLPP_GITHUB_REPO`).
