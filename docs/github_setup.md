# Publish to GitHub

1. Create an empty **public** repository on GitHub, e.g. `network-bufferbloat` (do not initialize it with a GitHub README; a local README already exists).
2. Open a terminal at the unpacked project folder.
3. Replace `YOUR-USERNAME` below with the actual GitHub username:

```bash
git init
git add .
git commit -m "feat: add reproducible bufferbloat simulations"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/network-bufferbloat.git
git push -u origin main
```
