using System;
using System.Diagnostics;
using System.Runtime.InteropServices;

public static class DirectInterface
{
    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool LockWorkStation();

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool ExitWindowsEx(uint uFlags, uint dwReason);

    private const uint EWX_LOGOFF = 0x00000000;
    private const uint EWX_SHUTDOWN = 0x00000001;
    private const uint EWX_REBOOT = 0x00000002;
    private const uint EWX_FORCE = 0x00000004;

    public static void Lock() => LockWorkStation();

    public static void LogOff() => ExitWindowsEx(EWX_LOGOFF, 0);

    public static void Shutdown(bool force = false) =>
        ExitWindowsEx(EWX_SHUTDOWN | (force ? EWX_FORCE : 0), 0);

    public static void Restart(bool force = false) =>
        ExitWindowsEx(EWX_REBOOT | (force ? EWX_FORCE : 0), 0);

    public static void OpenTaskManager()
    {
        Process.Start(new ProcessStartInfo
        {
            FileName = "taskmgr.exe",
            UseShellExecute = true
        });
    }

    public static void OpenSecurityOptions()
    {
        Process.Start(new ProcessStartInfo
        {
            FileName = "rundll32.exe",
            Arguments = "user32.dll,LockWorkStation",
            UseShellExecute = true
        });
    }
}

class Program
{
    static void Main(string[] args)
    {
        if (args.Length == 0)
        {
            Console.WriteLine("Usage: DirectInterface.exe <command> [options]");
            Console.WriteLine("Commands: lock, logoff, shutdown, restart, taskmgr, security");
            return;
        }

        string command = args[0].ToLowerInvariant();

        try
        {
            switch (command)
            {
                case "lock":
                    DirectInterface.Lock();
                    break;
                case "logoff":
                    DirectInterface.LogOff();
                    break;
                case "shutdown":
                    DirectInterface.Shutdown(force: args.Contains("/force"));
                    break;
                case "restart":
                    DirectInterface.Restart(force: args.Contains("/force"));
                    break;
                case "taskmgr":
                    DirectInterface.OpenTaskManager();
                    break;
                case "security":
                    DirectInterface.OpenSecurityOptions();
                    break;
                default:
                    Console.WriteLine($"Unknown command: {command}");
                    break;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error executing {command}: {ex.Message}");
        }
    }
}
