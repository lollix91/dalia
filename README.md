# Dalia
a containerized launcher with a GUI for multi-agent-systems written in [DALI](https://github.com/AAAI-DISIM-UnivAQ/DALI).

### Pre-Requisites:

1. Install  [sicstus](https://sicstus.sics.se/)
2. Clone    [DALI](https://github.com/AAAI-DISIM-UnivAQ/DALI):
    - check the compatibility table [DALI-DALIA Compatibility](docs/compatibility.md)
    - e.g. 
    ```sh
    git clone --branch 2024.10 --depth 1 https://github.com/AAAI-DISIM-UnivAQ/DALI
    ```
3. Install [docker](https://docs.docker.com/engine/install/)

### Installation 
1. Open a Unix-Style shell (e.g. GIT BASH)
2. Clone [DALIA](https://github.com/lollix91/dalia)
    - check the compatibility table [DALI-DALIA Compatibility](https://github.com/alyshmahell/dalia/compatibility.md)
    - e.g. 
    ```sh
    git clone --depth 1 https://github.com/lollix91/dalia
    or
    git clone --branch 2025.09 --depth 1 https://github.com/lollix91/dalia
    ```
3. Navigate into the cloned repo:
```sh
cd dalia
```
4. Insert your Sicstus-Prolog for Linux license information in the "install_sicstus.exp" file

### Usage
```sh
./run --dali <PATH-TO-DALI-DIRECTORY> --src <PATH-TO-MAS-DIRECTORY> 
```

- `PATH-TO-MAS-DIRECTORY` is the path to the multi agent system you've written using [DALI](https://github.com/AAAI-DISIM-UnivAQ/DALI), you can use the `example` directory found in this repository in `PATH-TO-MAS-DIRECTORY` when getting started.