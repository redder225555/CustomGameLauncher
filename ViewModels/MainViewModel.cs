using System.Collections.ObjectModel;
using System.Collections.Specialized;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.CompilerServices;
using System.Windows;
using System.Windows.Data;
using System.Windows.Input;
using CustomGameLauncher.Models;
using CustomGameLauncher.Services;
using Microsoft.Win32;

namespace CustomGameLauncher.ViewModels;

public class MainViewModel : INotifyPropertyChanged
{
    public ObservableCollection<Game> Games { get; } = new();
    public ICollectionView GamesView { get; }

    public ICommand AddFolderCommand { get; }
    public ICommand RefreshCommand { get; }
    public ICommand LaunchCommand { get; }
    public ICommand SetLaunchExeCommand { get; }
    public ICommand OpenFolderCommand { get; }
    public ICommand RemoveCommand { get; }
    public ICommand ClearCommand { get; }

    public MainViewModel()
    {
        GamesView = CollectionViewSource.GetDefaultView(Games);
        GamesView.Filter = FilterGame;
        ((ListCollectionView)GamesView).CustomSort = new GameComparer();

        Games.CollectionChanged += OnGamesChanged;

        AddFolderCommand = new RelayCommand(async _ => await AddFolderAsync());
        RefreshCommand = new RelayCommand(async _ => await RefreshAsync());
        LaunchCommand = new RelayCommand(Launch);
        SetLaunchExeCommand = new RelayCommand(SetLaunchExe);
        OpenFolderCommand = new RelayCommand(OpenFolder);
        RemoveCommand = new RelayCommand(Remove);
        ClearCommand = new RelayCommand(_ => ClearAll());

        // Initial load from disk + resolve icons.
        foreach (var g in GameStore.Load()) Games.Add(g);
        UpdateStatus();
        _ = LoadIconsAsync();
    }

    // ── search ────────────────────────────────────────────────────────────
    private string _search = "";
    public string Search
    {
        get => _search;
        set { _search = value; OnPropertyChanged(); GamesView.Refresh(); }
    }

    private bool FilterGame(object o) =>
        o is Game g &&
        (string.IsNullOrWhiteSpace(_search) ||
         g.Name.Contains(_search, StringComparison.OrdinalIgnoreCase));

    // ── status + empty hint ───────────────────────────────────────────────
    private string _statusText = "";
    public string StatusText
    {
        get => _statusText;
        set { _statusText = value; OnPropertyChanged(); }
    }

    public Visibility EmptyHintVisibility =>
        Games.Count == 0 ? Visibility.Visible : Visibility.Collapsed;

    private void OnGamesChanged(object? s, NotifyCollectionChangedEventArgs e) =>
        OnPropertyChanged(nameof(EmptyHintVisibility));

    private void UpdateStatus() => StatusText = $"{Games.Count} games";

    // ── commands ──────────────────────────────────────────────────────────
    private async Task AddFolderAsync()
    {
        var dlg = new OpenFolderDialog { Title = "Pick a folder of games (subfolders are scanned)" };
        if (dlg.ShowDialog() != true) return;
        var folder = dlg.FolderName;

        StatusText = "Scanning…";
        var found = await Task.Run(() => GameScanner.ScanGames(folder));

        // dedupe by game folder (fall back to exe path for older entries)
        var existing = new HashSet<string>(
            Games.Select(g => string.IsNullOrEmpty(g.FolderPath) ? g.ExePath : g.FolderPath),
            StringComparer.OrdinalIgnoreCase);

        int added = 0;
        foreach (var g in found)
        {
            if (existing.Add(g.FolderPath))
            {
                Games.Add(g);
                added++;
            }
        }
        GamesView.Refresh();
        GameStore.Save(Games);
        StatusText = $"{Games.Count} games ({added} new)";
        await LoadIconsAsync();
    }

    private void SetLaunchExe(object? p)
    {
        if (p is not Game g) return;
        var dlg = new OpenFileDialog
        {
            Title = $"Pick the launch .exe for {g.Name}",
            Filter = "Executables (*.exe)|*.exe",
            InitialDirectory = Directory.Exists(g.FolderPath)
                ? g.FolderPath
                : (Path.GetDirectoryName(g.ExePath) ?? "")
        };
        if (dlg.ShowDialog() != true) return;
        g.ExePath = dlg.FileName;
        g.Icon = null;
        GameStore.Save(Games);
        _ = LoadIconsAsync();
    }

    private void OpenFolder(object? p)
    {
        if (p is not Game g) return;
        var dir = Directory.Exists(g.FolderPath) ? g.FolderPath : Path.GetDirectoryName(g.ExePath);
        if (!string.IsNullOrEmpty(dir) && Directory.Exists(dir))
            Process.Start(new ProcessStartInfo { FileName = dir, UseShellExecute = true });
    }

    private void Remove(object? p)
    {
        if (p is Game g) { Games.Remove(g); GameStore.Save(Games); UpdateStatus(); }
    }

    private void ClearAll()
    {
        Games.Clear();
        GameStore.Save(Games);
        UpdateStatus();
    }

    private async Task RefreshAsync()
    {
        Games.Clear();
        foreach (var g in GameStore.Load()) Games.Add(g);
        GamesView.Refresh();
        UpdateStatus();
        await LoadIconsAsync();
    }

    private void Launch(object? p)
    {
        if (p is not Game g) return;
        if (!File.Exists(g.ExePath))
        {
            MessageBox.Show($"File not found:\n{g.ExePath}", "Launch failed");
            return;
        }
        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = g.ExePath,
                WorkingDirectory = Path.GetDirectoryName(g.ExePath) ?? "",
                UseShellExecute = true
            });
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Couldn't launch {g.Name}:\n{ex.Message}", "Launch failed");
        }
    }

    // ── icons (parallel, disk-cached, off the UI thread) ──────────────────
    private async Task LoadIconsAsync()
    {
        var todo = Games.Where(g => g.Icon == null).ToList();
        if (todo.Count == 0) return;
        await Task.Run(() =>
        {
            Parallel.ForEach(todo, new ParallelOptions { MaxDegreeOfParallelism = 4 }, g =>
            {
                var icon = IconExtractor.GetIcon(g.ExePath);
                if (icon != null)
                    Application.Current.Dispatcher.Invoke(() => g.Icon = icon);
            });
        });
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    private void OnPropertyChanged([CallerMemberName] string? n = null) =>
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(n));
}

/// Case-insensitive A–Z sort by name for the grid.
internal sealed class GameComparer : System.Collections.IComparer
{
    public int Compare(object? x, object? y) =>
        string.Compare((x as Game)?.Name, (y as Game)?.Name, StringComparison.OrdinalIgnoreCase);
}
