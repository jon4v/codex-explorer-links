# Codex Explorer Links

Open File Explorer with a particular file selected. Run this Python CLI on Windows or in WSL, then click the link it prints in Codex or your terminal. This is an independent community project.

## Install

With Python 3.9 or later and [pipx](https://pipx.pypa.io/stable/installation/), run this command in PowerShell or WSL:

```console
pipx install https://github.com/jon4v/codex-explorer-links/releases/download/v1.0.1/codex_explorer_links-1.0.1-py3-none-any.whl
```

If your terminal cannot find the command after installation, run `pipx ensurepath` and open a new terminal. To uninstall, run `pipx uninstall codex-explorer-links`.

## Reveal a file

From the folder containing your file, run:

```console
codex-explorer-links "model.3mf"
```

Click the URL next to the filename. A direct click from a terminal can open File Explorer immediately. If the browser shows a confirmation page, click **Show in File Explorer**.

To create links for two files and keep them available for two hours, run:

```console
codex-explorer-links --hours 2 "model.3mf" "preview.html"
```

Keep the command running while you use its links. The default lifetime is 24 hours. You can set it to any whole number of hours from 1 to 168, or press Ctrl+C to stop it early. If you stop the command, restart your computer, or move the file, run the command again for a fresh link.

## Use links in a Codex response

Pass all the finished files to the CLI in one invocation. Use the printed URL for a link labeled **Show in File Explorer** and include the ordinary file path for later access. Tell the reader how long the links will last. Each person who wants this feature runs the CLI on their own computer.

## How it works

The CLI listens on the IPv4 loopback address and generates a random token for each file. It keeps the token-to-path mapping in memory. File contents stay on disk. Anyone who has a valid link and access to the same computer can use it to select that file.

Link previews show a confirmation button. A direct browser navigation can request selection immediately. The browser may leave a confirmation tab open. When running under WSL, the Windows browser must be able to reach the WSL loopback service.

## Run from source

Download the source archive from [GitHub Releases](https://github.com/jon4v/codex-explorer-links/releases) and extract it. The CLI uses only the Python standard library.

| Action | Windows (PowerShell) | WSL |
| --- | --- | --- |
| Create a link | `py -3 explorer_links.py "model.3mf"` | `python3 explorer_links.py "model.3mf"` |
| Run the tests | `py -3 -m unittest -v` | `python3 -m unittest -v` |

The tests use temporary files and a simulated File Explorer. To test desktop integration, open a link and check the selected filename in File Explorer.

## License

[MIT](LICENSE).
