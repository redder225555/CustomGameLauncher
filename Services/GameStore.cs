using System.IO;
using System.Text.Json;
using CustomGameLauncher.Models;

namespace CustomGameLauncher.Services;

/// Loads/saves the game list as JSON in %LOCALAPPDATA%\CustomGameLauncher\games.json.
public static class GameStore
{
    private static readonly string Dir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "CustomGameLauncher");
    private static readonly string File_ = Path.Combine(Dir, "games.json");

    private static readonly JsonSerializerOptions Opts = new() { WriteIndented = true };

    public static List<Game> Load()
    {
        try
        {
            if (!File.Exists(File_)) return new();
            var json = File.ReadAllText(File_);
            return JsonSerializer.Deserialize<List<Game>>(json) ?? new();
        }
        catch
        {
            return new();
        }
    }

    public static void Save(IEnumerable<Game> games)
    {
        try
        {
            Directory.CreateDirectory(Dir);
            File.WriteAllText(File_, JsonSerializer.Serialize(games, Opts));
        }
        catch { /* best-effort */ }
    }
}
