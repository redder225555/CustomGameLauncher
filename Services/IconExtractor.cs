using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace CustomGameLauncher.Services;

/// Extracts the largest embedded icon (up to 256px) from an .exe via Win32,
/// converts it to a WPF ImageSource, and disk-caches it as PNG so we never
/// re-extract. Returns a *frozen* image so it's safe to build on a background
/// thread and assign on the UI thread. Returns null when there's no icon
/// (the UI shows a letter-tile fallback instead of a white box).
public static class IconExtractor
{
    private static readonly string CacheDir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "CustomGameLauncher", "iconcache");

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int PrivateExtractIcons(
        string lpszFile, int nIconIndex, int cxIcon, int cyIcon,
        IntPtr[] phicon, int[] piconid, int nIcons, int flags);

    [DllImport("user32.dll")]
    private static extern bool DestroyIcon(IntPtr hIcon);

    public static ImageSource? GetIcon(string exePath)
    {
        try
        {
            var cacheFile = Path.Combine(CacheDir, Hash(exePath) + ".png");
            if (File.Exists(cacheFile))
                return LoadPng(cacheFile);

            var src = ExtractNative(exePath);
            if (src == null) return null;

            Directory.CreateDirectory(CacheDir);
            SavePng(src, cacheFile);
            return src;
        }
        catch
        {
            return null; // any failure -> letter-tile fallback, never a crash
        }
    }

    private static BitmapSource? ExtractNative(string exePath)
    {
        if (!File.Exists(exePath)) return null;
        var hicons = new IntPtr[1];
        var ids = new int[1];
        // Ask for the 256px variant; Windows returns the best available <= that.
        int n = PrivateExtractIcons(exePath, 0, 256, 256, hicons, ids, 1, 0);
        if (n <= 0 || hicons[0] == IntPtr.Zero) return null;
        try
        {
            var src = Imaging.CreateBitmapSourceFromHIcon(
                hicons[0], Int32Rect.Empty, BitmapSizeOptions.FromEmptyOptions());
            src.Freeze();
            return src;
        }
        finally
        {
            DestroyIcon(hicons[0]);
        }
    }

    private static void SavePng(BitmapSource src, string file)
    {
        var enc = new PngBitmapEncoder();
        enc.Frames.Add(BitmapFrame.Create(src));
        using var fs = File.Create(file);
        enc.Save(fs);
    }

    private static BitmapImage LoadPng(string file)
    {
        var bi = new BitmapImage();
        bi.BeginInit();
        bi.CacheOption = BitmapCacheOption.OnLoad; // don't lock the file
        bi.UriSource = new Uri(file);
        bi.EndInit();
        bi.Freeze();
        return bi;
    }

    private static string Hash(string s) =>
        Convert.ToHexString(SHA1.HashData(Encoding.UTF8.GetBytes(s.ToLowerInvariant())));
}
