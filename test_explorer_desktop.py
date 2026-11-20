"""Opt-in integration check. Restores and closes only a unique test folder."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from explorer_desktop import powershell, reveal


def observe(path, action):
    target = str(path) if os.name == "nt" else subprocess.check_output(
        ["wslpath", "-w", str(path)], text=True).rstrip("\n")
    script = r"""
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
$target = [Console]::In.ReadToEnd()
$folder = [IO.Path]::GetDirectoryName($target)
$windows = @((New-Object -ComObject Shell.Application).Windows() |
    Where-Object { $_.Document.Folder.Self.Path -eq $folder })
"""
    if action == "close":
        script += "foreach ($w in $windows) { $w.Quit() }"
    else:
        script += r"""
if ($windows.Count -ne 1) { throw "Expected a single test window; found $($windows.Count)." }
$w = $windows[0]
Add-Type -Namespace Test -Name Window -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool IsIconic(System.IntPtr h);
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern System.IntPtr GetForegroundWindow();
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool ShowWindowAsync(System.IntPtr h, int command);
'@
$handle = [IntPtr]([long]$w.HWND)
"""
        if action == "minimize":
            script += """
[void][Test.Window]::ShowWindowAsync($handle, 6)
Start-Sleep -Milliseconds 250
if (-not [Test.Window]::IsIconic($handle)) { throw 'Fixture was not minimized.' }
"""
        else:
            script += """
$selection = @($w.Document.SelectedItems() | ForEach-Object { $_.Path })
if ($selection.Count -ne 1 -or $selection[0] -ne $target) { throw 'Wrong selection.' }
if ([Test.Window]::IsIconic($handle)) { throw 'Window is minimized.' }
if ([Test.Window]::GetForegroundWindow() -ne $handle) { throw 'Window is in the background.' }
"""
    subprocess.run([powershell(), "-NoProfile", "-NonInteractive", "-Command", script],
                   input=target.encode(), check=True, timeout=15)


@unittest.skipUnless(os.environ.get("EXPLORER_LINKS_TEST_DIR"), "requires an interactive Windows desktop")
class DesktopTest(unittest.TestCase):
    def test_open_then_restore_the_same_window(self):
        with tempfile.TemporaryDirectory(dir=os.environ["EXPLORER_LINKS_TEST_DIR"]) as tmp:
            first, second = (Path(tmp, name) for name in ("sample α, 1.txt", "sample 2.html"))
            first.touch()
            second.touch()
            try:
                reveal(first)
                observe(first, "verify")
                observe(first, "minimize")
                reveal(second)
                observe(second, "verify")
            finally:
                observe(first, "close")
