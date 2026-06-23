using System.Windows;
using CustomGameLauncher.ViewModels;

namespace CustomGameLauncher;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        DataContext = new MainViewModel();
    }
}
