# RISC-V Simulator
Simulates the RISC-V base integer instruction set architecture as outlined in the official [RISC-V specification](https://riscv.org/wp-content/uploads/2017/05/riscv-spec-v2.2.pdf).

# Getting Started
## Prerequisites
  * riscv-gnu-toolchain

```
brew install riscv-gnu-toolchain
```

## Installation

1. Clone this repo

```
git clone https://github.com/dylanobata/rv32ISS
```

2. Clone and build ```riscv-tests```

```
git clone https://github.com/riscv/riscv-tests
cd riscv-tests
git submodule update --init --recursive
autoconf
./configure
make
make install
cd ..
```

3. Install Python packages

```
pip install bitstring
pip install pyelftools
```
