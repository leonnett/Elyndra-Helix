# Toolchain license review

The CI workflows download or install tools for verification and synthesis. They are not copied into this repository or linked into the Helix RTL.

| Tool | Pinned version | Upstream license | Use in this project |
|---|---|---|---|
| Cocotb | 2.0.0 | BSD-3-Clause | Python test framework used by the cloud test runner |
| YoWASP Yosys | 0.69.0.0.post1233 | ISC | Python-distributed WebAssembly Yosys executable used in cloud synthesis |
| Verilator | v5.036 | LGPL-3.0-only OR Artistic-2.0 | Cloud-only lint and Cocotb simulator; built from upstream source |

The project license applies to this repository's source. These tools remain separately licensed external dependencies. Their licenses do not change the Apache-2.0 license on Elyndra Helix source. Before changing a tool version or distributing any tool binary, review the upstream package license and notices again.

Primary license records: [Cocotb source](https://github.com/cocotb/cocotb), [YoWASP Yosys package](https://pypi.org/project/yowasp-yosys/0.69.0.0.post1233/), [Verilator source](https://github.com/verilator/verilator).
