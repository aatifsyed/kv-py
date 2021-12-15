# kvsh, a command-line key-value store for the shell
- Cross-shell persistence
- Easy UI, with tab completion
## `kv` for quick operations
```shell
$ kv hello world
$ kv hello
world
```
## `kvv` for advanced functionality
```shell
$ kv hello world
$ kv foo food
$ kv bar bartender
$ kvv env # Print key=value iff key is a valid environment variable name
hello=world
foo=food
bar=bartender
$ kvv remove hello
$ kvv env
hello=world
$ kvv clear
```
## Installation
Recommended installation with [`pipx`](https://github.com/pypa/pipx):
```shell
pipx install kvsh
```
Tab completion with [`argcomplete`](https://github.com/kislyuk/argcomplete):
```shell
pipx install argcomplete
eval "$(register-python-argcomplete kv)"
eval "$(register-python-argcomplete kvv)"
```