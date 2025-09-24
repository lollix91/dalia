# Dalia
a containerized launcher with a GUI for multi-agent-systems written in [DALI](https://github.com/AAAI-DISIM-UnivAQ/DALI).

### Pre-Requisites:

1. install  [sicstus](https://sicstus.sics.se/)
2. clone    [DALI](https://github.com/AAAI-DISIM-UnivAQ/DALI):
    - check the compatibility table [DALI-DALIA Compatibility](docs/compatibility.md)
    - e.g. 
    ```sh
    git clone --branch 2024.10 --depth 1 https://github.com/AAAI-DISIM-UnivAQ/DALI
    ```
3. install [docker](https://docs.docker.com/engine/install/)

### Installation 

1. clone [DALIA](https://github.com/alyshmahell/dalia)
    - check the compatibility table [DALI-DALIA Compatibility](compatibility.md)
    - e.g. 
    ```sh
    git clone --branch 2025.09 --depth 1 https://github.com/alyshmahell/dalia
    ```
2. navigate into the cloned repo:
```sh
cd dalia
```

### Usage
```sh
./run --sicstus <path_to_sicstus_directory> --dali <path_to_dali_directory> --src <path_to_mas_directory> 
```

- `path_to_mas_directory` is the path to the multi agent system you've written using [DALI](https://github.com/AAAI-DISIM-UnivAQ/DALI), you can use the `example` directory found in this repository in `path_to_mas_directory` when getting started.