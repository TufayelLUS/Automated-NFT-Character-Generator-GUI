import os
import customtkinter as ctk
from customtkinter import CTkImage
from tkinter import filedialog, Listbox, END, messagebox
from PIL import Image
import random
import io
from itertools import permutations

# pip instal customtkinter pillow


class DragDropApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        self.title("Character Generator")
        self.geometry("500x600")

        self.folder_path = ""
        self.folder_list = []
        self.drag_data = {"index": None}

        self.preview_label = ctk.CTkLabel(self, text="Preview Image")
        self.preview_label.pack(pady=5)
        self.preview_canvas = ctk.CTkLabel(
            self, text="Select Layers Folder for a Random Preview")
        self.preview_canvas.pack(pady=5)
        self.preview_canvas.bind(
            "<Button-1>", lambda event: self.update_preview())

        self.select_folder_btn = ctk.CTkButton(
            self, text="Select Layers Folder", command=self.select_folder)
        self.select_folder_btn.pack(pady=10)

        self.layer_label = ctk.CTkLabel(
            self, text="Order of Layers(top to bottom order):")
        self.layer_label.pack()

        self.listbox = Listbox(self, selectmode="single",
                               bg="#2E2E2E", fg="white", font=("Arial", 14))
        self.listbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.listbox.bind("<ButtonPress-1>", self.on_drag_start)
        self.listbox.bind("<B1-Motion>", self.on_drag_motion)
        self.listbox.bind("<ButtonRelease-1>", self.on_drag_drop)

        self.num_images_label = ctk.CTkLabel(self, text="Number of Images:")
        self.num_images_label.pack()

        self.num_images_entry = ctk.CTkEntry(self)
        self.num_images_entry.pack()

        self.generate_btn = ctk.CTkButton(
            self, text="Generate", command=self.generate_images)
        self.generate_btn.pack(pady=10)

    def update_preview(self):
        if not self.folder_list:
            print("No folders selected for preview.")
            return

        try:
            sample_image = self.create_character(
                self.folder_list, preview=True)

            if not sample_image:
                print("Preview image not found.")
                return

            # Convert the PIL Image to a byte stream
            img_byte_arr = io.BytesIO()
            sample_image.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)  # Rewind to the start of the byte array

            # Convert to CTkImage using the byte stream
            ctk_img = CTkImage(light_image=Image.open(
                img_byte_arr), size=(100, 100))

            self.preview_canvas.configure(image=ctk_img)
            # Store reference to prevent garbage collection
            self.preview_canvas.image = ctk_img
        except Exception as e:
            print(f"Preview Error: {e}")

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path = folder_selected
            self.load_folders()
            self.preview_canvas.configure(text="")
            self.update_preview()
            self.preview_label.configure(text="Preview Image (click image to randomly change)")

    def load_folders(self):
        self.folder_list = sorted([f for f in os.listdir(
            self.folder_path) if os.path.isdir(os.path.join(self.folder_path, f))])
        self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, END)
        for folder in self.folder_list:
            self.listbox.insert(END, folder)

    def on_drag_start(self, event):
        widget = event.widget
        index = widget.nearest(event.y)
        self.drag_data["index"] = index

    def on_drag_motion(self, event):
        pass  # Motion event does not need handling

    def on_drag_drop(self, event):
        widget = event.widget
        new_index = widget.nearest(event.y)
        old_index = self.drag_data["index"]

        if old_index is not None and old_index != new_index:
            item = self.folder_list.pop(old_index)
            self.folder_list.insert(new_index, item)
            self.update_listbox()
            self.update_preview()

        self.drag_data["index"] = None

    def generate_images(self):
        num_images = self.num_images_entry.get()
        if not self.folder_list:
            messagebox.showerror("Error", "No folders selected.")
            return
        print(
            f"Generating {num_images} images from folders: {self.folder_list}")
        self.create_character(self.folder_list, num_images)

    def get_random_image(self, folder):
        """Selects a random image from the given folder and its subdirectories."""
        images = []
        for root, _, files in os.walk(folder):
            images.extend(os.path.join(root, f)
                          for f in files if f.lower().endswith('.png'))
        if not images:
            raise ValueError(f"No PNG images found in {folder}")
        return os.path.join(folder, random.choice(images))

    def get_sequential_images(self, folder):
        """Generates all possible ordered combinations of images serially."""
        images = []
        for root, _, files in os.walk(folder):
            images.extend(os.path.join(root, f) for f in files if f.lower().endswith('.png'))
        
        if not images:
            raise ValueError(f"No PNG images found in {folder}")
        
        return list(permutations(images, len(images)))


    def create_character(self, layer_folders, num_images=1, preview=False):
        if preview:
            num_images = 1  # Only generate one image for preview
        else:
            if not str(num_images).isdigit():
                messagebox.showerror(
                    "Error", "Number of images to generate is not provided correctly!")
                return

        for count in range(int(num_images)):
            layer_images = []

            for layer in layer_folders[::-1]:
                try:
                    image_path = self.get_random_image(
                        os.path.join(self.folder_path, layer))
                    body = Image.open(image_path).convert("RGBA")
                    layer_images.append(body)
                except Exception as e:
                    print(f"Error loading layer '{layer}': {e}")
                    return None if preview else None

            if not layer_images:
                print("No layers found for preview.")
                return None if preview else None

            width, height = layer_images[0].size
            for i in range(1, len(layer_images)):
                layer_images[i] = layer_images[i].resize(
                    (width, height), Image.LANCZOS)

            final_image = layer_images[0]
            for image in layer_images[1:]:
                final_image = Image.alpha_composite(final_image, image)

            # For preview, return the image object instead of saving it
            if preview:
                return final_image  # Return the final image object directly
            else:
                output_path = os.path.join(
                    self.folder_path, f"output_{count}.png")
                final_image.save(output_path, format="PNG")
        if not preview:
            messagebox.showinfo(
                "Success", f"{num_images} images generated successfully!")


if __name__ == "__main__":
    app = DragDropApp()
    app.mainloop()
