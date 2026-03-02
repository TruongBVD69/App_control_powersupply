import tkinter as tk

from controllers.app_controller import AppController
from ui.main_view import build_main_view


def main() -> None:
    root = tk.Tk()
    controller = AppController(root)
    build_main_view(root, controller)
    root.mainloop()


if __name__ == "__main__":
    main()

