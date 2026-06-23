using System.IO;

namespace CustomGameLauncher.Services;

/// Scans a folder (recursively) for game .exe files, skipping the usual
/// non-game junk (uninstallers, redistributables, crash handlers, etc.).
public static class GameScanner
{
    // Substrings that mark an exe as NOT a game. Tune freely.
    private static readonly string[] Junk =
    {
        "unins", "uninstall", "setup", "vcredist", "vc_redist", "dxsetup",
        "dxwebsetup", "directx", "dotnet", "ndp", "crashpad", "crashhandler",
        "crashreport", "unitycrashhandler", "nvngx", "redist", "prereq",
        "easyanticheat", "battleye", "werfault", "notification_helper",
        "ue4prereqsetup", "ue prereq", "vcruntime", "oalinst", "cefsharp",
        "subprocess", "helper"
    };

    public static List<string> Scan(string folder)
    {
        var found = new List<string>();
        var opts = new EnumerationOptions
        {
            RecurseSubdirectories = true,
            IgnoreInaccessible = true,
            AttributesToSkip = FileAttributes.System | FileAttributes.Hidden
        };
        try
        {
            foreach (var exe in Directory.EnumerateFiles(folder, "*.exe", opts))
            {
                if (!IsJunk(exe)) found.Add(exe);
            }
        }
        catch { /* ignore unreadable trees */ }
        return found;
    }

    private static bool IsJunk(string path)
    {
        var name = Path.GetFileNameWithoutExtension(path).ToLowerInvariant();
        foreach (var j in Junk)
            if (name.Contains(j)) return true;
        return false;
    }

    /// A readable title from the exe filename: "the_witcher3.exe" -> "The Witcher3".
    public static string PrettyName(string exePath)
    {
        var raw = Path.GetFileNameWithoutExtension(exePath).Replace('_', ' ').Replace('-', ' ').Trim();
        if (raw.Length == 0) return Path.GetFileName(exePath);
        var parts = raw.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        for (int i = 0; i < parts.Length; i++)
            if (parts[i].Length > 1 && char.IsLower(parts[i][0]))
                parts[i] = char.ToUpperInvariant(parts[i][0]) + parts[i][1..];
        return string.Join(' ', parts);
    }
}
