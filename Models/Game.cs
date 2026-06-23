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
    public string ExePath { get; set; } = "";

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
