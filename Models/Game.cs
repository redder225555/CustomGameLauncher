using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Text.Json.Serialization;
using System.Windows.Media;

namespace CustomGameLauncher.Models;

/// A single launchable game/exe. Only Name + ExePath are persisted; the Icon is
/// resolved at runtime (and disk-cached) so the JSON stays tiny.
public class Game : INotifyPropertyChanged
{
    public string Name { get; set; } = "";

    private string _exePath = "";
    public string ExePath { get => _exePath; set { _exePath = value; OnPropertyChanged(); } }

    /// The game's top-level folder (for "open folder" + dedupe + the exe picker).
    public string FolderPath { get; set; } = "";

    /// Every non-junk exe found in this game's folder — lets you re-pick the
    /// launch target without rescanning.
    public List<string> AllExes { get; set; } = new();

    [JsonIgnore]
    public string Initial =>
        string.IsNullOrWhiteSpace(Name) ? "?" : Name.TrimStart()[..1].ToUpperInvariant();

    private ImageSource? _icon;
    [JsonIgnore]
    public ImageSource? Icon
    {
        get => _icon;
        set { _icon = value; OnPropertyChanged(); }
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    private void OnPropertyChanged([CallerMemberName] string? n = null) =>
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(n));
}
