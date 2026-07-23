### What is this?

You can think of this program as a "redis-cli on steroids". I use redis a lot and I prefer interacting with it from the terminal. The standard redis-cli however is quite clunky and tedious to use, so I decided to make this simple tui to make the redis-terminal experience a little more nice and easy. 

### Installation (not quite)

After cloning the repo add this line in your .bashrc or .zshrc file:

`alias tredis="uv run --directory path/to/cloned/folder main.py"`

Of course you can change the command from "tredis" to something else of your liking.

After that just `source` your .bashrc or .zshrc and that's it, enjoy your redis tui!

### How to use it

You can move around in the table with the arrow keys, and while on a "value" cell you can press "Enter" to edit it. Also, by pressing "A" you can add a new key-value pair, while by pressing "X" you can delete the current row your cursor is on.