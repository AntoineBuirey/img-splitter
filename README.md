# img-splitter

## Construire l'application

Le build produit un exécutable unique avec les fichiers du thème et la
configuration par défaut intégrés. PyInstaller construit pour le système sur
lequel il est exécuté : il faut donc lancer le build séparément sur Windows et
Linux.

### Windows

Avec Python 3.12 et `uv` installés :

```powershell
.\build.ps1
```

L'exécutable final se trouve dans `dist\img-splitter.exe`.

### Linux

Avec Python 3.12, `uv` et les dépendances Tk installés :

```bash
chmod +x build.sh
./build.sh
```

L'exécutable final se trouve dans `dist/img-splitter`. Il se lance sans
terminal avec le fichier de configuration utilisateur suivant :
`~/.config/ImgSplitter/config.yml`.

Sur Debian/Ubuntu, Tk peut être installé avec :

```bash
sudo apt install python3-tk
```

Les réglages modifiés par l'utilisateur sont enregistrés dans
`%APPDATA%\ImgSplitter\config.yml` sous Windows et
`~/.config/ImgSplitter/config.yml` sous Linux, afin de rester persistants et
accessibles en écriture.

## Releases GitHub

Lorsqu'une release GitHub est publiée, le workflow
`.github/workflows/release.yml` compile automatiquement deux exécutables sur
des runners natifs :

- `img-splitter-windows-x86_64.exe`
- `img-splitter-linux-x86_64`

Les deux fichiers sont ajoutés automatiquement aux assets de la release.