# img-splitter

## Construire l'application Windows

Le build produit un exécutable unique sans fenêtre de terminal. Depuis la racine
du projet, avec Python 3.12 et `uv` installés :

```powershell
.\build.ps1
```

L'exécutable final se trouve dans `dist\img-splitter.exe`. Les fichiers du thème
et la configuration par défaut sont intégrés dans l'exécutable. Les réglages
modifiés par l'utilisateur sont enregistrés dans
`%APPDATA%\ImgSplitter\config.yml`, afin de rester persistants et accessibles
en écriture.