from textual.app import App, ComposeResult
from textual.widgets import DataTable, Header, Footer, Input, Label
from rich.text import Text
from redis_utils import RedisDataHelper
from textual.screen import ModalScreen
from textual.containers import Vertical

class EditValueScreen(ModalScreen[str]):
    """Modal dialog screen to edit a Redis value."""

    def __init__(self, key_name: str, current_value: str) -> None:
        super().__init__()
        self.key_name = key_name
        self.current_value = current_value

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Edit Value for key: [bold cyan]{self.key_name}[/bold cyan]")
            yield Input(value=self.current_value, id="value_input")
            yield Label("[dim]Press Enter to Save | ESC to Cancel[/dim]")

    def on_mount(self) -> None:
        # Auto-focus the input box when the modal pops up
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Triggered when Enter is pressed inside the Input field
        self.dismiss(event.value)

    def key_escape(self) -> None:
        # Cancel without saving if ESC is pressed
        self.dismiss(None)

class AddKeyScreen(ModalScreen[str]):
    """Modal dialog screen to add a Redis value."""

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Set a new key and value:")            
            yield Input(value="", id="new_key")
            yield Input(value="", id="new_value")
            yield Label("[dim]Press Enter to Save | ESC to Cancel[/dim]")

    def on_mount(self) -> None:
        # Auto-focus the input box when the modal pops up
        self.query_one("#new_key").focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "new_key":
            self.query_one("#new_value", Input).focus()
            return
        key_val = self.query_one("#new_key", Input).value
        val_val = self.query_one("#new_value", Input).value
        self.dismiss((key_val, val_val))

    def key_escape(self) -> None:
        self.dismiss(None)

class ConfirmDeleteScreen(ModalScreen[bool]):
    """Modal dialog screen to confirm key deletion."""

    def __init__(self, key_name: str) -> None:
        super().__init__()
        self.key_name = key_name

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Are you sure you want to delete '[bold red]{self.key_name}[/bold red]'?")
            yield Label("[dim]Press Enter / Y to Delete | ESC / N to Cancel[/dim]")

    def key_y(self) -> None:
        """Confirm deletion when 'y' is pressed."""
        self.dismiss(True)

    def key_enter(self) -> None:
        """Confirm deletion when Enter is pressed."""
        self.dismiss(True)

    def key_n(self) -> None:
        """Cancel deletion when 'n' is pressed."""
        self.dismiss(False)

    def key_escape(self) -> None:
        """Cancel deletion when ESC is pressed."""
        self.dismiss(False)

class RedisTermanApp(App):
    CSS_PATH = "redis.tcss"
    BINDINGS = [("q", "quit", "Quit"),
                ("a", "add_key", "Add new key"),
                ("x", "remove_key", "Remove focused key")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable()
        yield Footer()
    
    def on_unmount(self) -> None:
        if hasattr(self, "pubsub"):
            self.pubsub.close()

    def action_quit(self):
        self.exit()

    def action_remove_key(self) -> None:
        table = self.query_one(DataTable)

        if table.cursor_coordinate is None:
            self.notify("No key selected to remove!", severity="warning")
            return

        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        key_name = str(row_key.value)

        def handle_confirm_result(confirmed: bool | None) -> None:
            if confirmed:
                try:
                    self.rdh.client.delete(key_name)
                except Exception as e:
                    self.notify(f"Failed to delete key: {e}", severity="error")

        self.push_screen(
            ConfirmDeleteScreen(key_name),
            callback=handle_confirm_result
        )
    

    def action_add_key(self):
        def handle_edit_result(result: tuple[str,str] | None) -> None:
                if result is not None:
                    new_key, new_value = result
                    self.save_value_to_redis(new_key, new_value)

        self.push_screen(
                AddKeyScreen(),
                callback=handle_edit_result,
            )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.zebra_stripes = True
        table_width = table.size.width or self.console.width
        col_width = min(25, (table_width // 2) - 1)
        table.add_column(Text("Key", justify="left", style="bold orange1"), key="key", width=col_width)
        table.add_column(Text("Value", justify="left", style="bold bright_cyan"), key="value", width=col_width)

        self.rdh = RedisDataHelper()

        initial_data = self.rdh.get_all_keys_and_values()
        for key, val in initial_data.items():
            table.add_row(
                Text(str(key), justify="left",),
                Text(str(val), justify="left"),
                key=key,
            )

        try:
            self.rdh.client.config_set("notify-keyspace-events", "KEA")
        except Exception as e:
            self.notify(f"Could not enable config: {e}", severity="warning")

        self.run_worker(self.listen_to_redis_events, thread=True, exclusive=True)

    def on_resize(self, event) -> None:
        """Triggered automatically whenever the terminal window is resized."""
        table = self.query_one(DataTable)
        
        if not table.columns:
            return

        total_width = event.size.width - 8
        key_width = max(10, int(total_width * 0.3))
        value_width = max(15, int(total_width * 0.7))

        if "key" in table.columns:
            table.columns["key"].width = key_width
        if "value" in table.columns:
            table.columns["value"].width = value_width
        # Force the table to re-render layout
        table.refresh(layout=True)


    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Triggered when user presses ENTER on a cell."""

        if event.cell_key.column_key.value == "value":
            row_key = event.cell_key.row_key.value
            current_cell_content = str(event.value)

            # Show the modal screen asynchronously
            def handle_edit_result(new_value: str | None) -> None:
                if new_value is not None and new_value != current_cell_content:
                    self.save_value_to_redis(row_key, new_value)

            self.push_screen(
                EditValueScreen(row_key, current_cell_content),
                callback=handle_edit_result,
            )

    def save_value_to_redis(self, key: str, new_value: str) -> None:
        try:
            self.rdh.client.set(key, new_value)
        except Exception as e:
            self.notify(f"Failed to update Redis: {e}", severity="error")

    def listen_to_redis_events(self) -> None:
        """
        Runs in a background thread.
        Listens to Redis events continuously without blocking the UI.
        """
        # Create a Pub/Sub object subscribing to keyspace events for DB 0
        self.pubsub = self.rdh.client.pubsub()
        self.pubsub.psubscribe("__keyspace@0__:*")

        for message in self.pubsub.listen():
            if message["type"] == "pmessage":
                # Channel format: '__keyspace@0__:your_key_name'
                channel = message["channel"]
                event_type = message["data"]
                
                key = channel.split(":", 1)[1]

                # Post a thread-safe call back to the main UI thread
                self.call_from_thread(self.handle_key_change, key, event_type)

    def handle_key_change(self, key: str, event_type: str) -> None:
        """Runs safely on the main thread to update the DataTable."""
        table = self.query_one(DataTable)

        if event_type in ("del", "expired"):
            if key in table.rows:
                table.remove_row(key)

        elif event_type in ("set", "hset", "lpush", "rpush", "sadd"):
            new_type = self.rdh.client.type(key)
            
            if new_type == "string":
                val = self.rdh.client.get(key)
            elif new_type == "hash":
                val = self.rdh.client.hgetall(key)
            else:
                val = f"<{new_type}>"

            val_str = str(val)

            if key in table.rows:
                table.update_cell(row_key=key, column_key="value", value=Text(val_str, justify="left"))
            else:
                table.add_row(Text(key, justify="left"), Text(val_str, justify="left"), key=key)


if __name__ == "__main__":
    app = RedisTermanApp()
    app.run()