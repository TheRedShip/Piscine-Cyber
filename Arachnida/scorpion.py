import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS
import piexif
from fractions import Fraction
import ast

class ImageMetadataApp:
	def __init__(self, master):
		self.master = master
		self.master.title("Image Metadata Editor")
		self.master.geometry("1000x700")
		self.master.configure(bg="#2C3E50") 

		self.image_path = None
		self.metadata = {}
		self.image_preview = None

		self.style = ttk.Style()
		self.style.theme_use("clam")
		self.style.configure("TButton", padding=6, relief="flat", background="#3498DB")
		self.style.configure("TEntry", padding=6, relief="flat")
		self.style.configure("TFrame", background="#2C3E50")

		self.create_widgets()

	def create_widgets(self):
		main_frame = ttk.Frame(self.master, padding="10")
		main_frame.pack(fill=tk.BOTH, expand=True)

		left_frame = ttk.Frame(main_frame)
		left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

		right_frame = ttk.Frame(main_frame)
		right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

		self.choose_button = ttk.Button(left_frame, text="Choose Image", command=self.choose_image)
		self.choose_button.pack(pady=10)

		self.canvas = tk.Canvas(left_frame, width=400, height=400, bg="#34495E")
		self.canvas.pack(pady=10)

		self.metadata_listbox = tk.Listbox(right_frame, width=60, height=20, bg="#34495E", fg="white")
		self.metadata_listbox.pack(pady=10)

		edit_frame = ttk.Frame(right_frame)
		edit_frame.pack(pady=10)

		self.key_entry = ttk.Entry(edit_frame, width=25)
		self.key_entry.grid(row=0, column=0, padx=5)

		self.value_entry = ttk.Entry(edit_frame, width=25)
		self.value_entry.grid(row=0, column=1, padx=5)

		self.add_button = ttk.Button(edit_frame, text="Add/Modify", command=self.add_modify_metadata)
		self.add_button.grid(row=0, column=2, padx=5)

		self.delete_button = ttk.Button(edit_frame, text="Delete", command=self.delete_metadata)
		self.delete_button.grid(row=0, column=3, padx=5)

		self.save_button = ttk.Button(right_frame, text="Save Image", command=self.save_image)
		self.save_button.pack(pady=10)

	def choose_image(self):
		self.image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")])
		if self.image_path:
			self.load_metadata()
			self.display_image()

	def load_metadata(self):
		self.metadata_listbox.delete(0, tk.END)
		self.metadata = {}
		
		try:
			with Image.open(self.image_path) as img:
				exif_data = img._getexif()
				if exif_data:
					for tag_id, value in exif_data.items():
						tag = TAGS.get(tag_id, tag_id)
						self.metadata[tag] = str(value)
						self.metadata_listbox.insert(tk.END, f"{tag}: {value}")
		except Exception as e:
			messagebox.showerror("Error", f"Failed to load metadata: {str(e)}")

	def display_image(self):
		try:
			with Image.open(self.image_path) as img:
				img.thumbnail((400, 400))
				photo = ImageTk.PhotoImage(img)
				self.canvas.config(width=photo.width(), height=photo.height())
				self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
				self.canvas.image = photo
		except Exception as e:
			messagebox.showerror("Error", f"Failed to display image: {str(e)}")

	def add_modify_metadata(self):
		key = self.key_entry.get()
		value = self.value_entry.get()
		if key and value:
			self.metadata[key] = value
			self.update_listbox()
		else:
			messagebox.showwarning("Warning", "Both key and value must be provided.")

	def delete_metadata(self):
		selected = self.metadata_listbox.curselection()
		if selected:
			key = self.metadata_listbox.get(selected[0]).split(":")[0]
			del self.metadata[key]
			self.update_listbox()
		else:
			messagebox.showwarning("Warning", "Please select a metadata item to delete.")

	def update_listbox(self):
		self.metadata_listbox.delete(0, tk.END)
		for key, value in self.metadata.items():
			self.metadata_listbox.insert(tk.END, f"{key}: {value}")

	def save_image(self):
		if not self.image_path:
			messagebox.showerror("Error", "No image loaded.")
			return

		save_path = filedialog.asksaveasfilename(defaultextension=".jpg",
												 filetypes=[("JPEG files", "*.jpg")])
		if not save_path:
			return

		try:
			with Image.open(self.image_path) as img:
				exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

				for key, value in self.metadata.items():
					try:
						tag = next(tag for tag, name in TAGS.items() if name == key)
						ifd = self.get_ifd_for_tag(tag)
						if ifd is not None:
							value = self.convert_to_exif_value(tag, value)
							if (tag in [33437, 37122, 37378, 37380, 37381, 37382, 37386, 41486, 41487]):
								continue
							exif_dict[ifd][tag] = value

					except StopIteration:
						pass

				exif_bytes = piexif.dump(exif_dict)
				img.save(save_path, "jpeg", exif=exif_bytes)

			messagebox.showinfo("Success", "Image saved successfully with updated metadata.")
		except IOError:
			messagebox.showerror("Error", "Failed to save the image. Please check file permissions and try again.")
		except piexif.InvalidImageDataError:
			messagebox.showerror("Error", "Invalid image data. The metadata could not be written.")
		except ValueError as e:
			messagebox.showerror("Error", f"Value error: {str(e)}")
		except Exception as e:
			messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

	def get_ifd_for_tag(self, tag):
		if tag in piexif.ImageIFD.__dict__.values():
			return "0th"
		elif tag in piexif.ExifIFD.__dict__.values():
			return "Exif"
		elif tag in piexif.GPSIFD.__dict__.values():
			return "GPS"
		return None

	def convert_to_exif_value(self, tag, value):
		if tag in (piexif.ImageIFD.XResolution, piexif.ImageIFD.YResolution):
			try:
				float_value = float(value)
				return (int(float_value * 1000), 1000)
			except ValueError:
				return (0, 1)
		elif tag in (piexif.ExifIFD.ExposureTime, piexif.ExifIFD.ShutterSpeedValue):
			try:
				frac = Fraction(value).limit_denominator(1000000)
				return (frac.numerator, frac.denominator)
			except ValueError:
				return (0, 1)
		elif isinstance(value, str):
			if (value.startswith("b'")):
				value = ast.literal_eval(value)
			else:
				value = value.encode("utf-8")
			return value
		elif isinstance(value, bytes):
			return value
		elif isinstance(value, (int, float)):
			return int(value)
		else:
			return str(value).encode('utf-8')


if __name__ == "__main__":
	root = tk.Tk()
	app = ImageMetadataApp(root)
	root.mainloop()