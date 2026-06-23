# Custom Game Launcher (WPF rebuild)

A native Windows game launcher — scan a folder of games, get crisp exe icons,
launch from a clean auto-wrapping grid. C# / .NET 8 / WPF, **zero NuGet
dependencies** (just the SDK).

## Prerequisites
- **.NET 8 SDK** (or newer): https://dotnet.microsoft.com/download
  (the `OpenFolderDialog` used here needs .NET 8+)
- Windows 10/11

## Build & run
From this folder:

```
dotnet run
```

or open `CustomGameLauncher.csproj` in Visual Studio 2022 (17.8+) and press F5.

To produce a fast-launching standalone .exe (no .NET install needed on the target):

```
dotnet publish -c Release -r win-x64 --self-contained -p:PublishSingleFile=true -p:PublishReadyToRun=true
```

(WPF doesn't support NativeAOT; ReadyToRun + single-file is the equivalent fast path.)

## What it does
- **Add Folder** → pick a folder; it recursively scans for game `.exe`s
  (skipping uninstallers / redistributables / crash handlers — tune the list in
  `Services/GameScanner.cs`).
- **Crisp icons**: extracts the real 256px embedded icon natively, scales *down*
  (never upscaled/stretched — `Image Stretch="Uniform"`), and **disk-caches** it
  so it's instant next time. No icon → a letter tile, never a white box.
- **Auto-wrapping grid** (`WrapPanel`) — tiles reflow to fit the window; no manual
  column math, so no "4-in-a-row on refresh" bug.
- **Data-bound** (`ObservableCollection` → grid): add/remove/refresh updates the
  view automatically — no hand-managed widgets, so duplicates can't happen.
- **Search** box filters live; click a tile to launch.
- Games persist to `%LOCALAPPDATA%\CustomGameLauncher\games.json`; icon cache in
  `…\iconcache\`.

## Project layout
```
CustomGameLauncher.csproj
App.xaml / App.xaml.cs          # dark theme + control styles
MainWindow.xaml / .cs           # toolbar + grid
Models/Game.cs                  # the bound data item
ViewModels/MainViewModel.cs     # collection, commands, icon loading
Services/GameScanner.cs         # folder scan + junk filter
Services/IconExtractor.cs       # native 256px icon + cache + fallback
Services/GameStore.cs           # JSON persistence
RelayCommand.cs                 # minimal ICommand
```

## Next steps (foundations are here for these)
- Store **source adapters**: Steam (`libraryfolders.vdf` + `appmanifest_*.acf`),
  Epic (`%ProgramData%\Epic\…\Manifests\*.item`), itch — each just produces `Game`s.
- **Box art** via SteamGridDB (free API) instead of exe icons.
- **VirtualizingWrapPanel** (NuGet) if your library grows into the thousands
  (the built-in `WrapPanel` renders all items).
- Right-click menu (rename / remove / set-launch-exe override), categories, last-played.
