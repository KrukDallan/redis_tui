### What is this?

You can think of this program as a "redis-cli on steroids". I use redis a lot and I prefer interacting with it from the terminal. The standard redis-cli however is quite clunky and tedious to use, so I decided to make this simple tui to make the redis-terminal experience a little more nice and easy. 

### Installation

Currently the easiest way to install it is through uv.

After cloning the repo enter the folder you just cloned and type this command:

`uv tool install --editable .`

Now you can use the command `tredis` from your terminal to open the tui.

### How to use it

You can move around in the table with the arrow keys, and while on a "value" cell you can press "Enter" to edit it. Also, by pressing "A" you can add a new key-value pair, while by pressing "X" you can delete the current row your cursor is on.