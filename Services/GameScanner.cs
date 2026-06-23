using System.IO;
using CustomGameLauncher.Models;

namespace CustomGameLauncher.Services;

/// Scans a folder for games. Instead of one tile per .exe, it groups every exe
/// under each top-level game folder and picks ONE primary launch exe per game
/// (preferring a launcher, then a folder-name match, then the shallowest/biggest
/// binary), skipping anti-cheat / updater / web-helper / redistributable junk.
public static class GameScanner
{
    // Substrings that mark an exe as NOT the game you want to launch. Tune freely.
    private static readonly string[] Junk =
    {
        // installers / uninstallers / redistributables
        "unins", "uninstall", "setup", "installer", "vcredist", "vc_redist", "vcruntime",
        "dxsetup", "dxwebsetup", "directx", "dotnet", "ndp", "oalinst", "redist", "prereq",
        "ue4prereqsetup", "ue prereq",
        // anti-cheat
        "beservice", "battleye", "easyanticheat", "eac_", "anticheat",
        // updaters / patchers helpers
        "autoup", "autoupdate", "updater", "crashpad", "crashhandler", "crashreport",
        "unitycrashhandler", "werfault", "errorreport",
        // embedded web / engine helper processes
        "awesomium", "cefsharp", "browsersubprocess", "nwjs", "chromedriver",
        "notification_helper", "subprocess", "helper", "webhelper",
        // misc tooling
        "pak utility", "support tool", "config tool", "benchmark", "dedicated server",
    };

    public static List<Game> ScanGames(string root)
    {
        root = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar);
        var opts = new EnumerationOptions
        {
            RecurseSubdirectories = true,
            IgnoreInaccessible = true,
            AttributesToSkip = FileAttributes.System | FileAttributes.Hidden
        };

        // group: game folder -> all its non-junk exes
        var byGame = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase);
        try
        {
            foreach (var exe in Directory.EnumerateFiles(root, "*.exe", opts))
            {
                if (IsJunk(exe)) continue;
                var folder = GameFolderOf(exe, root);
                if (!byGame.TryGetValue(folder, out var list)) byGame[folder] = list = new();
                list.Add(exe);
            }
        }
        catch { /* ignore unreadable trees */ }

        var games = new List<Game>();
        foreach (var (folder, exes) in byGame)
        {
            var primary = PickPrimary(folder, exes);
            if (primary == null) continue;
            games.Add(new Game
            {
                Name = PrettyName(Path.GetFileName(folder)),
                ExePath = primary,
                FolderPath = folder,
                AllExes = exes.OrderBy(e => e, StringComparer.OrdinalIgnoreCase).ToList()
            });
        }
        games.Sort((a, b) => string.Compare(a.Name, b.Name, StringComparison.OrdinalIgnoreCase));
        return games;
    }

    /// The top-level game folder an exe belongs to (first path segment under root;
    /// the root itself if the exe sits directly in it).
    private static string GameFolderOf(string exe, string root)
    {
        var rel = Path.GetRelativePath(root, exe);
        int sep = rel.IndexOf(Path.DirectorySeparatorChar);
        return sep < 0 ? root : Path.Combine(root, rel[..sep]);
    }

    /// Best-guess launch exe for a game folder.
    private static string? PickPrimary(string folder, List<string> exes)
    {
        if (exes.Count == 0) return null;
        var folderKey = Norm(Path.GetFileName(folder));
        string? best = null;
        int bestScore = int.MinValue;
        foreach (var e in exes)
        {
            var name = Path.GetFileNameWithoutExtension(e);
            int score = 0;
            if (name.ToLowerInvariant().Contains("launch")) score += 100; // you want the launcher
            if (Norm(name) == folderKey) score += 80;                     // exe named like the game
            int depth = Path.GetRelativePath(folder, e).Count(c => c == Path.DirectorySeparatorChar);
            score -= depth * 15;                                          // prefer shallow (root) exes
            try { score += (int)Math.Min(40, new FileInfo(e).Length / (50L * 1024 * 1024)); } catch { }
            if (score > bestScore) { bestScore = score; best = e; }
        }
        return best;
    }

    private static bool IsJunk(string path)
    {
        var name = Path.GetFileNameWithoutExtension(path).ToLowerInvariant();
        foreach (var j in Junk)
            if (name.Contains(j)) return true;
        return false;
    }

    private static string Norm(string s) =>
        new(s.ToLowerInvariant().Where(char.IsLetterOrDigit).ToArray());

    /// A readable title: "the_witcher-3" -> "The Witcher 3".
    public static string PrettyName(string raw)
    {
        raw = raw.Replace('_', ' ').Replace('-', ' ').Trim();
        if (raw.Length == 0) return "(unnamed)";
        var parts = raw.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        for (int i = 0; i < parts.Length; i++)
            if (parts[i].Length > 1 && char.IsLower(parts[i][0]))
                parts[i] = char.ToUpperInvariant(parts[i][0]) + parts[i][1..];
        return string.Join(' ', parts);
    }
}
