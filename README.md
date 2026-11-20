# Codex Explorer Links

Open File Explorer with a particular file selected. Run this Python CLI on Windows or in WSL, then click the link it prints in Codex or your terminal. This is an independent community project.

## Install

With Python 3.9 or later and [pipx](https://pipx.pypa.io/stable/installation/), run this command in PowerShell or WSL:

```console
pipx install https://github.com/jon4v/codex-explorer-links/releases/download/v1.1.1/codex_explorer_links-1.1.1-py3-none-any.whl
```

If your terminal cannot find the command after installation, run `pipx ensurepath` and open a new terminal. To uninstall, run `pipx uninstall codex-explorer-links`.

## Direct clicks in Codex on WSL

Use the direct opener to reveal a file without a browser tab or a running server. From a WSL shell with a working independent `xdg-open` for ordinary web links, start Codex with:

```sh
BROWSER=codex-explorer-open codex
```

For an existing thread, use `BROWSER=codex-explorer-open codex resume` when reopening it. In the same WSL user account, generate a link:

```sh
codex-explorer-links --direct "model.3mf"
```

Use the generated URL for **Show in File Explorer** in a Codex response. Use a plain left click inside the Codex transcript. The opener selects the file, restores a minimized Explorer window and checks that the matching window is in the foreground. Direct links are local to the account that created them. Their random tokens expire after 24 hours by default; `--hours` changes the lifetime. Registered paths and expiration times are stored in the user's local state directory.

The opener passes ordinary web URLs to `xdg-open`. In Windows Terminal, **Ctrl+click** can send a link straight to the Windows browser, bypassing the WSL opener. New direct links use the numeric loopback address and browser-blocked port 0. The selection token is in the URL fragment, which stays out of HTTP requests. If a browser gets the click, it may display a blocked-port error. For keyboard-only access, pass the quoted URL to `codex-explorer-open` in WSL. Ordinary Markdown file links in existing Codex messages still use Codex's built-in file preview. Reissue a direct link for those files.

With the direct opener configured, the CLI also chooses direct links automatically. Use `--browser` to force browser mode.

## Browser-compatible links

From the folder containing your file, run:

```console
codex-explorer-links --browser "model.3mf"
```

Click the URL next to the filename. A direct click from a terminal can open File Explorer immediately. If the browser shows a confirmation page, click **Show in File Explorer**.

To create links for two files and keep them available for two hours, run:

```console
codex-explorer-links --browser --hours 2 "model.3mf" "preview.html"
```

In browser mode, keep the command running while you use its links. The default lifetime is 24 hours. You can set it to any whole number of hours from 1 to 168, or press Ctrl+C to stop it early. If you stop the command, restart your computer, or move the file, run the command again for a fresh link.

## Use links in a Codex response

For WSL sessions using the direct opener, pass all finished files to `codex-explorer-links --direct` in one invocation. Otherwise use browser-compatible links. Use the printed URL for a link labeled **Show in File Explorer** and include the ordinary file path for later access. Tell the reader how long the links will last. Each person who wants this feature runs the CLI on their own computer.

## How it works

In browser mode the CLI listens on the IPv4 loopback address and generates a random token for each file. It keeps the token-to-path mapping in memory. File contents stay on disk. Anyone who has a valid link and access to the same computer can use it to select that file.

Link previews show a confirmation button. A direct browser navigation can request selection immediately. Successful requests receive an empty HTTP 204 response. A browser launched outside the direct opener may still create or focus a tab. When running under WSL, the Windows browser must be able to reach the WSL loopback service.

## Run from source

Download the source archive from [GitHub Releases](https://github.com/jon4v/codex-explorer-links/releases) and extract it. The CLI uses only the Python standard library.

| Action | Windows (PowerShell) | WSL |
| --- | --- | --- |
| Create a link | `py -3 explorer_links.py "model.3mf"` | `python3 explorer_links.py "model.3mf"` |
| Run the tests | `py -3 -m unittest -v` | `python3 -m unittest -v` |

The default tests use temporary files and a simulated File Explorer. To run the interactive regression as well, set `EXPLORER_LINKS_TEST_DIR` to a writable directory on a Windows drive before running the tests. This check creates a unique folder, opens and minimizes its Explorer window, then reveals a second file and checks the selection, window count and foreground handle. It closes the test folder afterward.

## License

[MIT](LICENSE).
