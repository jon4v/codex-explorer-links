"""Select a file in Windows Explorer and bring the matching window forward."""
import os
from pathlib import Path
import shutil
import subprocess


# The target path travels on stdin, never as PowerShell code. PIDLs avoid
# Explorer's command-line parsing of filenames containing commas or spaces.
_SELECT = r"""
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
$target = [Console]::In.ReadToEnd()
Add-Type -Namespace ExplorerLinks -Name Native -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("shell32.dll", CharSet=System.Runtime.InteropServices.CharSet.Unicode)]
public static extern int SHParseDisplayName(string name, System.IntPtr bind, out System.IntPtr item, uint attrs, out uint result);
[System.Runtime.InteropServices.DllImport("shell32.dll")]
public static extern int SHOpenFolderAndSelectItems(System.IntPtr item, uint count, System.IntPtr children, uint flags);
[System.Runtime.InteropServices.DllImport("user32.dll")]
public static extern bool IsIconic(System.IntPtr window);
[System.Runtime.InteropServices.DllImport("user32.dll")]
public static extern bool ShowWindowAsync(System.IntPtr window, int command);
[System.Runtime.InteropServices.DllImport("user32.dll")]
public static extern bool SetForegroundWindow(System.IntPtr window);
[System.Runtime.InteropServices.DllImport("user32.dll")]
public static extern System.IntPtr GetForegroundWindow();
'@
$shell = New-Object -ComObject Shell.Application
$folder = [IO.Path]::GetDirectoryName($target)
$windows = @($shell.Windows() | Where-Object { $_.Document.Folder.Self.Path -eq $folder })
$existing = $windows | Where-Object { [long]$_.HWND -eq [ExplorerLinks.Native]::GetForegroundWindow().ToInt64() } | Select-Object -First 1
if (-not $existing) { $existing = $windows | Select-Object -First 1 }
if ($existing) {
    $entry = $existing.Document.Folder.ParseName([IO.Path]::GetFileName($target))
    if (-not $entry) { throw 'File not found in Explorer.' }
    $existing.Document.SelectItem($entry, 29)
} else {
    $item = [IntPtr]::Zero
    $attrs = [uint32]0
    try {
        [Runtime.InteropServices.Marshal]::ThrowExceptionForHR(
            [ExplorerLinks.Native]::SHParseDisplayName($target, [IntPtr]::Zero, [ref]$item, 0, [ref]$attrs))
        [Runtime.InteropServices.Marshal]::ThrowExceptionForHR(
            [ExplorerLinks.Native]::SHOpenFolderAndSelectItems($item, 0, [IntPtr]::Zero, 0))
    } finally {
        if ($item -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::FreeCoTaskMem($item) }
    }
}
for ($try = 0; $try -lt 30; $try++) {
    foreach ($window in @($shell.Windows())) {
        try {
            if ($existing -and $window.HWND -ne $existing.HWND) { continue }
            if ($window.Document.Folder.Self.Path -ne $folder) { continue }
            if ($target -notin @($window.Document.SelectedItems() | ForEach-Object { $_.Path })) { continue }
            $handle = [IntPtr]([long]$window.HWND)
            if ([ExplorerLinks.Native]::IsIconic($handle)) {
                [void][ExplorerLinks.Native]::ShowWindowAsync($handle, 9)
                Start-Sleep -Milliseconds 100
            }
            if ([ExplorerLinks.Native]::GetForegroundWindow() -ne $handle) {
                [void][ExplorerLinks.Native]::SetForegroundWindow($handle)
            }
            $stable = 0
            for ($wait = 0; $wait -lt 24; $wait++) {
                if (-not [ExplorerLinks.Native]::IsIconic($handle) -and
                    [ExplorerLinks.Native]::GetForegroundWindow() -eq $handle) {
                    $stable++
                    if ($stable -ge 3) { exit 0 }
                } else { $stable = 0 }
                if ($wait -eq 5 -and $stable -eq 0) {
                    # A background WSL caller can get a denied foreground request.
                    # Explorer handles its own restore. Change only the selected
                    # window and always post the paired restore request.
                    try {
                        [void][ExplorerLinks.Native]::ShowWindowAsync($handle, 6)
                        for ($poll = 0; $poll -lt 8; $poll++) {
                            if ([ExplorerLinks.Native]::IsIconic($handle)) { break }
                            Start-Sleep -Milliseconds 25
                        }
                    } finally {
                        [void][ExplorerLinks.Native]::ShowWindowAsync($handle, 9)
                    }
                }
                Start-Sleep -Milliseconds 60
            }
            throw 'Windows did not grant foreground focus.'
        } catch [Runtime.InteropServices.COMException] { continue }
    }
    Start-Sleep -Milliseconds 125
}
[Console]::Error.WriteLine('Explorer did not confirm a foreground window with the file selected.')
exit 1
"""


def powershell():
    if os.name == "nt":
        root = Path(os.environ["SystemRoot"])
    else:
        if not shutil.which("wslpath"):
            raise OSError("Windows or WSL with Windows interoperability is required.")
        root = Path(subprocess.check_output(["wslpath", "-u", r"C:\Windows"], text=True).strip())
    exe = root / "System32/WindowsPowerShell/v1.0/powershell.exe"
    if not exe.is_file():
        raise OSError("Windows PowerShell not found.")
    return str(exe)


def reveal(path):
    target = str(path) if os.name == "nt" else subprocess.check_output(
        ["wslpath", "-w", str(path)], text=True).rstrip("\n")
    try:
        subprocess.run([powershell(), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", _SELECT],
                       input=target.encode("utf-8"), check=True, timeout=20)
    except (OSError, subprocess.SubprocessError) as exc:
        raise OSError("Could not confirm selection and foreground focus in File Explorer.") from exc
